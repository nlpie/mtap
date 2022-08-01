#  Copyright 2020 Regents of the University of Minnesota.
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
"""Events service client API and wrapper classes.

"""

import collections
import threading
import uuid
from typing import Iterator, List, Dict, MutableMapping, Generic, TypeVar, NamedTuple, \
    ContextManager, Iterable, Optional, Sequence, Union, Mapping, TYPE_CHECKING, Callable

import grpc
from grpc_health.v1 import health_pb2_grpc, health_pb2

from mtap import _config, _discovery, constants
from mtap.api.v1 import events_pb2, events_pb2_grpc
from mtap.data import _base, _labels, _label_adapters

if TYPE_CHECKING:
    import mtap
    import mtap.data as data

L = TypeVar('L', bound='data.Label')


class Event:
    """An object for interacting with a specific event locally or on the events service.

    The Event object functions as a map from string document names to :obj:`Document` objects that
    can be used to access document data from the events server.

    Keyword Args:
        event_id (~typing.Optional[str]):
            A globally-unique identifier for the event, or omit / none for a random UUID.
        client (~typing.Optional[EventsClient]):
            A client for an events service to push any changes to the event to.
        only_create_new (bool): Fails if the event already exists on the events service.

    Examples:
        >>> with EventsClient() as c, Event(event_id='id', client=c) as event:
        >>>     # use event
        >>>     ...
    """
    __slots__ = ('_event_id', '_client', '_lock', 'default_adapters', '_documents', '_metadata',
                 '_binaries', '_event_service_instance_id')

    def __init__(self, *, event_id: Optional[str] = None,
                 event_service_instance_id: Optional[str] = None,
                 client: Optional['mtap.EventsClient'] = None,
                 only_create_new: bool = False,
                 default_adapters: Optional[Mapping[str, 'data.ProtoLabelAdapter']] = None):
        self._event_id = event_id or str(uuid.uuid4())
        self._event_service_instance_id = event_service_instance_id
        self._lock = threading.RLock()
        self.default_adapters = default_adapters or {}
        self._client = client
        if self._client is not None:
            self._client = client.get_local_instance(self._event_service_instance_id)
            self._event_service_instance_id = self._client.instance_id
            self._client.open_event(self._event_id, only_create_new=only_create_new)

    @property
    def client(self) -> Optional['mtap.EventsClient']:
        return self._client

    @property
    def event_id(self) -> str:
        """str: The globally unique identifier for this event."""
        return self._event_id

    @property
    def event_service_instance_id(self) -> str:
        """str: The unique instance identifier for this event's paired event service."""
        return self._event_service_instance_id

    @property
    def documents(self) -> MutableMapping[str, 'mtap.Document']:
        """~typing.MutableMapping[str, Document]: A mutable mapping of strings to :obj:`Document`
        objects that can be used to query and add documents to the event."""
        try:
            return self._documents
        except AttributeError:
            self._documents = _Documents(self, self.client)
            return self._documents

    @property
    def metadata(self) -> MutableMapping[str, str]:
        """~typing.MutableMapping[str, str]: A mutable mapping of strings to strings that can be
        used to query and add metadata to the event."""
        try:
            return self._metadata
        except AttributeError:
            self._metadata = _Metadata(self, self.client)
            return self._metadata

    @property
    def binaries(self) -> MutableMapping[str, bytes]:
        """~typing.MutableMapping[str, str]: A mutable mapping of strings to bytes that can be used
        to query and add binary data to the event."""
        try:
            return self._binaries
        except AttributeError:
            self._binaries = _Binaries(self, self.client)
            return self._binaries

    @property
    def created_indices(self) -> Dict[str, List[str]]:
        """~typing.Dict[str, ~typing.List[str]]: A mapping of document names to a list of the names
        of all the label indices that have been added to that document"""
        return {document_name: document.created_indices
                for document_name, document in self.documents.items()}

    def close(self):
        """Closes this event. Lets the event service know that we are done with the event,
        allowing to clean up the event if no other clients have open leases to it."""
        if self.client is not None:
            self.release_lease()

    def create_document(self, document_name: str, text: str) -> 'mtap.Document':
        """Adds a document to the event keyed by `document_name` and
        containing the specified `text`.

        Args:
            document_name (str): The event-unique identifier for the document, example: 'plaintext'.
            text (str):
                The content of the document. This is a required field, document text is final and
                immutable, as changing the text would very likely invalidate any labels on the
                document.

        Returns:
            Document: The added document.

        Examples:

            >>> event = Event()
            >>> document = event.create_document('plaintext', text="The text of the document.")

        """
        if not isinstance(text, str):
            raise ValueError('text is not string.')
        document = Document(document_name, text=text, event=self)
        self.documents[document_name] = document
        return document

    def add_document(self, document: 'mtap.Document'):
        """Adds the document to this event, first uploading to events service if this event has a
        client connection to the events service.

        Args:
            document (~mtap.Document): The document to add to this event.

        Examples:

            >>> event = Event()
            >>> document = Document('plaintext', text="The text of the document.")
            >>> event.add_document(document)

        """
        if document._event is not None:
            raise ValueError('The document already exists on an event')
        document._event = self
        document._client = self.client
        document._event_id = self.event_id
        self.documents[document.document_name] = document

    def __enter__(self) -> 'Event':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def add_created_indices(self, created_indices):
        for k, v in created_indices.items():
            try:
                doc = self._documents[k]
                doc.add_created_indices(v)
            except KeyError:
                pass

    def lease(self):
        if self.client is not None:
            self.client.open_event(self.event_id, only_create_new=False)

    def release_lease(self):
        if self.client is not None:
            self.client.close_event(self.event_id)


