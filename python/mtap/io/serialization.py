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

from mtap.events import Event, Document, LabelIndexType, EventsClient
from mtap.label_indices import LabelIndex, label_index
from mtap.labels import GenericLabel
from mtap.processing import EventProcessor, processor
from mtap.processing.descriptions import parameter

logger = logging.getLogger(__name__)


def event_to_dict(event: Event, *, include_label_text: bool = False) -> Dict:
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


def document_to_dict(document: Document, *, include_label_text: bool = False) -> Dict:
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

    for index_info in document.get_label_indices_info():
        if index_info.type == LabelIndexType.OTHER or index_info.type == LabelIndexType.UNKNOWN:
            logger.warning(
                'Index {} of type {} will not be included in serialization.'.format(
                    index_info.index_name, index_info.type.name
                )
            )
            continue
        d['label_indices'][index_info.index_name] = label_index_to_dict(
            document.get_label_index(index_info.index_name),
            include_label_text=include_label_text
        )
    return d


def label_index_to_dict(label_index: LabelIndex[GenericLabel],
                        *, include_label_text: bool = False) -> Dict:
    """A helper method that turns a label index into a python dictionary.

    Args:
        label_index (LabelIndex[GenericLabel]): The label index itself.

    Keyword Args:
        include_label_text (bool): Whether to include the text labels cover with the labels.

    Returns:
        dict: A dictionary representing the label index.
    """
    d = {
        'json_labels': [dict(label.fields, _text=label.text) if include_label_text else label.fields
                        for label in label_index],
        'distinct': label_index.distinct
    }
    return d


def dict_to_event(d: Dict, *, client: Optional[EventsClient] = None) -> Event:
    """Turns a serialized dictionary into an Event.

    Args:
        d (dict): The dictionary representation of the event.
        client (~typing.Optional[EventsClient]): An events service to create the event on.

    Returns:
        Event: The deserialized event object.
    """
    event = Event(event_id=d['event_id'], client=client)
    for k, v in d['metadata'].items():
        event.metadata[k] = v
    for k, v in d['documents'].items():
        dict_to_document(k, v, event=event)
    return event


def dict_to_document(document_name: str, d: Dict, *, event: Optional[Event] = None) -> Document:
    """Turns a serialized dictionary into a Document.

    Args:
        document_name (str): The name identifier of the document on the event.
        d (dict): The dictionary representation of the document.
        event (~typing.Optional[Event]): An event that the document should be added to.

    Returns:
        Document: The deserialized Document object.

    """
    document = Document(document_name=document_name, text=d['text'])
    if event is not None:
        event.add_document(document)
    for k, v in d['label_indices'].items():
        index = dict_to_label_index(d=v)
        document.add_labels(k, index, distinct=index.distinct)

    return document


def dict_to_label_index(d: Dict) -> LabelIndex:
    """Turns a serialized dictionary into a label index.

    Args:
        d (dict): The dictionary representation of the label index.

    Returns:
        LabelIndex: The deserialized label index.
    """
    return label_index([GenericLabel(**{k: v for k, v in x.items() if not k.startswith('_')})
                        for x in d['json_labels']], distinct=d['distinct'])


class Serializer(ABC):
    """Abstract base class for a serializer of MTAP events.
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """str: Filename extension, including period. Ex: ``'.json'``."""
        ...

    @abstractmethod
    def event_to_file(self, event: Event, f: Union[Path, str, io.IOBase],
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
                      client: Optional[EventsClient] = None) -> Event:
        """Loads an event from a serialized file.

        Args:
            f (~typing.Union[~pathlib.Path, str, ~io.IOBase]): The file to load from.
            client (~typing.Optional[EventsClient]): The events service to load the event into.

        Returns:
            Event: The loaded event object.
        """
        ...


@processor('mtap-serializer',
           description='Serializes events to a specific directory',
           parameters=[parameter('filename', data_type='str',
                                 description='Optional override for the filename to write the '
                                             'document to.')])
class SerializationProcessor(EventProcessor):
    """An MTAP :obj:`EventProcessor` that serializes events to a specific directory.

    Args:
        ser (Serializer): The serializer to use.
        output_dir (str): The output_directory.
    """

    def __init__(self, ser: Serializer, output_dir: str):
        self.serializer = ser
        self.output_dir = output_dir

    def process(self, event: Event, params: Dict[str, Any]):
        name = params.get('filename', event.event_id + self.serializer.extension)
        path = Path(self.output_dir, name)
        self.serializer.event_to_file(event, path)


class _JsonSerializer(Serializer):
    """Serializer implementation that performs serialization to JSON.
    """
    @property
    def extension(self) -> str:
        return '.json'

    def event_to_file(self, event: Event, f: Path, *, include_label_text: bool = False):
        import json
        d = event_to_dict(event, include_label_text=include_label_text)
        try:
            json.dump(d, f)
        except AttributeError:
            f = Path(f)
            f.parent.mkdir(parents=True, exist_ok=True)
            with f.open('w') as f:
                json.dump(d, f)

    def file_to_event(self, f: Union[Path, str, io.IOBase],
                      client: Optional[EventsClient] = None) -> Event:
        import json
        try:
            d = json.load(f)
        except AttributeError:
            if isinstance(f, str):
                f = Path(f)
            with f.open('r') as f:
                d = json.load(f)
        return dict_to_event(d, client=client)


JsonSerializer = _JsonSerializer()


def get_serializer(identifier):
    return {
        'json': JsonSerializer
    }[identifier]
