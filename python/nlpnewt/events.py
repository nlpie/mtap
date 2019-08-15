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
"""Events service client API and wrapper classes."""

import collections
import threading
import uuid
from abc import abstractmethod, ABC
from enum import Enum
from typing import Iterator, List, Dict, MutableMapping, Generic, TypeVar, Callable, \
    NamedTuple, ContextManager, Iterable, Optional, Sequence

import grpc
from grpc_health.v1 import health_pb2_grpc, health_pb2

from nlpnewt import _discovery
from nlpnewt import _structs
from nlpnewt import constants
from nlpnewt._config import Config
from nlpnewt.api.v1 import events_pb2_grpc, events_pb2
from nlpnewt.constants import EVENTS_SERVICE_NAME
from nlpnewt.label_indices import label_index, LabelIndex
from nlpnewt.labels import GenericLabel, Label

__all__ = [
    'Event',
    'LabelIndexType',
    'LabelIndexInfo',
    'Document',
    'Labeler',
    'proto_label_adapter',
    'ProtoLabelAdapter',
    'EventsClient'
]

L = TypeVar('L', bound=Label)


class Event:
    """The object created by :func:`~Events.open_event` or :func:`~Events.create_event` to interact
    with a specific event on the events service.

    The Event object functions as a map from string document names to :obj:`Document` objects that
    can be used to access document data from the events server.

    Parameters
    ----------
    event_id : str, optional
        A globally-unique identifier for the event, or omit / none for a random UUID.
    client: EventsClient
        A client for an events service to push any changes to the event to.
    only_create_new: bool
        Fails if the event already exists on the events service.

    Examples
    --------
    >>> with Event('id', client=client) as event:
    >>>     # use event

    """

    def __init__(self, event_id: Optional[str] = None, client: Optional['EventsClient'] = None,
                 only_create_new: bool = False):
        self._event_id = event_id or str(uuid.uuid4())
        self._client = client
        self._lock = threading.RLock()
        if client is not None:
            client.open_event(self._event_id, only_create_new=only_create_new)
        self._open = True

    @property
    def client(self) -> Optional['EventsClient']:
        return self._client

    @property
    def event_id(self) -> str:
        """
        Returns
        -------
        str
            The globally unique identifier for this event.
        """
        return self._event_id

    @property
    def documents(self) -> MutableMapping[str, 'Document']:
        """

        Returns
        -------
        MutableMapping[str, Document]
            An object that can be used to query and add documents to the event.

        """
        try:
            return self._documents
        except AttributeError:
            self._documents = _Documents(self, self.client)
            return self._documents

    @property
    def metadata(self) -> MutableMapping[str, str]:
        """

        Returns
        -------
        MutableMapping[str, str]
            An object that can be used to query and add metadata to the event.
        """
        try:
            return self._metadata
        except AttributeError:
            self._metadata = _Metadata(self, self.client)
            return self._metadata

    @property
    def binaries(self) -> MutableMapping[str, bytes]:
        """

        Returns
        -------
        MutableMapping[str, bytes]
            An object that can be used to query and add binary data to the event.

        """
        try:
            return self._binaries
        except AttributeError:
            self._binaries = _Binaries(self, self.client)
            return self._binaries

    @property
    def created_indices(self) -> Dict[str, List[str]]:
        """
        Returns
        -------
        dict[str, list[str]]
            A map of document names to the names of label indices that have been
            added to the document.
        """
        return {document_name: document.created_indices
                for document_name, document in self._documents.items()}

    def close(self):
        """Closes this event. Lets the event service know that we are done with the event,
        allowing to clean up the event if everyone is done with it.
        """
        if self.client is not None and self._open is True:
            with self._lock:
                # using double locking here to ensure that the event does not
                if self._open:
                    self._client.close_event(self._event_id)
                    self._open = False

    def create_document(self, document_name: str, text: str) -> 'Document':
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
        if not isinstance(text, str):
            raise ValueError('text is not string.')
        document = Document(document_name, text)
        document.event = self
        self.documents[document_name] = document
        return document

    def add_document(self, document: 'Document'):
        """Adds the document to this event, first uploading to events service if this event has a
        ``EventsClient`` object.

        Parameters
        ----------
        document: Document
            The document to add to this event.
        """
        self.documents[document.document_name] = document

    def __enter__(self) -> 'Event':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_val is not None:
            raise exc_val

    def add_created_indices(self, created_indices):
        for k, v in created_indices.items():
            try:
                doc = self._documents[k]
                doc.add_created_indices(v)
            except KeyError:
                pass