class _WaitingIndex(NamedTuple('_WaitingIndex',
                               [('index_name', str),
                                ('labels', List['mtap.GenericLabel']),
                                ('waiting_on', List[int])])):
    """A label index that is waiting on some labels to be staticized before uploading.
    """


class Document:
    """An object for interacting with text and labels stored on an :class:`Event`.

    Documents are keyed by their name, and pipelines can store different pieces of
    related text on a single processing event using multiple documents. An example would be storing
    the text of one language on one document, and a translation on another, or storing the
    rtf or html encoding on one document, and the parsed plaintext on another document.

    Both the document text and any added label indices are immutable. This is to enable
    parallelization and distribution of processing, and to prevent changes to the dependency graph
    of label indices and text, which can make debugging difficult.

    Args:
        document_name (str): The document name identifier.

    Keyword Args:
        text (~typing.Optional[str]):
            The document text, can be omitted if this is an existing document and text needs to be
            retrieved from the events service.
        event (~typing.Optional[Event]):
            The parent event of this document. If the event has a client, then that client will be
            used to share changes to this document with all other clients of the Events service. In
            that case, text should only be specified if it is the known existing text of the
            document.

    Examples:
        Local document:

        >>> document = Document('plaintext', text='Some document text.')

        Existing distributed object:

        >>> with EventsClient(address='localhost:8080') as client, \\
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = event.documents['plaintext']
        >>>     document.text
        'Some document text fetched from the server.'

        New distributed object:

        >>> with EventsClient(address='localhost:8080') as client, \\
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = Document('plaintext', text='Some document text.')
        >>>     event.add_document(document)

        or

        >>> with EventsClient(address='localhost:8080') as client, \\
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = event.create_document('plaintext', text='Some document text.')

    """
    __slots__ = ('_document_name', '_event', '_client', '_event_id', '_text', '_labelers',
                 '_created_indices', '_waiting_indices', 'default_adapters', '_labels')

    def __init__(self,
                 document_name: str,
                 *,
                 text: Optional[str] = None,
                 event: Optional[Event] = None,
                 default_adapters: Optional[Mapping[str, 'data.ProtoLabelAdapter']] = None):
        if not isinstance(document_name, str):
            raise TypeError('Document name is not string.')
        self._document_name = document_name
        self._event = event
        self._client = None
        self._event_id = None
        if event is not None:
            self._client = event.client
            self._event_id = event.event_id
        self._text = text
        self._labelers = []
        self._created_indices = []
        self._waiting_indices = []
        self.default_adapters = default_adapters or {}
        if self._client is None and text is None:
            raise ValueError('Document without text or an event with a client to fetch the text '
                             'from.')

    @property
    def event(self) -> Event:
        """Event: The parent event of this document."""
        return self._event

    @property
    def document_name(self) -> str:
        """str: The unique identifier for this document on the event."""
        return self._document_name

    @property
    def text(self):
        """str: The document text."""
        if self._text is None and self._client is not None:
            self._text = self._client.get_document_text(self._event_id, self._document_name)
        return self._text

    @property
    def created_indices(self) -> List[str]:
        """~typing.List[str]: A list of all of the label index names that have created on this
                document using a labeler either locally or by remote pipeline components invoked on
                this document."""
        return list(self._created_indices)

    @property
    def labels(self) -> Mapping[str, 'data.LabelIndex']:
        try:
            return self._labels
        except AttributeError:
            self._labels = _LabelIndices(self)
            return self._labels

    def get_label_index(self,
                        label_index_name: str) -> 'data.LabelIndex[Union[mtap.GenericLabel, L]]':
        """Gets the document's label index with the specified key.

        Will fetch from the events service if it is not cached locally if the document has an event
        with a client. Uses the `label_adapter` argument to perform unmarshalling from the proto
        message if specified.

        Args:
            label_index_name (str): The name of the label index to get.

        Returns:
            LabelIndex: The requested label index.
        """
        return self.labels[label_index_name]

    def get_labeler(self,
                    label_index_name: str,
                    *, distinct: Optional[bool] = None):
        """Creates a function that can be used to add labels to a label index.

        Args:
            label_index_name (str): A document-unique identifier for the label index to be created.
            distinct (~typing.Optional[bool]):
                Optional, if using generic labels, whether to use distinct generic labels or
                non-distinct generic labels, will default to False.

        Returns:
            Labeler: A callable when used in conjunction with the 'with' keyword will automatically
            handle uploading any added labels to the server.

        Examples:
            >>> with document.get_labeler('sentences', distinct=True) as labeler:
            >>>     labeler(0, 25, sentence_type='STANDARD')
            >>>     sentence = labeler(26, 34)
            >>>     sentence.sentence_type = 'FRAGMENT'
        """
        if label_index_name in self._labelers:
            raise KeyError("Labeler already in use: " + label_index_name)
        label_adapter = self.get_default_adapter(label_index_name, distinct)

        labeler = Labeler(self._client, self, label_index_name, label_adapter)
        self._labelers.append(label_index_name)
        return labeler

    def add_labels(self,
                   label_index_name: str,
                   labels: Sequence[Union['data.Label', L]],
                   *, distinct: Optional[bool] = None,
                   label_adapter: Optional['data.ProtoLabelAdapter'] = None):
        """Skips using a labeler and adds the sequence of labels as a new label index.

        Args:
            label_index_name (str): The name of the label index.
            labels (~typing.Sequence[Label]): The labels to add.
            distinct (~typing.Optional[bool]):
                Whether the index is distinct or non-distinct.
            label_adapter (mtap.label_adapters.ProtoLabelAdapter): A label adapter to use.

        Returns:
            LabelIndex: The new label index created from the labels.
        """
        if label_index_name in self.labels:
            raise KeyError("Label index already exists with name: " + label_index_name)
        if label_adapter is None:
            if distinct is None:
                distinct = False
            label_adapter = self.get_default_adapter(label_index_name, distinct)
        labels, waiting_on = _labels._staticize(labels, self, label_index_name)
        if len(self._waiting_indices) > 0:
            label_ids = {id(label) for label in labels}
            self._check_waiting_indices(label_ids)

        if len(waiting_on) > 0:
            self._waiting_indices.append((label_index_name, labels, label_adapter, waiting_on))
        else:
            self._finalize_labels(label_adapter, label_index_name, labels)

    def _check_waiting_indices(self, updated_ids):
        waiting_indices = []
        for label_index_name, labels, label_adapter, waiting_on in self._waiting_indices:
            still_waiting = waiting_on.difference(updated_ids)
            if len(still_waiting) == 0:
                self._finalize_labels(label_adapter, label_index_name, labels)
            else:
                waiting_indices.append((label_index_name, labels, label_adapter, still_waiting))
        self._waiting_indices = waiting_indices

    def _finalize_labels(self, label_adapter, label_index_name, labels):
        label_adapter.store_references(labels)
        if self._client is not None:
            self._client.add_labels(event_id=self.event.event_id,
                                    document_name=self.document_name,
                                    index_name=label_index_name,
                                    labels=labels,
                                    adapter=label_adapter)
        self._created_indices.append(label_index_name)
        index = label_adapter.create_index(labels)
        self.labels.add_to_cache(label_index_name, index)
        return index

    def get_default_adapter(self, label_index_name: str,
                            distinct: Optional[bool] = None) -> Optional['data.ProtoLabelAdapter']:
        try:
            return self.default_adapters[label_index_name]
        except KeyError:
            pass
        try:
            return self.event.default_adapters[label_index_name]
        except (AttributeError, KeyError):
            return _label_adapters.DISTINCT_GENERIC_ADAPTER if distinct \
                else _label_adapters.GENERIC_ADAPTER

    def add_created_indices(self, created_indices: Iterable[str]):
        # Internal, used by the pipeline to add any indices created remotely to the
        # "created_indices" on a local document.
        return self._created_indices.extend(created_indices)


