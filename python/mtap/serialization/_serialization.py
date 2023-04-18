#  Copyright 2023 Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Serialization, serializers, and helper methods for going to and from
flattened python dictionary representations of events.
"""
import io
import logging
import os
from abc import abstractmethod, ABCMeta
from os import PathLike
from typing import Union, Dict, Any, Optional, TextIO, Type, ClassVar, IO, \
    BinaryIO

from mtap._document import Document
from mtap._event import Event
from mtap._events_client import EventsClient
from mtap._label_adapters import GENERIC_ADAPTER
from mtap.descriptors import processor, parameter
from mtap.processing import EventProcessor, Processor

logger = logging.getLogger('mtap.serialization')


def event_to_dict(event: Event, *,
                  include_label_text: bool = False) -> Dict:
    """A helper method that turns an event into a python dictionary.

    Args:
        event: The event object.
        include_label_text: Whether to include the text labels cover with the
            labels.

    Returns:
        dict: A dictionary object suitable for serialization.

    """
    d = {
        'event_id': event.event_id,
        'metadata': {},
        'documents': {}
    }
    for k, v in event.metadata.items():
        d['metadata'][k] = v
    for doc in event.documents.values():
        d['documents'][doc.document_name] = document_to_dict(
            doc,
            include_label_text=include_label_text
        )
    return d


def document_to_dict(document: Document, *,
                     include_label_text: bool = False) -> Dict:
    """A helper method that turns a document into a python dictionary.

    Args:
        document: The document object.
        include_label_text: Whether to include the text labels cover with the
            labels.

    Returns:
        A dictionary object suitable for serialization.
    """
    d = {
        'text': document.text,
        'label_indices': {}
    }

    for index_name, index in document.labels.items():
        adapter = index.adapter
        if adapter is None:
            adapter = GENERIC_ADAPTER
        d['label_indices'][index_name] = adapter.pack(
            index,
            include_label_text=include_label_text
        )
    return d


def dict_to_event(d: Dict, *,
                  client: Optional[EventsClient] = None) -> Event:
    """Turns a serialized dictionary into an Event.

    Args:
        d: A json-like (only ``str`` keys) dictionary representation of the
            event.
        client: If specified, will upload the event to this events service.
            Otherwise, creates a local event.

    Returns:
        The deserialized event object.
    """
    event = Event(event_id=d['event_id'], client=client)
    for k, v in d['metadata'].items():
        event.metadata[k] = v
    for k, v in d['documents'].items():
        dict_to_document(k, v, event=event)
    return event


def dict_to_document(document_name: str,
                     d: Dict,
                     *, event: Optional[Event] = None) -> Document:
    """Turns a serialized dictionary into a Document.

    Args:
        document_name: The name identifier of the document.
        d: A json-like (only ``str`` keys) dictionary representation of the
            document.
        event: If specified, the function will add the document to this
            event. Otherwise, it will create a stand-alone document.

    Returns:
        The deserialized Document object.

    """
    document = Document(document_name=document_name, text=d['text'])
    if event is not None:
        event.add_document(document)
    for k, v in d['label_indices'].items():
        adapter = document.default_adapter(k)
        index = adapter.unpack(v, k, document=document)
        document.add_labels(k, index, distinct=index.distinct)

    return document


class SerializerRegistry(ABCMeta):
    REGISTRY: ClassVar[Dict[str, Type['Serializer']]] = {}

    def __init__(cls: Type['Serializer'], *args, **kwargs):
        super().__init__(*args, **kwargs)
        SerializerRegistry.REGISTRY[cls.name()] = cls

    @staticmethod
    def get(name: str) -> Type['Serializer']:
        return SerializerRegistry.REGISTRY[name]


class Serializer(metaclass=SerializerRegistry):
    """Abstract base class for a serializer of MTAP events.
    """

    @classmethod
    def name(cls) -> str:
        return cls.__name__.casefold()

    @classmethod
    def extension(cls) -> str:
        """str: Filename extension, including period. Ex: ``'.json'``."""
        ...

    @classmethod
    @abstractmethod
    def event_to_file(
            cls,
            event: Event,
            f: Union[str, bytes, PathLike, IO],
            *, include_label_text: bool = False
    ):
        """Writes the event to a file.

        Args:
            event: The event object to serialize.
            f: A file or a path to a file to write the event to.
            include_label_text: Whether, when serializing, to include the text
            that each label covers with the rest of the label.
        """
        ...

    @classmethod
    @abstractmethod
    def file_to_event(
            cls,
            f: Union[str, bytes, PathLike, IO],
            *, client: Optional[EventsClient] = None
    ) -> Event:
        """Loads an event from a serialized file.

        Args:
            f: The file to load from.
            client: The events service to load the event into.

        Returns:
            The loaded event object.
        """
        ...


@processor(
    'mtap-serializer',
    description='Serializes events to a specific directory',
    parameters=[
        parameter(
            'filename',
            data_type='str',
            description='Optional override for the filename '
                        'to write the document to.'
        )
    ]
)
class SerializationProcessor(EventProcessor):
    """An MTAP :obj:`EventProcessor` that serializes events to a specific
    directory.

    Attributes:
        serializer (~mtap.serialization.Serializer): The serializer to use.
        output_dir: The output directory.
        include_label_text: Whether to attach the covered text to labels.

    """
    serializer: Serializer
    output_dir: Union[str, bytes, PathLike]
    include_label_text: bool

    def __init__(
            self,
            serializer: Serializer,
            output_dir: Union[str, bytes, PathLike],
            include_label_text: bool = False
    ):
        self.serializer = serializer
        self.output_dir = os.path.abspath(output_dir)
        self.include_label_text = include_label_text
        os.makedirs(self.output_dir, exist_ok=True)

    def process(self, event: Event, params: Dict[str, Any]):
        name = params.get('filename',
                          event.event_id + self.serializer.extension())
        path = os.path.join(self.output_dir, name)
        self.serializer.event_to_file(
            event,
            path,
            include_label_text=self.include_label_text
        )


class JsonSerializer(Serializer):
    """Serializer implementation that performs serialization to JSON.
    """

    @classmethod
    def name(cls) -> str:
        return 'json'

    @classmethod
    def extension(cls) -> str:
        return '.json'

    @classmethod
    def event_to_file(cls,
                      event: Event,
                      f: Union[str, bytes, PathLike, IO], *,
                      include_label_text: bool = False):
        import json
        with Processor.started_stopwatch('transform'):
            d = event_to_dict(event, include_label_text=include_label_text)
        with Processor.started_stopwatch('io'):
            try:
                json.dump(d, f)
            except (AttributeError, TypeError):
                os.makedirs(os.path.dirname(f), exist_ok=True)
                with open(f, 'w') as f:
                    json.dump(d, f)

    @classmethod
    def file_to_event(cls,
                      f: Union[str, bytes, PathLike, IO],
                      client: Optional[EventsClient] = None) -> Event:
        import json
        with Processor.started_stopwatch('io'):
            try:
                d = json.load(f)
            except (AttributeError, TypeError):
                with open(f, 'r') as f:
                    d = json.load(f)
        with Processor.started_stopwatch('transform'):
            return dict_to_event(d, client=client)


class YamlSerializer(Serializer):
    """Serializer implementation that performs serialization to YAML.
    """

    @classmethod
    def name(cls) -> str:
        return 'yaml'

    @classmethod
    def extension(cls) -> str:
        return '.yml'

    @classmethod
    def event_to_file(cls, event: Event,
                      f: Union[str, bytes, PathLike, IO], *,
                      include_label_text: bool = False):
        import yaml
        try:
            from yaml import CDumper as Dumper
        except ImportError:
            from yaml import Dumper
        with Processor.started_stopwatch('transform'):
            d = event_to_dict(event, include_label_text=include_label_text)
        with Processor.started_stopwatch('io'):
            try:
                yaml.dump(d, f, Dumper=Dumper)
            except (AttributeError, TypeError):
                os.makedirs(os.path.dirname(f), exist_ok=True)
                with open(f, 'w') as f:
                    yaml.dump(d, f, Dumper=Dumper)

    @classmethod
    def file_to_event(cls,
                      f: Union[str, bytes, PathLike, TextIO],
                      *, client: Optional[EventsClient] = None) -> Event:
        import yaml
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        with Processor.started_stopwatch('io'):
            try:
                d = yaml.load(f, Loader=Loader)
            except (AttributeError, TypeError):
                with open(f) as f:
                    d = yaml.load(f, Loader=Loader)
        with Processor.started_stopwatch('transform'):
            return dict_to_event(d, client=client)


class PickleSerializer(Serializer):
    """Serializer implementation that performs serialization to .pickle.
    """

    @classmethod
    def name(cls) -> str:
        return 'pickle'

    @classmethod
    def extension(cls) -> str:
        return '.pickle'

    @classmethod
    def event_to_file(cls,
                      event: Event,
                      f: Union[str, bytes, PathLike, BinaryIO], *,
                      include_label_text: bool = False):
        import pickle
        with Processor.started_stopwatch('transform'):
            d = event_to_dict(event, include_label_text=include_label_text)
        with Processor.started_stopwatch('io'):
            try:
                pickle.dump(d, f)
            except (AttributeError, TypeError):
                os.makedirs(os.path.dirname(f), exist_ok=True)
                with open(f, 'wb') as f:
                    pickle.dump(d, f)

    @classmethod
    def file_to_event(
            cls,
            f: Union[str, bytes, PathLike, BinaryIO], *,
            client: Optional[EventsClient] = None
    ) -> Event:
        import pickle
        with Processor.started_stopwatch('io'):
            try:
                d = pickle.load(f)
            except (AttributeError, TypeError):
                with open(f, 'rb') as f:
                    d = pickle.load(f)
        with Processor.started_stopwatch('transform'):
            return dict_to_event(d, client=client)
