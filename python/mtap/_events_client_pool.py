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
from typing import ContextManager

from mtap._events_client import EventsClient


class EventsClientPool(ContextManager[EventsClient]):
    __slots__ = ('_ptr', '_clients', '_map')

    def __init__(self, clients):
        if clients is None or len(clients) == 0:
            raise ValueError(
                "Trying to start a client pool with no clients"
            )
        self._clients = list(clients)
        self._ptr = 0
        self._map = None

    def __reduce__(self):
        return EventsClientPool, (self._clients,)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for client in self._clients:
            client.close()

    @property
    def instance_id(self):
        raise NotImplementedError("EventsClientPool has no instance id.")

    def __get_instance(self, instance_id):
        if instance_id is None:
            raise ValueError("instance_id cannot be `None`")
        if self._map is None:
            # Generate Map
            self._map = {c.instance_id: c for c in self._clients}
        try:
            return self._map[instance_id]
        except KeyError:
            raise KeyError(f"instance_id: {instance_id} not found. "
                           f"Available instances: "
                           f"{self._map.keys()}")

    def open_event(self, instance_id, event_id, only_create_new):
        if instance_id is None:
            # Creating a new event, grab a client via round-robin
            client = self._clients[self._ptr]
            self._ptr = (self._ptr + 1) % len(self._clients)
        else:
            client = self.__get_instance(instance_id)
        return client.open_event(instance_id, event_id, only_create_new)

    def __getattr__(self, item):
        def f(*args, **kwargs):
            if len(args) > 0:
                instance_id = args[0]
            else:
                try:
                    instance_id = kwargs['instance_id']
                except KeyError:
                    raise TypeError(
                        f"{item}() missing 1 required positional argument: "
                        f"'instance_id'"
                    )
            client = self.__get_instance(instance_id)
            return getattr(client, item)(*args, **kwargs)
        return f


EventsClient.register(EventsClientPool)