class Labeler(Generic[L], ContextManager['Labeler']):
    """Object provided by :func:`~'mtap.Document'.get_labeler` which is responsible for adding labels
    to a label index on a document.
    """
    __slots__ = ('_client', '_document', '_label_index_name', '_label_adapter', 'is_done',
                 '_current_labels', '_lock')

    def __init__(self,
                 client: 'mtap.EventsClient',
                 document: Document,
                 label_index_name: str,
                 label_adapter: 'data.ProtoLabelAdapter[L]'):
        self._client = client
        self._document = document
        self._label_index_name = label_index_name
        self._label_adapter = label_adapter
        self.is_done = False
        self._current_labels = []
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs) -> L:
        """Calls the constructor for the label type adding it to the list of labels to be uploaded.

        Args:
            args: Arguments passed to the label type's constructor.
            kwargs: Keyword arguments passed to the label type's constructor.

        Returns:
            Label: The object that was created by the label type's constructor.

        Examples:
            >>> labeler(0, 25, some_field='some_value', x=3)
            GenericLabel(start_index=0, end_index=25, some_field='some_value', x=3)
        """
        label = self._label_adapter.create_label(*args, document=self._document, **kwargs)
        self._current_labels.append(label)
        return label

    def __enter__(self) -> 'data.Labeler':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        self.done()

    def done(self):
        """Finalizes the label index, uploads the added labels to the events service.

        Normally called automatically on exit from a context manager block, but can be manually
        invoked if the labeler is not used in a context manager block."""
        with self._lock:
            if self.is_done:
                return
            self.is_done = True
            self._document.add_labels(self._label_index_name, self._current_labels,
                                      label_adapter=self._label_adapter)


