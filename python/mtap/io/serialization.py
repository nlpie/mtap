# Copyright 2019 Regents of the University of Minnesota.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Serialization, serializers, and helper methods for going to and from flattened python dictionary
representations of events.

Attributes:
    JsonSerializer (Serializer): For serializing to and from json.

"""
import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Dict, Any, Optional

import mtap
from mtap import data, processing
from mtap import descriptions as d

logger = logging.getLogger(__name__)

__all__ = [
    'event_to_dict',
    'document_to_dict',
    'dict_to_event',
    'dict_to_document',
    'Serializer',
    'SerializationProcessor',
    'JsonSerializer',
    'YamlSerializer',
    'PickleSerializer',
    'standard_serializers',
    'get_serializer'
]


def event_to_dict(event: mtap.Event, *, include_label_text: bool = False) -> Dict:
    """A helper method that turns an event into a python dictionary.

    Args:
        event (Event): The event object.

    Keyword Args:
        include_label_text (bool): Whether to include the text labels cover with the labels.

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
        d['documents'][doc.document_name] = document_to_dict(doc,
                                                             include_label_text=include_label_text)
    return d


def document_to_dict(document: mtap.Document, *, include_label_text: bool = False) -> Dict:
    """A helper method that turns a document into a python dictionary.

    Args:
        document (Document): The document object.

    Keyword Args:
        include_label_text (bool): Whether to include the text labels cover with the labels.

    Returns:
        dict: A dictionary object suitable for serialization.
    """
    d = {
        'text': document.text,
        'label_indices': {}
    }

    for index_name, index in document.labels.items():
        adapter = index.adapter
        if adapter is None:
            adapter = data.GENERIC_ADAPTER
        d['label_indices'][index_name] = adapter.pack(
            index,
            include_label_text=include_label_text
        )
    return d


def dict_to_event(d: Dict, *, client: Optional[mtap.EventsClient] = None) -> mtap.Event:
    """Turns a serialized dictionary into an Event.

    Args:
        d (dict): The dictionary representation of the event.
        client (~typing.Optional[EventsClient]): An events service to create the event on.

    Returns:
        Event: The deserialized event object.
    """
    event = mtap.Event(event_id=d['event_id'], client=client)
    for k, v in d['metadata'].items():
        event.metadata[k] = v
    for k, v in d['documents'].items():
        dict_to_document(k, v, event=event)
    return event


def dict_to_document(document_name: str,
                     d: Dict,
                     *, event: Optional[mtap.Event] = None) -> mtap.Document:
    """Turns a serialized dictionary into a Document.

    Args:
        document_name (str): The name identifier of the document on the event.
        d (dict): The dictionary representation of the document.
        event (~typing.Optional[Event]): An event that the document should be added to.

    Returns:
        Document: The deserialized Document object.

    """
    document = mtap.Document(document_name=document_name, text=d['text'])
    if event is not None:
        event.add_document(document)
    for k, v in d['label_indices'].items():
        adapter = document.get_default_adapter(k)
        index = adapter.unpack(v, k, document=document)
        document.add_labels(k, index, distinct=index.distinct)

    return document


