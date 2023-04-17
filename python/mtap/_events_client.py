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
import logging
from abc import abstractmethod, ABC
from typing import overload, Iterable, ContextManager, Union, List, cast

EventsAddressLike = Union[str, List[str], None]

logger = logging.getLogger("mtap.events_client")


@overload
def events_client(address: str) -> 'EventsClient':
    """Creates a client object for interacting with the events service.

    Args:
        address: The events service target e.g. 'localhost:9090'.

    Examples:
        >>> with EventsClient(address='localhost:50000') as client, \\
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = event.create_document(
        >>>         document_name='plaintext',
        >>>         text='The quick brown fox jumps over the lazy dog.'
        >>>     )
    """
    ...


@overload
def events_client(addresses: Iterable[str]) -> 'EventsClient':
    """Creates a client object for interacting with the events service.

    Args:
        addresses: A pool of events client addresses to use.
    """
    ...


@overload
def events_client() -> 'EventsClient':
    """Creates a client object for interacting with the events service.

    Uses service discovery to retrieve the address(es).
    """
    ...


def events_client(address: EventsAddressLike = None) -> 'EventsClient':
    logger.debug(f"Creating events client with address: {address}")
    from mtap._events_client_grpc import GrpcEventsClient
    if address is None or not isinstance(address, str) and len(address) == 0:
        from mtap.discovery import DiscoveryMechanism
        discovery = DiscoveryMechanism()
        address = discovery.discover_events_service('v1')
        if len(address) == 1:
            address = address[0]
        elif len(address) == 0:
            raise ValueError(
                "Did not discover any addresses for the events service."
            )

    if isinstance(address, str):
        return GrpcEventsClient(address)
    elif isinstance(address, Iterable):
        from mtap._events_client_pool import EventsClientPool
        return cast(EventsClient,
                    EventsClientPool(list(map(GrpcEventsClient, address))))
    else:
        raise TypeError("Unsupported address type.", type(address))


class EventsClient(ContextManager['EventsClient'], ABC):
    """Communicates with the events service.
    """
    @property
    @abstractmethod
    def instance_id(self):
        ...

    @abstractmethod
    def close(self):
        """Closes the events client"""
        ...

    @abstractmethod
    def ensure_open(self, instance_id):
        pass

    @abstractmethod
    def open_event(self, instance_id, event_id, only_create_new):
        pass

    @abstractmethod
    def close_event(self, instance_id, event_id):
        pass

    @abstractmethod
    def get_all_metadata(self, instance_id, event_id):
        pass

    @abstractmethod
    def add_metadata(self, instance_id, event_id, key, value):
        pass

    @abstractmethod
    def get_all_binary_data_names(self, instance_id, event_id):
        pass

    @abstractmethod
    def add_binary_data(self, instance_id, event_id, binary_data_name,
                        binary_data):
        pass

    @abstractmethod
    def get_binary_data(self, instance_id, event_id, binary_data_name):
        pass

    @abstractmethod
    def get_all_document_names(self, instance_id, event_id):
        pass

    @abstractmethod
    def add_document(self, instance_id, event_id, document_name, text):
        pass

    @abstractmethod
    def get_document_text(self, instance_id, event_id, document_name):
        pass

    @abstractmethod
    def get_label_index_info(self, instance_id, event_id, document_name):
        pass

    @abstractmethod
    def add_labels(self, instance_id, event_id, document_name, index_name,
                   labels, adapter):
        pass

    @abstractmethod
    def get_labels(self, instance_id, event_id, document_name, index_name,
                   adapter):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