def create_channel(address):
    config = _config.Config()
    options = config.get('grpc.events_channel_options', {})
    channel = grpc.insecure_channel(address, options=list(options.items()))

    health = health_pb2_grpc.HealthStub(channel)
    hcr = health.Check(health_pb2.HealthCheckRequest(service=constants.EVENTS_SERVICE_NAME))
    if hcr.status != health_pb2.HealthCheckResponse.SERVING:
        raise ValueError('Failed to connect to events service. Status:')
    return channel


class _ClientPool:
    __slots__ = ('_ptr', 'clients', 'instance_id_to_delegate')

    def __init__(self, channel_factory, addresses):
        self._ptr = 0
        self.clients = [EventsClient(address=addresses, channel_factory=channel_factory,
                                     _pool=self, _channel=channel_factory(a))
                        for a in addresses]
        self.instance_id_to_delegate = {d.instance_id: d for d in self.clients}

    def get_instance(self, instance_id):
        try:
            return self.instance_id_to_delegate[instance_id]
        except KeyError:
            i = self.clients[self._ptr]
            self._ptr = (self._ptr + 1) % len(self.clients)
            return i


class EventsClient:
    """A client object for interacting with the events service.

    Normally, users shouldn't have to use any of the methods on this object, as they are invoked by
    the globally distributed object classes of :obj:`Event`, :obj:`Document`, and :obj:`~data.Labeler`.

    Keyword Args:
        address (~typing.Optional[str]): The events service target e.g. 'localhost:9090' or
            omit/None to use service discovery.
        stub (~typing.Optional[~mtap.api.v1.events_pb2_grpc.EventsStub]): An existing events service
            client gRPC stub to use.

    Examples:
        >>> with EventsClient(address='localhost:50000') as client, \\
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = event.create_document(document_name='plaintext',
        >>>                                      text='The quick brown fox jumps over the lazy dog.')
    """
    __slots__ = ('addresses', 'channel_factory', '_pool', '_channel', 'stub', '_instance_id',
                 '_is_open')

    def __init__(self, address: Optional[Union[str, Iterable[str]]],
                 channel_factory: Callable[[str], grpc.Channel] = None,
                 _pool: Optional[_ClientPool] = None,
                 _channel: Optional[grpc.Channel] = None):
        if address is None:
            discovery = _discovery.Discovery(_config.Config())
            address = discovery.discover_events_service('v1')
        if isinstance(address, str):
            self.addresses = [address]
        elif isinstance(address, Iterable):
            self.addresses = list(address)
        else:
            raise ValueError("Unrecognized address type: " + str(type(address)))
        self.channel_factory = channel_factory
        if channel_factory is None:
            self.channel_factory = create_channel
        self._pool = _pool
        if self._pool is None:
            self._pool = _ClientPool(self.channel_factory, self.addresses)
        self._channel = _channel
        if self._channel is not None:
            self.stub = events_pb2_grpc.EventsStub(self._channel)
            r = self.stub.GetEventsInstanceId(events_pb2.GetEventsInstanceIdRequest())
            self._instance_id = r.instance_id
            self._is_open = True

    @property
    def instance_id(self) -> str:
        return self._instance_id

    def __enter__(self) -> 'EventsClient':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __reduce__(self):
        return _create_events_client, (self.addresses, self.channel_factory,)

    def get_local_instance(self, instance_id: Optional[str]) -> 'EventsClient':
        return self._pool.get_instance(instance_id)

    def ensure_open(self):
        if not self._is_open:
            raise ValueError("Client to events service is not open")

    def open_event(self, event_id: str, only_create_new: bool):
        request = events_pb2.OpenEventRequest(event_id=event_id, only_create_new=only_create_new)
        try:
            response = self.stub.OpenEvent(request)
            assert response is not None
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise ValueError("Event already exists") from e
            raise e

    def close_event(self, event_id):
        request = events_pb2.CloseEventRequest(event_id=event_id)
        try:
            response = self.stub.CloseEvent(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response is not None

    def get_all_metadata(self, event_id):
        request = events_pb2.GetAllMetadataRequest(event_id=event_id)
        try:
            response = self.stub.GetAllMetadata(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response.metadata

    def add_metadata(self, event_id, key, value):
        request = events_pb2.AddMetadataRequest(event_id=event_id, key=key, value=value)
        try:
            response = self.stub.AddMetadata(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response is not None

    def get_all_binary_data_names(self, event_id: str) -> List[str]:
        request = events_pb2.GetAllBinaryDataNamesRequest(event_id=event_id)
        try:
            response = self.stub.GetAllBinaryDataNames(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return list(response.binary_data_names)

    def add_binary_data(self, event_id: str, binary_data_name: str, binary_data: bytes):
        request = events_pb2.AddBinaryDataRequest(event_id=event_id,
                                                  binary_data_name=binary_data_name,
                                                  binary_data=binary_data)
        try:
            response = self.stub.AddBinaryData(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response is not None

    def get_binary_data(self, event_id: str, binary_data_name: str) -> bytes:
        request = events_pb2.GetBinaryDataRequest(event_id=event_id,
                                                  binary_data_name=binary_data_name)
        try:
            response = self.stub.GetBinaryData(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response.binary_data

    def get_all_document_names(self, event_id):
        request = events_pb2.GetAllDocumentNamesRequest(event_id=event_id)
        try:
            response = self.stub.GetAllDocumentNames(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return list(response.document_names)

    def add_document(self, event_id, document_name, text):
        request = events_pb2.AddDocumentRequest(event_id=event_id,
                                                document_name=document_name,
                                                text=text)
        try:
            response = self.stub.AddDocument(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response is not None

    def get_document_text(self, event_id, document_name):
        request = events_pb2.GetDocumentTextRequest(event_id=event_id,
                                                    document_name=document_name)
        try:
            response = self.stub.GetDocumentText(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response.text

    def get_label_index_info(self,
                             event_id: str,
                             document_name: str) -> List['data.LabelIndexInfo']:
        request = events_pb2.GetLabelIndicesInfoRequest(event_id=event_id,
                                                        document_name=document_name)
        try:
            response = self.stub.GetLabelIndicesInfo(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        result = []
        for index in response.label_index_infos:
            if index.type == events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.GENERIC:
                index_type = _base.LabelIndexType.GENERIC
            elif index.type == events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.CUSTOM:
                index_type = _base.LabelIndexType.CUSTOM
            else:
                index_type = _base.LabelIndexType.UNKNOWN
            result.append(_base.LabelIndexInfo(index.index_name, index_type))
        return result

    def add_labels(self, event_id, document_name, index_name, labels, adapter):
        request = events_pb2.AddLabelsRequest(event_id=event_id, document_name=document_name,
                                              index_name=index_name,
                                              no_key_validation=True)
        adapter.add_to_message(labels, request)
        try:
            response = self.stub.AddLabels(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return response is not None

    def get_labels(self, event_id, document_name, index_name, adapter):
        request = events_pb2.GetLabelsRequest(event_id=event_id,
                                              document_name=document_name,
                                              index_name=index_name)
        try:
            response = self.stub.GetLabels(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Failed to connect to events service on addresses: {}".format(self.addresses))
            raise e
        return adapter.create_index_from_response(response)

    def close(self):
        self._is_open = False
        try:
            self._channel.close()
        except AttributeError:
            pass


def _create_events_client(addresses, channel_factory):
    return EventsClient(address=addresses, channel_factory=channel_factory)


class _Documents(MutableMapping[str, Document]):
    __slots__ = ('event', 'event_id', 'client', 'documents')

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
            if not self.client.add_document(self.event_id, k, v.text):
                raise ValueError()
        v._event = self.event
        v._event_id = self.event_id
        v._client = self.client
        self.documents[k] = v

    def __delitem__(self, v: str) -> None:
        raise NotImplementedError()

    def _refresh_documents(self):
        if self.client is not None:
            document_names = self.client.get_all_document_names(self.event_id)
            for name in document_names:
                if name not in self.documents:
                    document = Document(name, event=self.event)
                    self.documents[name] = document


class _Metadata(MutableMapping[str, str]):
    __slots__ = ('_client', '_event', '_event_id', '_metadata')

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
            if not self._client.add_metadata(self._event_id, key, value):
                raise ValueError()

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
    __slots__ = ('_client', '_event', '_event_id', '_names', '_binaries')

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
            if not self._client.add_binary_data(self._event_id, key, value):
                raise ValueError()

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


class _LabelIndices(Mapping[str, 'data.LabelIndex']):
    __slots__ = ('_document', '_document_name', '_event_id', '_client', '_cache', '_names_cache')

    def __init__(self, document: Document):
        self._document = document
        self._document_name = document.document_name
        try:
            self._event_id = document.event.event_id
            self._client = document.event.client
        except AttributeError:
            self._event_id = None
            self._client = None
        self._cache = {}
        self._names_cache = set()

    def __getitem__(self, k: str) -> 'data.LabelIndex':
        try:
            return self._cache[k]
        except KeyError:
            pass

        if k not in self:
            raise KeyError

        if self._client is not None:
            label_adapter = self._document.get_default_adapter(k)
            if label_adapter is None:
                label_adapter = data.GENERIC_ADAPTER
            index = self._client.get_labels(self._event_id, self._document_name, k,
                                            adapter=label_adapter)
            for label in index:
                label.label_index_name = k
                label.document = self._document
            self._cache[k] = index
            self._names_cache.add(k)
            return index
        else:
            raise KeyError('Document does not have label index: ' + k)

    def __contains__(self, item):
        self._refresh_names()
        return item in self._names_cache

    def __len__(self) -> int:
        self._refresh_names()
        return len(self._names_cache)

    def __iter__(self) -> Iterator[str]:
        self._refresh_names()
        return iter(self._names_cache)

    def _refresh_names(self):
        if self._client is not None:
            infos = self._client.get_label_index_info(self._event_id, self._document_name)
            for info in infos:
                self._names_cache.add(info.index_name)

    def add_to_cache(self, label_index_name, index):
        self._cache[label_index_name] = index
        self._names_cache.add(label_index_name)
