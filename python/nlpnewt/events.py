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
"""Internal events client."""

import collections
import contextlib
import threading
import uuid
from abc import abstractmethod, ABC
from typing import Iterator, AnyStr, List, Dict, MutableMapping, Mapping, Generic, TypeVar, Callable

import grpc

from . import _discovery
from . import _utils
from . import constants
from ._config import Config
from .api.v1 import events_pb2_grpc, events_pb2
from .label_indices import label_index
from .labels import GenericLabel, Label

__all__ = [
    'Events',
    'Event',
    'Document',
    'Labeler',
    'proto_label_adapter',
    'ProtoLabelAdapter'
]

L = TypeVar('L', bound=Label)


class Events:
    """Creates an object that can be used for making requests to an events service.

    Parameters
    ----------
    address: str, optional
        The events service target e.g. 'localhost:9090' or omit/None to use service discovery.
    stub: EventsStub
        An existing events service client stub to use.

    Examples
    --------
    Use service discovery to create connection:

    >>> with nlpnewt.Events() as events:
    >>>     # use events

    Use address to create connection:

    >>> with nlpnewt.Events('localhost:9090') as events:
    >>>     # use events

    """

    def __init__(self, address=None, *, stub=None):
        self._client = _EventsClient(address, stub=stub)

    def open_event(self, event_id: str = None) -> 'Event':
        """Opens or creates an event on the events service and returns an Event object that can be
        used to access and manipulate data.

        Parameters
        ----------
        event_id : str, optional
            A globally-unique identifier for the event, or omit / none for a random UUID.

        Returns
        -------
        Event
            An Event object for interacting with the event.

        """
        event_id = event_id or uuid.uuid1()
        self._client.open_event(event_id, only_create_new=False)
        return Event(self._client, event_id)

    def create_event(self, event_id: str = None) -> 'Event':
        """Creates an event on the events service, failing if an event already exists with the
        specified ID, returns an :obj:`Event` object that can be used to access and manipulate data.

        Parameters
        ----------
        event_id : str, optional
            A globally-unique identifier for the event, or omit / none for a random UUID.

        Returns
        -------
        Event
            A newly initialized event.

        Raises
        ------
        ValueError
            If the event already exists on the server.

        """
        event_id = event_id or uuid.uuid1()
        self._client.open_event(event_id, only_create_new=True)
        return Event(self._client, event_id)

    def __enter__(self) -> 'Events':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._client.close()


class Event(Mapping[str, 'Document']):
    """The object created by :func:`~Events.open_event` or :func:`~Events.create_event` to interact
    with a specific event on the events service.

    The Event object functions as a map from string document names to :obj:`Document` objects that
    can be used to access document data from the events server.

    Examples
    --------
    >>> with events.open_event('id') as event:
    >>>     # use event

    """

    def __init__(self, client: '_EventsClient', event_id):
        self._client = client
        self._event_id = event_id
        self._documents = {}
        self._open = True
        self._lock = threading.RLock()

    @property
    def event_id(self) -> str:
        """Returns the globally unique identifier for this event.

        Returns
        -------
        str
            The event ID.
        """
        return self._event_id

    @property
    def metadata(self) -> MutableMapping[str, str]:
        """Returns an object that can be used to query and add metadata to the object.

        Returns
        -------
        typing.MutableMapping[str, str]
            An object containing the metadata

        """
        self.ensure_open()
        try:
            return self._metadata
        except AttributeError:
            self._metadata = _Metadata(self._client, self)

    @property
    def created_indices(self) -> Dict[AnyStr, List[AnyStr]]:
        """Returns a map of label indices that have been added to any document on this event.

        Returns
        -------
        dict[str, list[str]]
            A dictionary of string ``document_name`` to lists of string ``index_name``.

        """
        return {document_name: document.created_indices
                for document_name, document in self._documents.items()}

    def close(self):
        """Closes this event. Lets the event service know that we are done with the event,
        allowing to clean up the event if everyone is done with it.
        """
        if self._open is True:
            with self._lock:
                # using double locking here to ensure that the event does not
                if self._open:
                    self._client.close_event(self._event_id)
                    self._open = False

    def add_document(self, document_name, text):
        """Adds a document to the event keyed by the document_name and
        containing the specified text.

        Parameters
        ----------
        document_name : str
            The event-unique identifier for the document, example: 'plaintext'.
        text : str
            The content of the document. This is a required field, document text is final and
            immutable, as changing the text very likely would invalidate any labels on the document.

        Returns
        -------
        Document
            An object that is set up to connect to the events service to retrieve data and
            modify the document with the `document_name` on this event.
        """
        self.ensure_open()
        if text is None:
            raise ValueError("Argument text cannot be None. "
                             "None maps to an empty string in protobuf.")
        self._client.add_document(self._event_id, document_name, text)
        document = Document(self._client, self, document_name)
        self._documents[document_name] = document
        return document

    def __contains__(self, document_name: str) -> bool:
        if not isinstance(document_name, str):
            raise TypeError('Document name is not string')
        self.ensure_open()
        if document_name in self._documents:
            return True
        self._refresh_documents()
        return document_name in self._documents

    def __getitem__(self, document_name):
        """Retrieves an object for interacting with an existing document on this event.

        Parameters
        ----------
        document_name : str
            The document_name identifier.

        Returns
        -------
        Document
            An object that is set up to connect to the events service to retrieve data and
            modify the document with the `document_name` on this event.

        Examples
        --------
        >>> plaintext_document = event['plaintext']
        >>> plaintext_document.text
        'The quick brown fox jumped over the lazy dog.'

        """
        if not isinstance(document_name, str):
            raise TypeError('Document name is not string')
        self.ensure_open()
        try:
            return self._documents[document_name]
        except KeyError:
            pass
        self._refresh_documents()
        return self._documents[document_name]

    def __len__(self) -> int:
        self.ensure_open()
        self._refresh_documents()
        return len(self._documents)

    def __iter__(self) -> Iterator[str]:
        self.ensure_open()
        self._refresh_documents()
        return iter(self._documents)

    def __enter__(self) -> 'Event':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _refresh_documents(self):
        document_names = self._client.get_all_document_names(self._event_id)
        for name in document_names:
            if name not in self._documents:
                self._documents[name] = Document(self._client, self, name)

    def ensure_open(self):
        self._client.ensure_open()
        if not self._open:
            raise ValueError("Event has been closed.")

    def add_created_indices(self, created_indices):
        for k, v in created_indices.items():
            try:
                doc = self._documents[k]
                doc.add_created_indices(v)
            except KeyError:
                pass


