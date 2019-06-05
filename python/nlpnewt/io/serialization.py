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
import io
import logging
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from typing import Callable, Union, Dict, Any

from nlpnewt.events import Event, Document, LabelIndexType, Events
from nlpnewt.label_indices import LabelIndex
from nlpnewt.labels import GenericLabel
from nlpnewt.processing import EventProcessor, processor, processor_parser, run_processor

_serializer_fs = {}
_serializers = {}
logger = logging.getLogger(__name__)


def event_to_dict(event: Event) -> Dict:
    """Turns the event into a python dictionary.

    Parameters
    ----------
    event: Event
        The event object.

    Returns
    -------
    dict
        A dictionary object suitable for serialization.

    """
    d = {
        'event_id': event.event_id,
        'metadata': {},
        'documents': {}
    }
    for k, v in event.metadata.items():
        d['metadata'][k] = v
    for doc in event.values():
        d['documents'][doc.document_name] = document_to_dict(doc)
    return d


def document_to_dict(document: Document) -> Dict:
    """Turns the document into a python dictionary.

    Parameters
    ----------
    document: Document
        The document object.

    Returns
    -------
    dict
        A dictionary object suitable for serialization.

    """
    d = {
        'text': document.text,
        'label_indices': {}
    }

    for index_info in document.get_label_indices_info():
        if index_info.type == LabelIndexType.OTHER or index_info.type == LabelIndexType.UNKNOWN:
            logger.warning(
                'Index %s of type %s will not be included in serialization.'.format(
                    index_info.index_name, index_info.type.name
                )
            )
            continue
        d['label_indices'][index_info.index_name] = label_index_to_dict(
            document.get_label_index(index_info.index_name)
        )
    return d


def label_index_to_dict(label_index: LabelIndex[GenericLabel]) -> Dict:
    """Turns the label index into a dictionary representation.

    Parameters
    ----------
    label_index: LabelIndex[GenericLabel]
        The label index itself.

    Returns
    -------
    dict
        A dictionary representing the label index.
    """
    d = {
        'json_labels': [label.fields for label in label_index],
        'distinct': label_index.distinct
    }
    return d


def dict_to_event(events: Events, d: Dict) -> Event:
    """Turns a serialized dictionary into an Event.

    Parameters
    ----------
    events: Events
        An events service to create the event on.
    d: dict
        The dictionary representation of the event.

    Returns
    -------
    Event
        The deserialized event object.

    """
    event = events.create_event(event_id=d['event_id'])
    for k, v in d['metadata'].items():
        event.metadata[k] = v
    for k, v in d['documents'].items():
        dict_to_document(event, k, v)
    return event


def dict_to_document(event: Event, document_name: str, d: Dict) -> Document:
    """Turns a serialized dictionary into a Document.

    Parameters
    ----------
    event: Event
        The parent event of the document.
    document_name: str
        The name identifier of the document on the event.
    d: dict
        The dictionary representation of the document.

    Returns
    -------
    Document
        The deserialized Document object.

    """
    document = event.add_document(document_name=document_name, text=d['text'])
    for k, v in d['label_indices'].items():
        dict_to_label_index(document, index_name=k, d=v)
    return document


def dict_to_label_index(document: Document, index_name: str, d: Dict):
    """Deserializes a label index from its dictionary form.

    Parameters
    ----------
    document: Document
        The document object to place the label index on.
    index_name: str
        The index name on the document.
    d: dict
        The dictionary representation of the label index.

    """
    with document.get_labeler(label_index_name=index_name, distinct=d['distinct']) as labeler:
        for l in d['json_labels']:
            labeler(**l)


class Serializer(ABC):
    """Base class for a serializer of NLP-NEWT events.
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """The default filename extension.

        Returns
        -------
        str
            Filename extension, including period. Ex: ``'.json'``.
        """
        ...

    @abstractmethod
    def event_to_file(self, event: Event, f: Union[Path, str, io.IOBase]):
        """Writes the event to a file.

        Parameters
        ----------
        event: Event
            The event object to serialize.
        f: Path or str or file-like object
            A file or a path to a file to write the event to.
        """
        ...

    @abstractmethod
    def file_to_event(self, f: Union[Path, str, io.IOBase], events: Events) -> Event:
        """Loads an event from a serialized file.

        Parameters
        ----------
        f: Path or str path or file-like object
            The file to load from.
        events: Events
            The events service to load the event into.

        Returns
        -------
        Event
            The loaded event object.

        """
        ...


def serializer(name: str) -> Callable[[Callable[[], Serializer]], Callable[[], Serializer]]:
    """Decorator which marks an implementation of :obj:`Serializer` that can be used for a specific
    kind of serialization.

    Parameters
    ----------
    name: str
        The name to register the serializer under, Ex. ``'json'``.

    Returns
    -------
    decorator
        Decorator of class or function which returns a serializer.

    """

    def decorator(func: Callable[[], Serializer]) -> Callable[[], Serializer]:
        _serializer_fs[name] = func
        return func

    return decorator


def get_serializer(name: str) -> Serializer:
    """Gets a callable which creates a serializer for the specific name.

    Parameters
    ----------
    name: str
        The name for the type of serialization, Ex. ``'json'``.

    Returns
    -------
    Callable[[], Serializer]
        Function that can be used to create a :obj:`Serializer`.

    """
    try:
        return _serializers[name]
    except KeyError:
        # Maybe lock here depending on how heavy serializer instantiation is?
        s = _serializer_fs[name]()
        _serializers[name] = s
        return s


@processor('nlpnewt-serializer')
class SerializationProcessor(EventProcessor):
    """NLP-Newt processor that serializes events to a specific directory.

    """

    def __init__(self, serializer: Serializer, output_dir: str):
        self.serializer = serializer
        self.output_dir = output_dir

    def process(self, event: Event, params: Dict[str, Any]):
        name = params.get('filename', event.event_id + self.serializer.extension)
        path = Path(self.output_dir, name)
        self.serializer.event_to_file(event, path)


def main(args=None):
    parser = ArgumentParser(parents=[processor_parser()])
    parser.add_argument('serializer', help="The name of the serializer to use.")
    parser.add_argument('--output-dir', '-o', default=".",
                        help="Directory to write serialized files to.")
    ns = parser.parse_args(args)
    serializer = get_serializer(ns.serializer)
    proc = SerializationProcessor(serializer, ns.output_dir)
    run_processor(proc, ns)


if __name__ == '__main__':
    main()
