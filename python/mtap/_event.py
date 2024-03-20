# Copyright (c) Regents of the University of Minnesota.
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
import uuid
from typing import ContextManager, Dict, MutableMapping, Optional, Iterator, \
    List, Mapping, TYPE_CHECKING, cast

from mtap._document import Document
from mtap._events_client import EventsClient

if TYPE_CHECKING:
    from mtap._label_adapters import ProtoLabelAdapter


class Event(ContextManager['Event']):
    """An object for interacting with a specific event locally or on the
    events service.

    The Event object functions as a map from string document names to
    :obj:`Document` objects that can be used to access document data from the
    events server.

    To connect to the events service and load an existing event, all of
    ``event_id``, ``event_service_instance_id``, and ``client`` must be
    specified.

    Args:
        event_id: A globally-unique identifier for the event, or omit / none
            for a random UUID.
        client: If specified, connects to the events service with id
            ``event_service_instance_id`` and accesses either accesses the
            existing event with the ``event_id`` or creates a new one.
        only_create_new: Fails if the event already exists on the events
            service.

    Attributes:
        label_adapters: A mapping of string label index names to
            :class:`ProtoLabelAdapter` instances to perform custom
            mapping of label types.

    Examples:
        Creating a new event locally.

        >>> event = Event()

        Creating a new event remotely.

        >>> with EventsClient(address='localohost:50000') as c, \
        >>>     Event(event_id='id', client=c) as event:
        >>>     # use event
        >>>     ...

        Connecting to an existing event.

        >>> with EventsClient(address='localohost:50000') as c, \
        >>>     Event(event_id='id',
        >>>           event_service_instance_id='events_sid',
        >>>           client=c) as event:
        >>>
        >>>
    """
    __slots__ = ('_event_id', '_client', '_lock', 'label_adapters',
                 '_documents_cache', '_metadata_cache', '_binaries_cache',
                 '_event_service_instance_id', '_leased')

    label_adapters: Mapping[str, 'ProtoLabelAdapter']

    def __init__(
            self, event_id: Optional[str] = None,
            *, client: Optional['EventsClient'] = None,
            only_create_new: bool = False,
            label_adapters: Optional[Mapping[str, 'ProtoLabelAdapter']] = None,
            event_service_instance_id: Optional[str] = None,
            lease: bool = True
    ):
        self._event_id = event_id or str(uuid.uuid4())
        self._event_service_instance_id = event_service_instance_id
        if label_adapters is not None:
            self.label_adapters = dict(label_adapters)
        else:
            self.label_adapters = {}
        self._client = client
        self._leased = lease
        if self._client is not None and self._leased:
            self._event_service_instance_id = self._client.open_event(
                event_service_instance_id,
                self._event_id,
                only_create_new=only_create_new
            )
        self._documents_cache = None
        self._metadata_cache = None
        self._binaries_cache = None

    @property
    def client(self) -> Optional['EventsClient']:
        return self._client

    @property
    def event_id(self) -> str:
        """The globally unique identifier for this event."""
        return self._event_id

    @property
    def event_service_instance_id(self) -> str:
        """The unique instance identifier for this event's paired event
        service."""
        return self._event_service_instance_id

    @property
    def documents(self) -> Mapping[str, Document]:
        """A mutable mapping of strings to :obj:`Document` objects that can be
        used to query and add documents to the event."""
        if self._documents_cache is None:
            self._documents_cache = _Documents(self)
        return self._documents_cache

    @property
    def metadata(self) -> MutableMapping[str, str]:
        """A mutable mapping of strings to strings that can be used to query
        and add metadata to the event."""
        if self._metadata_cache is None:
            self._metadata_cache = _Metadata(self)
        return self._metadata_cache

    @property
    def binaries(self) -> MutableMapping[str, bytes]:
        """A mutable mapping of strings to bytes that can be used to query and
        add binary data to the event."""
        if not self._binaries_cache:
            self._binaries_cache = _Binaries(self)
        return self._binaries_cache

    @property
    def created_indices(self) -> Dict[str, List[str]]:
        """A mapping of document names to a list of the names of all the label
        indices that have been added to that document"""
        try:
            return {document_name: document.created_indices
                    for document_name, document in self._documents_cache.data.items()}
        except AttributeError:
            return {}

    def close(self):
        """Closes this event. Lets the event service know that we are done
        with the event, allowing to clean up the event if no other clients
        have open leases to it."""
        if self.client is not None and self._leased:
            self.release_lease()

    def create_document(self,
                        document_name: str,
                        text: str) -> Document:
        """Adds a document to the event keyed by `document_name` and
        containing the specified `text`.

        Args:
            document_name: The event-unique identifier for the document,
                example: ``'plaintext'``.
            text: The content of the document. This is a required field,
                and the document text is final and immutable.

        Returns:
            The added document.

        Examples:

            >>> event = Event()
            >>> doc = event.create_document('plaintext',
            >>>                             text="The text of the document.")

        """
        if not isinstance(text, str):
            raise ValueError('text is not string.')
        document = Document(document_name, text=text)
        self.add_document(document)
        return document

    def add_document(self, document: Document):
        """Adds the document to this event, first uploading to events service
        if this event has a client connection to the events service.

        Args:
            document: The document to add to this event.

        Examples:

            >>> event = Event()
            >>> doc = Document('plaintext',
            >>>                text="The text of the document.")
            >>> event.add_document(doc)

        """
        if document.event is not None:
            raise ValueError('This document already has an event, it cannot '
                             'be added to another.')
        document._event = self
        name = document.document_name
        if self.client is not None:
            self.client.add_document(*ids(self), name, document.text)
        cast(_Documents, self.documents).data[name] = document

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not KeyboardInterrupt:
            self.close()

    def add_created_indices(self, created_indices):
        for k, v in created_indices.items():
            try:
                doc = self.documents[k]
                doc.add_created_indices(v)
            except KeyError:
                pass

    def lease(self):
        if self.client is not None:
            self.client.open_event(self._event_service_instance_id,
                                   self.event_id,
                                   only_create_new=False)

    def release_lease(self):
        if self.client is not None:
            self.client.close_event(self.event_service_instance_id,
                                    self.event_id)