class Document:
    """An object returned by :func:`~Event.__getitem__` or :func:`~Event.add_document`
    for accessing document data.

    Documents are keyed by their name, this is to allow pipelines to store different pieces of
    related text on a single processing event. An example would be storing the text of one language
    on one document, and the text of another language on another, or, for example, storing the
    plaintext.

    Both label indices, once added, and the document text are immutable. This is to enable
    parallelization and distribution of processing, and to prevent changes to upstream data that
    has already been used in the creation of downstream data.

    """

    def __init__(self, client: '_EventsClient', event: Event, document_name: str):
        self._client = client
        self._document_name = document_name
        self._event = event
        self._event_id = event.event_id

        self._text = None

        self._label_indices = {}
        self._labelers = []
        self._created_indices = []

    @property
    def event(self) -> Event:
        """Returns the parent event of this document.

        Returns
        -------
        Event
            The event object which contains this document.

        """
        return self._event

    @property
    def document_name(self) -> str:
        """The event-unique identifier.

        Returns
        -------
        str

        """
        self._event.ensure_open()
        return self._document_name

    @property
    def text(self):
        """Returns the document text, fetching if it is not cached locally.

        Returns
        -------
        str
            The text that the document was created

        """
        self._event.ensure_open()
        if self._text is None:
            self._text = self._client.get_document_text(self._event_id, self._document_name)
        return self._text

    @property
    def created_indices(self) -> List[str]:
        """Returns the newly created label indices on this document using a labeler.

        Returns
        -------
        list[str]
            A list of all of the label indices that have created on this document using a labeler.
        """
        return list(self._created_indices)

    def get_label_index(self, label_index_name: str, *, label_type_id: str = None):
        """Gets the document's label index with the specified key, fetching it from the
        service if it is not cached locally.

        Parameters
        ----------
        label_index_name : str
            The name of the label index to get.
        label_type_id : str, optional
            The identifier that a :obj:`ProtoLabelAdapter` was registered with
            :func:`proto_label_adapter`. It will be used to deserialize the labels in the index.
            If not set, the adapter for :obj:`GenericLabel` will be used.

        Returns
        -------
        LabelIndex
            LabelIndex object containing the labels.

        """
        self._event.ensure_open()
        if label_index_name in self._label_indices:
            return self._label_indices[label_index_name]

        if label_type_id is None:
            label_type_id = constants.GENERIC_LABEL_ID

        label_adapter = _label_adapters[label_type_id]

        label_index = self._client.get_labels(self._event_id, self._document_name, label_index_name,
                                              adapter=label_adapter)
        self._label_indices[label_index_name] = label_index
        return label_index

    @contextlib.contextmanager
    def get_labeler(self,
                    label_index_name: str,
                    *,
                    distinct: bool = None,
                    label_type_id: str = None) -> 'Labeler':
        """Creates a function that can be used to add labels to a label index.

        If the label id is not specified it will use :obj:`GenericLabel`, otherwise it will
        look for a custom :obj:`ProtoLabelAdapter` registered using :func:`proto_label_adapter`

        Parameters
        ----------
        label_index_name : str
            A document-unique identifier for the label index to be created.
        label_type_id: str
            Optional, the string identifier that an adapter has been registered under, or None if
            the default, generic labels are being used.
        distinct: bool
            Optional, whether to use GenericLabel or DistinctGenericLabel

        Returns
        -------
        typing.ContextManager
            A contextmanager for the labeler, which when used in conjunction with the 'with'
            keyword will automatically handle uploading any added labels to the server

        Examples
        --------
        >>> with document.get_labeler('sentences', distinct=True) as labeler:
        >>>     labeler(0, 25)
        >>>     sentence = labeler(26, 34)
        >>>     sentence.sentence_type = 'FRAGMENT'

        """
        self._event.ensure_open()
        if label_index_name in self._labelers:
            raise KeyError("Labeler already in use: " + label_index_name)
        if label_type_id is not None and distinct is not None:
            raise ValueError("Either distinct or or label_type needs to be set, but not both.")
        if label_type_id is None:
            label_type_id = (constants.DISTINCT_GENERIC_LABEL_ID
                             if distinct
                             else constants.GENERIC_LABEL_ID)

        labeler = Labeler(self._client, self, label_index_name, label_type_id)
        self._labelers.append(label_index_name)
        yield labeler
        # this isn't in a try-finally block because it is not cleanup, we do not want
        # the labeler to send labels after a processing failure.
        labeler.done()
        self._created_indices.append(label_index_name)

    def add_created_indices(self, created_indices):
        return self._created_indices.append(created_indices)