class LabelIndexType(Enum):
    """The type of serialized labels contained in the label index.
    """
    UNKNOWN = 0
    JSON = 1
    OTHER = 2


LabelIndexType.UNKNOWN.__doc__ = """Label index not set or type not known."""
LabelIndexType.JSON.__doc__ = """JSON / Generic Label index"""
LabelIndexType.OTHER.__doc__ = """Other / custom protobuf label index"""

LabelIndexInfo = NamedTuple('LabelIndexInfo',
                            [('index_name', str),
                             ('type', LabelIndexType)])
LabelIndexInfo.__doc__ = """Information about a label index contained on a document."""
LabelIndexInfo.index_name.__doc__ = """str: the name of the label index."""
LabelIndexInfo.type.__doc__ = """LabelIndexType: the type of the label index."""


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

    Parameters
    ----------
    document_name: str
        The document name identifier.
    text: optional str
        The document text, can be omitted if this is an existing document and text needs to be
        retrieved from the events service.
    """

    def __init__(self, document_name: str, text: Optional[str] = None):
        if not isinstance(document_name, str):
            raise TypeError('Document name is not string.')
        self._document_name = document_name
        self._text = text
        self._label_indices = {}
        self._labelers = []
        self._created_indices = []
        self._event = None
        self._client = None
        self._event_id = None

    @property
    def event(self) -> Event:
        """
        Returns
        -------
        Event
            The parent event of this document.
        """
        return self._event

    @event.setter
    def event(self, event: Event):
        self._event = event
        self._event_id = event.event_id
        self._client = event.client

    @property
    def document_name(self) -> str:
        """

        Returns
        -------
        str
            The unique identifier for this document on the event.
        """
        return self._document_name

    @property
    def text(self):
        """
        Returns
        -------
        str
            The document text.
        """
        if self._text is None and self._client is not None:
            self._text = self._client.get_document_text(self._event_id, self._document_name)
        return self._text

    @property
    def created_indices(self) -> List[str]:
        """
        Returns
        -------
        List[str]
            A list of all of the label index names that have created on this
            document using a labeler.
        """
        return list(self._created_indices)

    def get_label_indices_info(self) -> List[LabelIndexInfo]:
        """
        Returns
        -------
        list of LabelIndexInfo
            The list of label index information objects.
        """
        if self._client is not None:
            return self._client.get_label_index_info(self._event_id, self._document_name)
        return [LabelIndexInfo(k, LabelIndexType.JSON) for k, v in self._label_indices.items()]

    def get_label_index(self, label_index_name: str, *, label_type_id: str = None) -> LabelIndex:
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
        if label_index_name in self._label_indices:
            return self._label_indices[label_index_name]
        if label_type_id is None:
            label_type_id = constants.GENERIC_LABEL_ID

        if self._client is not None:
            label_adapter = _label_adapters[label_type_id]
            index = self._client.get_labels(self._event_id, self._document_name,
                                            label_index_name,
                                            adapter=label_adapter)
            self._label_indices[label_index_name] = index
            return index
        else:
            raise KeyError('Document does not have label index:', label_index_name)

    def get_labeler(self,
                    label_index_name: str,
                    *,
                    distinct: Optional[bool] = None,
                    label_type_id: Optional[str] = None) -> 'Labeler':
        """Creates a function that can be used to add labels to a label index.

        If the ``label_type_id`` parameter is specified it will use a custom
        :obj:`ProtoLabelAdapter` registered using :func:`proto_label_adapter`.

        Parameters
        ----------
        label_index_name : str
            A document-unique identifier for the label index to be created.
        label_type_id: str, optional
            Optional, the string identifier that an adapter has been registered under, or None if
            the default, generic labels are being used.
        distinct: bool, optional
            Optional, if using generic labels, whether to use distinct generic labels or
            non-distinct generic labels, will default to False

        Returns
        -------
        Labeler
            A callable when used in conjunction with the 'with' keyword will automatically handle
            uploading any added labels to the server.

        Examples
        --------
        >>> with document.get_labeler('sentences', distinct=True) as labeler:
        >>>     labeler(0, 25)
        >>>     sentence = labeler(26, 34)
        >>>     sentence.sentence_type = 'FRAGMENT'

        """
        if label_index_name in self._labelers:
            raise KeyError("Labeler already in use: " + label_index_name)
        if label_type_id is not None and distinct is not None:
            raise ValueError("Either 'distinct' or 'label_type_id' can be set, but not both.")
        if distinct is None and label_type_id is None:
            distinct = False
        if distinct is not None:
            label_type_id = (constants.DISTINCT_GENERIC_LABEL_ID
                             if distinct
                             else constants.GENERIC_LABEL_ID)

        labeler = Labeler(self._client, self, label_index_name, label_type_id)
        self._labelers.append(label_index_name)
        return labeler

    def add_labels(self,
                   label_index_name: str,
                   labels: Sequence['Label'],
                   *,
                   distinct: Optional[bool] = None,
                   label_type_id: Optional[str] = None,
                   label_adapter: Optional['ProtoLabelAdapter'] = None) -> LabelIndex:
        """Skips using a labeler and adds the sequence of labels as a new label index.

        Parameters
        ----------
        label_index_name: str
            The name of the label index.
        labels: Sequence[Label]
            The labels to add.
        distinct: bool, optional
            If using generic labels, whether the index is distinct or non-distinct.
        label_type_id: str, optional
            If using a custom registered adapter, the label_type_id of the adapter.
        label_adapter: ProtoLabelAdapter, optional
            A label adapter to use directly.

        Returns
        -------
        LabelIndex
            The new label index created from the labels.

        """
        if label_index_name in self._label_indices:
            raise KeyError("Label index already exists with name: " + label_index_name)
        count = sum(x is not None for x in (distinct, label_type_id, label_adapter))
        if count == 0:
            distinct = False
        elif count != 1:
            raise ValueError("Exactly one of 'distinct', 'label_type_id', and 'label_adapter' "
                             "parameters must be set.")
        if distinct is not None:
            label_type_id = (constants.DISTINCT_GENERIC_LABEL_ID
                             if distinct
                             else constants.GENERIC_LABEL_ID)
        if label_type_id is not None:
            label_adapter = _label_adapters[label_type_id]

        labels = sorted(labels, key=lambda l: l.location)
        if self._client is not None:
            self._client.add_labels(event_id=self.event.event_id,
                                    document_name=self.document_name,
                                    index_name=label_index_name,
                                    labels=labels,
                                    adapter=label_adapter)
        self._created_indices.append(label_index_name)
        index = label_adapter.create_index(labels)
        self._label_indices[label_index_name] = index
        return index

    def add_created_indices(self, created_indices: Iterable[str]):
        """Used by labelers or by pipelines when indices are added to the document.

        Parameters
        ----------
        created_indices: Iterable of str
            The label index names.

        """
        return self._created_indices.extend(created_indices)


class Labeler(Generic[L], ContextManager['Labeler']):
    """Object provided by :func:`~Document.get_labeler` which is responsible for adding labels to a
    label index on a document.

    See Also
    --------
    GenericLabel : The default Label type used if another registered label type is not specified.
    """

    def __init__(self,
                 client: 'EventsClient',
                 document: Document,
                 label_index_name: str,
                 label_type_id: str):
        self._client = client
        self._document = document
        self._label_index_name = label_index_name
        self._label_adapter = _label_adapters[label_type_id]
        self.is_done = False
        self._current_labels = []
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs) -> L:
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
        label = self._label_adapter.create_label(*args, **kwargs)
        self._current_labels.append(label)
        return label

    def __enter__(self) -> 'Labeler':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        self.done()

    def done(self):
        with self._lock:
            if self.is_done:
                return
            self.is_done = True
            self._document.add_labels(self._label_index_name, self._current_labels,
                                      label_adapter=self._label_adapter)


class ProtoLabelAdapter(ABC, Generic[L]):
    """Responsible for serialization and deserialization of non-standard label types.

    See Also
    --------
    proto_label_adapter: The decorator that stores proto label adapters for use.

    """

    @abstractmethod
    def create_label(self, *args, **kwargs) -> L:
        """Called by labelers to create labels.

        Should include the positional arguments 'start_index' and 'end_index', because those are
        required properties of labels.

        Parameters
        ----------
        args: Any
            args you want your labeler to take.
        kwargs: Any
            kwargs you want your labeler to take.

        Returns
        -------
        L
            The label type.

        """
        ...

    @abstractmethod
    def create_index_from_response(self, response: events_pb2.GetLabelsResponse) -> LabelIndex[L]:
        """Creates a LabelIndex from the response from an events service.

        Parameters
        ----------
        response: events_pb2.GetLabelsResponse
            The response from the events service.

        Returns
        -------
        LabelIndex[L]
            A label index containing all the labels from the events service.

        """
        ...

    @abstractmethod
    def create_index(self, labels: List[L]):
        """Creates a LabelIndex from an iterable of label objects.

        Parameters
        ----------
        labels: iterable of L
            The labels to create a label index from.

        Returns
        -------
        LabelIndex[L]
            A label index containing all of the labels in the list.

        """
        ...

    @abstractmethod
    def add_to_message(self, labels: List[L], request: events_pb2.AddLabelsRequest):
        """Adds a list of labels to the request to the event service to add labels.

        Parameters
        ----------
        labels: List[L]
            The list of labels that need to be sent to the server.
        request: events_pb2.AddLabelsRequest
            The request that will be sent to the server.
        """
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


class EventsClient:
    """A client object for interacting with the events service.

    Parameters
    ----------
    address: str, optional
        The events service target e.g. 'localhost:9090' or omit/None to use service discovery.
    stub: EventsStub
        An existing events service client stub to use.

    Examples
    --------
    >>> with EventsClient(address='localhost:50000' as client:
    >>>     with Event(event_id='1', client=client) as event:
    >>>         document = event.add_document(document_name='plaintext',
    >>>                                       text='The quick brown fox jumps over the lazy dog.')
    """

    def __init__(self, address: str = None, *, stub: events_pb2_grpc.EventsStub = None):
        if stub is None:
            if address is None:
                discovery = _discovery.Discovery(Config())
                address = discovery.discover_events_service('v1')

            channel = grpc.insecure_channel(address)

            health = health_pb2_grpc.HealthStub(channel)
            hcr = health.Check(health_pb2.HealthCheckRequest(service=EVENTS_SERVICE_NAME))
            if hcr.status != health_pb2.HealthCheckResponse.SERVING:
                raise ValueError('Failed to connect to events service. Status:')

            self._channel = channel
            self.stub = events_pb2_grpc.EventsStub(channel)
        else:
            self.stub = stub
        self._is_open = True

    def __enter__(self) -> 'EventsClient':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_type is not None:
            return False

    def ensure_open(self):
        """Makes sure the events client has not been closed.

        """
        if not self._is_open:
            raise ValueError("Client to events service is not open")

    def open_event(self, event_id: str, only_create_new: bool):
        """Opens the event for use.

        Parameters
        ----------
        event_id: str
            The unique event identifier.
        only_create_new: bool
            If true, will fail if the event already exists.

        """
        request = events_pb2.OpenEventRequest(event_id=event_id, only_create_new=only_create_new)
        try:
            self.stub.OpenEvent(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise ValueError("Event already exists")

    def close_event(self, event_id):
        """Closes the event.

        Parameters
        ----------
        event_id: str
            The unique event identifier.

        """
        request = events_pb2.CloseEventRequest(event_id=event_id)
        self.stub.CloseEvent(request)

    def get_all_metadata(self, event_id):
        request = events_pb2.GetAllMetadataRequest(event_id=event_id)
        response = self.stub.GetAllMetadata(request)
        return response.metadata

    def add_metadata(self, event_id, key, value):
        request = events_pb2.AddMetadataRequest(event_id=event_id, key=key, value=value)
        self.stub.AddMetadata(request)

    def get_all_binary_data_names(self, event_id: str) -> List[str]:
        request = events_pb2.GetAllBinaryDataNamesRequest(event_id=event_id)
        response = self.stub.GetAllBinaryDataNames(request)
        return list(response.binary_data_names)

    def add_binary_data(self, event_id: str, binary_data_name: str, binary_data: bytes):
        request = events_pb2.AddBinaryDataRequest(event_id=event_id,
                                                  binary_data_name=binary_data_name,
                                                  binary_data=binary_data)
        self.stub.AddBinaryData(request)

    def get_binary_data(self, event_id: str, binary_data_name: str) -> bytes:
        request = events_pb2.GetBinaryDataRequest(event_id=event_id,
                                                  binary_data_name=binary_data_name)
        response = self.stub.GetBinaryData(request)
        return response.binary_data

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

    def get_label_index_info(self, event_id: str, document_name: str) -> List[LabelIndexInfo]:
        request = events_pb2.GetLabelIndicesInfoRequest(event_id=event_id,
                                                        document_name=document_name)
        response = self.stub.GetLabelIndicesInfo(request)
        result = []
        for index in response.label_index_infos:
            if index.type == events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.JSON:
                index_type = LabelIndexType.JSON
            elif index.type == events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.OTHER:
                index_type = LabelIndexType.OTHER
            else:
                index_type = LabelIndexType.UNKNOWN
            result.append(LabelIndexInfo(index.index_name, index_type))
        return result

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


class _Documents(MutableMapping[str, Document]):
    def __init__(self, event: Event, client: Optional[EventsClient]):
        self.event = event
        self.event_id = event.event_id
        self.client = client
        self.documents = {}

    def __contains__(self, document_name: str) -> bool:
        if not isinstance(document_name, str):
            return False
        if document_name in self.documents:
            return True
        self._refresh_documents()
        return document_name in self.documents

    def __getitem__(self, document_name) -> 'Document':
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
        >>> plaintext_document = event.documents['plaintext']
        >>> plaintext_document.text
        'The quick brown fox jumped over the lazy dog.'

        """
        if not isinstance(document_name, str):
            raise KeyError
        try:
            return self.documents[document_name]
        except KeyError:
            pass
        self._refresh_documents()
        return self.documents[document_name]

    def __len__(self) -> int:
        self._refresh_documents()
        return len(self.documents)

    def __iter__(self) -> Iterator[str]:
        self._refresh_documents()
        return iter(self.documents)

    def __setitem__(self, k: str, v: Document) -> None:
        if self.client is not None:
            self.client.add_document(self.event_id, k, v.text)
        v.event = self
        self.documents[k] = v

    def __delitem__(self, v: str) -> None:
        raise NotImplementedError()

    def _refresh_documents(self):
        if self.client is not None:
            document_names = self.client.get_all_document_names(self.event_id)
            for name in document_names:
                if name not in self.documents:
                    document = Document(name)
                    document.event = self
                    self.documents[name] = document


class _Metadata(MutableMapping[str, str]):
    def __init__(self, event: Event, client: Optional[EventsClient] = None):
        self._client = client
        self._event = event
        self._event_id = event.event_id
        self._metadata = {}

    def __contains__(self, key):
        if key in self._metadata:
            return True
        self._refresh_metadata()
        return key in self._metadata

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError("Metadata already exists with key: " + key)
        self._metadata[key] = value
        if self._client is not None:
            self._client.add_metadata(self._event_id, key, value)

    def __getitem__(self, key):
        try:
            return self._metadata[key]
        except KeyError:
            self._refresh_metadata()
        return self._metadata[key]

    def __delitem__(self, v) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        self._refresh_metadata()
        return iter(self._metadata)

    def __len__(self) -> int:
        self._refresh_metadata()
        return len(self._metadata)

    def _refresh_metadata(self):
        if self._client is not None:
            response = self._client.get_all_metadata(self._event_id)
            self._metadata.update(response)


class _Binaries(collections.abc.MutableMapping):
    def __init__(self, event: Event, client: Optional[EventsClient] = None):
        self._client = client
        self._event = event
        self._event_id = event.event_id
        self._names = set()
        self._binaries = {}

    def __contains__(self, key):
        if key in self._names:
            return True
        self._refresh_binaries()
        return key in self._names

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError("Binary already exists with name: " + key)
        self._names.add(key)
        self._binaries[key] = value
        if self._client is not None:
            self._client.add_binary_data(self._event_id, key, value)

    def __getitem__(self, key):
        try:
            return self._binaries[key]
        except KeyError:
            pass
        if self._client is not None:
            b = self._client.get_binary_data(event_id=self._event_id, binary_data_name=key)
            self._names.add(b)
            self._binaries[key] = b
        return self._binaries[key]

    def __delitem__(self, v) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        self._refresh_binaries()
        return iter(self._names)

    def __len__(self) -> int:
        self._refresh_binaries()
        return len(self._names)

    def _refresh_binaries(self):
        if self._client is not None:
            response = self._client.get_all_binary_data_names(self._event_id)
            self._names.update(response)


class _GenericLabelAdapter(ProtoLabelAdapter):

    def __init__(self, distinct):
        self.distinct = distinct

    def create_label(self, *args, **kwargs):
        return GenericLabel(*args, **kwargs)

    def create_index(self, labels: List[L]):
        return label_index(labels, self.distinct)

    def create_index_from_response(self, response):
        json_labels = response.json_labels
        labels = []
        for label in json_labels.labels:
            d = {}
            _structs.copy_struct_to_dict(label, d)
            generic_label = GenericLabel(**d)
            labels.append(generic_label)

        return label_index(labels, self.distinct)

    def add_to_message(self, labels, request):
        json_labels = request.json_labels
        for label in labels:
            _structs.copy_dict_to_struct(label.fields, json_labels.labels.add(), [label])


_generic_adapter = _GenericLabelAdapter(False)

_distinct_generic_adapter = _GenericLabelAdapter(True)

_label_adapters = {
    constants.DISTINCT_GENERIC_LABEL_ID: _distinct_generic_adapter,
    constants.GENERIC_LABEL_ID: _generic_adapter
}


def _get_label_adapter(label_type_id) -> ProtoLabelAdapter:
    return _label_adapters[label_type_id]