def ids(event):
    return event.event_service_instance_id, event.event_id


class _Documents(Mapping[str, Document]):
    __slots__ = ('event', 'data')

    def __init__(self, event):
        self.event = event
        self.data = {}

    def __contains__(self, document_name: str) -> bool:
        if not isinstance(document_name, str):
            return False
        if document_name in self.data:
            return True
        self._refresh_documents()
        return document_name in self.data

    def __getitem__(self, document_name) -> Document:
        if not isinstance(document_name, str):
            raise KeyError
        try:
            return self.data[document_name]
        except KeyError:
            pass
        self._refresh_documents()
        return self.data[document_name]

    def __len__(self) -> int:
        self._refresh_documents()
        return len(self.data)

    def __iter__(self) -> Iterator[str]:
        self._refresh_documents()
        return iter(self.data)

    def _refresh_documents(self):
        if self.event.client is not None:
            document_names = self.event.client.get_all_document_names(
                *ids(self.event)
            )
            for name in document_names:
                if name not in self.data:
                    document = Document(name, event=self.event)
                    self.data[name] = document


class _Metadata(MutableMapping[str, str]):
    __slots__ = ('event', 'data')

    def __init__(self, event: Event):
        self.event = event
        self.data = {}

    def __contains__(self, key):
        if key in self.data:
            return True
        self._refresh_metadata()
        return key in self.data

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError("Metadata already exists with key: " + key)
        self.data[key] = value
        if self.event.client is not None:
            if not self.event.client.add_metadata(*ids(self.event),
                                                  key, value):
                raise ValueError()

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            self._refresh_metadata()
        return self.data[key]

    def __delitem__(self, v) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        self._refresh_metadata()
        return iter(self.data)

    def __len__(self) -> int:
        self._refresh_metadata()
        return len(self.data)

    def _refresh_metadata(self):
        if self.event.client is not None:
            response = self.event.client.get_all_metadata(*ids(self.event))
            self.data.update(response)


class _Binaries(MutableMapping[str, bytes]):
    __slots__ = ('event', 'names', 'data')

    def __init__(self, event: Event):
        self.event = event
        self.names = set()
        self.data = {}

    def __contains__(self, key):
        if key in self.names:
            return True
        self._refresh_binaries()
        return key in self.names

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError("Binary already exists with name: " + key)
        self.names.add(key)
        self.data[key] = value
        if self.event.client is not None:
            if not self.event.client.add_binary_data(*ids(self.event),
                                                     key, value):
                raise ValueError()

    def __getitem__(self, key):
        try:
            return self.data[key]
        except KeyError:
            pass
        if self.event.client is not None:
            b = self.event.client.get_binary_data(*ids(self.event),
                                                  binary_data_name=key)
            self.names.add(b)
            self.data[key] = b
        return self.data[key]

    def __delitem__(self, v) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        self._refresh_binaries()
        return iter(self.names)

    def __len__(self) -> int:
        self._refresh_binaries()
        return len(self.names)

    def _refresh_binaries(self):
        if self.event.client is not None:
            response = self.event.client.get_all_binary_data_names(
                *ids(self.event)
            )
            self.names.update(response)