class Labeler(Generic[L]):
    """Object provided by :func:`~Document.get_labeler` which is responsible for adding labels to a
    label index on a document.

    See Also
    --------
    GenericLabel : The default Label type used if another registered label type is not specified.
    """

    def __init__(self, client, document, label_index_name, label_type_id):
        self._client = client
        self._document = document
        self._label_index_name = label_index_name
        self._label_adapter = _label_adapters[label_type_id]
        self.is_done = False
        self._current_labels = []

    def __call__(self, *args, **kwargs):
        """Calls the constructor for the label type adding it to the list of labels to be uploaded.

        Parameters
        ----------
        args
            Arguments raise passed to the label type's constructor.
        kwargs
            Keyword arguments passed to the label type's constructor.

        Returns
        -------
        Label
            The object that was created by the label type's constructor.

        Examples
        --------
        >>> labeler(0, 25, some_field='some_value', x=3)
        GenericLabel(start_index=0, end_index=25, some_field='some_value', x=3)
        """
        self._document.event.ensure_open()
        label = self._label_adapter.create_label(*args, **kwargs)
        self._current_labels.append(label)
        return label

    def done(self):
        self._document.event.ensure_open()
        if self.is_done:
            return
        self._client.add_labels(event_id=self._document.event.event_id,
                                document_name=self._document.document_name,
                                index_name=self._label_index_name,
                                labels=self._current_labels,
                                adapter=self._label_adapter)
        self.is_done = True


class ProtoLabelAdapter(ABC):
    """Responsible for serialization and deserialization of non-standard label types.

    See Also
    --------
    proto_label_adapter: The decorator used to create

    """

    @abstractmethod
    def create_label(self, *args, **kwargs):
        ...

    @abstractmethod
    def create_index_from_response(self, response):
        ...

    @abstractmethod
    def add_to_message(self, labels, request):
        ...


def proto_label_adapter(label_type_id: str):
    """Registers a :obj:`ProtoLabelAdapter` for a specific identifier.

    When that id is referenced in the document :func:`~Document.get_labeler`
    and  :func:`~Document.get_label_index`.

    Parameters
    ----------
    label_type_id: hashable
        This can be anything as long as it is hashable, good choices are strings or the label types
        themselves if they are concrete classes.

    Returns
    -------
    decorator
        Decorator object which invokes the callable to create the label adapter.

    Examples
    --------
    >>> @nlpnewt.proto_label_adapter("example.Sentence")
    >>> class SentenceAdapter(nlpnewt.ProtoLabelAdapter):
    >>>    # ... implementation of the ProtoLabelAdapter for sentences.

    >>> with document.get_labeler("sentences", "example.Sentence") as labeler
    >>>     # add labels

    >>> label_index = document.get_label_index("sentences", "example.Sentence")
    >>>     # do something with labels
    """

    def decorator(func: Callable[[], ProtoLabelAdapter]):
        _label_adapters[label_type_id] = func()
        return func

    return decorator