class Serializer(ABC):
    """Abstract base class for a serializer of MTAP events.
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """str: Filename extension, including period. Ex: ``'.json'``."""
        ...

    @abstractmethod
    def event_to_file(self, event: mtap.Event, f: Union[Path, str, io.IOBase],
                      *, include_label_text: bool = False):
        """Writes the event to a file.

        Args:
            event (Event): The event object to serialize.
            f (~typing.Union[~pathlib.Path, str, ~io.IOBase]):
                A file or a path to a file to write the event to.
            include_label_text (bool):
                Whether, when serializing, to include the text that each label covers with the rest
                of the label.
        """
        ...

    @abstractmethod
    def file_to_event(self, f: Union[Path, str, io.IOBase], *,
                      client: Optional[mtap.EventsClient] = None) -> mtap.Event:
        """Loads an event from a serialized file.

        Args:
            f (~typing.Union[~pathlib.Path, str, ~io.IOBase]): The file to load from.
            client (~typing.Optional[EventsClient]): The events service to load the event into.

        Returns:
            Event: The loaded event object.
        """
        ...


@mtap.processor('mtap-serializer',
                description='Serializes events to a specific directory',
                parameters=[d.parameter('filename', data_type='str',
                                        description='Optional override for the filename to write the '
                                                    'document to.')])
class SerializationProcessor(mtap.EventProcessor):
    """An MTAP :obj:`EventProcessor` that serializes events to a specific directory.

    Args:
        ser (Serializer): The serializer to use.
        output_dir (str): The output_directory.
    """

    def __init__(self, ser: Serializer, output_dir: str, include_label_text: bool = False):
        self.serializer = ser
        self.output_dir = output_dir
        self.include_label_text = include_label_text
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def process(self, event: mtap.Event, params: Dict[str, Any]):
        name = params.get('filename', event.event_id + self.serializer.extension)
        path = Path(self.output_dir, name)
        self.serializer.event_to_file(event, path, include_label_text=self.include_label_text)


class _JsonSerializer(Serializer):
    """Serializer implementation that performs serialization to JSON.
    """

    @property
    def extension(self) -> str:
        return '.json'

    def event_to_file(self, event: mtap.Event, f: Path, *, include_label_text: bool = False):
        import json
        with processing.Processor.started_stopwatch('transform'):
            d = event_to_dict(event, include_label_text=include_label_text)
        with processing.Processor.started_stopwatch('io'):
            try:
                json.dump(d, f)
            except AttributeError:
                f = Path(f)
                f.parent.mkdir(parents=True, exist_ok=True)
                with f.open('w') as f:
                    json.dump(d, f)

    def file_to_event(self, f: Union[Path, str, io.IOBase],
                      client: Optional[mtap.EventsClient] = None) -> mtap.Event:
        import json
        with processing.Processor.started_stopwatch('io'):
            try:
                d = json.load(f)
            except AttributeError:
                if isinstance(f, str):
                    f = Path(f)
                with f.open('r') as f:
                    d = json.load(f)
        with processing.Processor.started_stopwatch('transform'):
            return dict_to_event(d, client=client)


class _YamlSerializer(Serializer):

    @property
    def extension(self) -> str:
        return '.yml'

    def event_to_file(self, event: mtap.Event, f: Union[Path, str, io.IOBase], *,
                      include_label_text: bool = False):
        import yaml
        try:
            from yaml import CDumper as Dumper
        except ImportError:
            from yaml import Dumper
        with processing.Processor.started_stopwatch('transform'):
            d = event_to_dict(event, include_label_text=include_label_text)
        with processing.Processor.started_stopwatch('io'):
            if isinstance(f, io.IOBase):
                yaml.dump(d, f, Dumper=Dumper)
            else:
                f = Path(f)
                with f.open('w') as f:
                    yaml.dump(d, f, Dumper=Dumper)

    def file_to_event(self, f: Union[Path, str, io.IOBase], *,
                      client: Optional[mtap.EventsClient] = None) -> mtap.Event:
        import yaml
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        with processing.Processor.started_stopwatch('io'):
            if isinstance(f, io.IOBase):
                d = yaml.load(f, Loader=Loader)
            else:
                with Path(f).open() as f:
                    d = yaml.load(f, Loader=Loader)
        with processing.Processor.started_stopwatch('transform'):
            return dict_to_event(d, client=client)


class _PickleSerializer(Serializer):

    @property
    def extension(self) -> str:
        return '.pickle'

    def event_to_file(self, event: mtap.Event, f: Union[Path, str, io.IOBase], *,
                      include_label_text: bool = False):
        import pickle
        with processing.Processor.started_stopwatch('transform'):
            d = event_to_dict(event, include_label_text=include_label_text)
        with processing.Processor.started_stopwatch('io'):
            try:
                pickle.dump(d, f)
            except TypeError:
                with Path(f).open('wb') as f:
                    pickle.dump(d, f)

    def file_to_event(self, f: Union[Path, str, io.IOBase], *,
                      client: Optional[mtap.EventsClient] = None) -> mtap.Event:
        import pickle
        with processing.Processor.started_stopwatch('io'):
            try:
                d = pickle.load(f)
            except TypeError:
                with Path(f).open('rb') as f:
                    d = pickle.load(f)
        with processing.Processor.started_stopwatch('transform'):
            return dict_to_event(d, client=client)


JsonSerializer = _JsonSerializer()
YamlSerializer = _YamlSerializer()
PickleSerializer = _PickleSerializer()

standard_serializers = {
    'json': JsonSerializer,
    'yml': YamlSerializer,
    'pickle': PickleSerializer
}


def get_serializer(identifier):
    return standard_serializers[identifier]