class _EventsClient:
    def __init__(self, address=None, *, stub=None):
        if stub is None:
            if address is None:
                discovery = _discovery.Discovery(Config())
                address = discovery.discover_events_service('v1')

            channel = grpc.insecure_channel(address)
            self._channel = channel
            self.stub = events_pb2_grpc.EventsStub(channel)
        else:
            self.stub = stub
        self._is_open = True

    def ensure_open(self):
        if not self._is_open:
            raise ValueError("Client to events service is not open")

    def open_event(self, event_id, only_create_new):
        request = events_pb2.OpenEventRequest(event_id=event_id, only_create_new=only_create_new)
        try:
            self.stub.OpenEvent(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise ValueError("Event already exists")

    def close_event(self, event_id):
        request = events_pb2.CloseEventRequest(event_id=event_id)
        self.stub.CloseEvent.with_call(request)

    def get_all_metadata(self, event_id):
        request = events_pb2.GetAllMetadataRequest(event_id=event_id)
        response = self.stub.GetAllMetadata(request)
        return response.metadata

    def add_metadata(self, event_id, key, value):
        request = events_pb2.AddMetadataRequest(event_id=event_id, key=key, value=value)
        self.stub.AddMetadata(request)

    def get_all_document_names(self, event_id):
        request = events_pb2.GetAllDocumentNamesRequest(event_id=event_id)
        response = self.stub.GetAllDocumentNames(request)
        return list(response.document_names)

    def add_document(self, event_id, document_name, text):
        request = events_pb2.AddDocumentRequest(event_id=event_id,
                                                document_name=document_name,
                                                text=text)
        self.stub.AddDocument(request)

    def get_document_text(self, event_id, document_name):
        request = events_pb2.GetDocumentTextRequest(event_id=event_id,
                                                    document_name=document_name)
        response = self.stub.GetDocumentText(request)
        return response.text

    def add_labels(self, event_id, document_name, index_name, labels, adapter):
        request = events_pb2.AddLabelsRequest(event_id=event_id, document_name=document_name,
                                              index_name=index_name)
        adapter.add_to_message(labels, request)
        self.stub.AddLabels(request)

    def get_labels(self, event_id, document_name, index_name, adapter):
        request = events_pb2.GetLabelsRequest(event_id=event_id,
                                              document_name=document_name,
                                              index_name=index_name)
        response = self.stub.GetLabels(request)
        return adapter.create_index_from_response(response)

    def close(self):
        self._is_open = False
        try:
            self._channel.close()
        except AttributeError:
            pass


class _Metadata(collections.abc.MutableMapping):
    def __init__(self, client: _EventsClient, event: Event):
        self._client = client
        self._event = event
        self._event_id = event.event_id
        self._metadata = {}

    def __contains__(self, key):
        self._event.ensure_open()
        if key in self._metadata:
            return True
        self._refresh_metadata()
        return key in self._metadata

    def __setitem__(self, key, value):
        self._event.ensure_open()
        if key in self:
            raise KeyError("Metadata already exists with key: " + key)
        self._metadata[key] = value
        self._client.add_metadata(self._event_id, key, value)

    def __getitem__(self, key):
        self._event.ensure_open()
        try:
            return self._metadata[key]
        except KeyError:
            self._refresh_metadata()
        return self._metadata[key]

    def __delitem__(self, v) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        self._event.ensure_open()
        self._refresh_metadata()
        return iter(self._metadata)

    def __len__(self) -> int:
        self._event.ensure_open()
        self._refresh_metadata()
        return len(self._metadata)

    def _refresh_metadata(self):
        self._event.ensure_open()
        response = self._client.get_all_metadata(self._event_id)
        self._metadata = response


class _GenericLabelAdapter(ProtoLabelAdapter):

    def __init__(self, distinct):
        self.distinct = distinct

    def create_label(self, *args, **kwargs):
        return GenericLabel(*args, **kwargs)

    def create_index_from_response(self, response):
        json_labels = response.json_labels
        labels = []
        for label in json_labels.labels:
            d = {}
            _utils.copy_struct_to_dict(label, d)
            generic_label = GenericLabel(**d)
            labels.append(generic_label)

        return label_index(labels, self.distinct)

    def add_to_message(self, labels, request):
        json_labels = request.json_labels
        for label in labels:
            _utils.copy_dict_to_struct(label.fields, json_labels.labels.add(), [label])


_generic_adapter = _GenericLabelAdapter(False)

_distinct_generic_adapter = _GenericLabelAdapter(True)

_label_adapters: Dict[str, ProtoLabelAdapter] = {
    constants.DISTINCT_GENERIC_LABEL_ID: _distinct_generic_adapter,
    constants.GENERIC_LABEL_ID: _generic_adapter
}


def _get_label_adapter(label_type_id) -> ProtoLabelAdapter:
    return _label_adapters[label_type_id]
