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
"""Internal service discovery magic."""

import abc
from typing import ClassVar, Dict, Type, Callable, TypeVar, List

from mtap import constants, _config


T = TypeVar('T', bound='DiscoveryMechanism')


class DiscoveryMechanism(abc.ABC):
    """Abstract base class for service discovery mechanisms.

    Uses a registry system to register subclasses. Note that your subclass
    must have a zero-args constructor, which will be used to instantiate the
    class. Your implementation can pass state using the :class:`mtap.Config`
    object. Note that to use your discovery mechanism its containing module
    must be imported somewhere before it can be instantiated. See the example
    below or the ConsulDiscovery class in this source file for how to
    implement.

    Examples:
        Implementing a new discovery mechanism.

        >>> import mtap
        >>>
        >>> @DiscoveryMechanism.register('my_discovery')
        >>> class MyDiscovery(DiscoveryMechanism):
        >>>     def __init__(self):
        >>>         config = mtap.Config()
        >>>         # retrieve configuration from config object.
        >>>     ...  # implement methods
        >>>
        >>> with mtap.Config() as c:
        >>>     c['discovery'] = 'my_discovery'
        >>>     with mtap.EventsClient() as client:
        >>>         ...  # client will use MyDiscovery to lookup event service

    """
    registry: 'ClassVar[Dict[str, Type[DiscoveryMechanism]]]' = {}

    def __new__(cls):
        config = _config.Config()
        cls = DiscoveryMechanism.registry[config['discovery']]
        return super(DiscoveryMechanism, cls).__new__(cls)

    @abc.abstractmethod
    def register_events_service(self,
                                sid: str,
                                address: str,
                                port: int,
                                version: str) -> Callable[[], None]:
        """Registers an events service for discovery.

        Use the ``mtap.constants.EVENTS_SERVICE_NAME`` value as a service
        name if one is needed.

        Args:
            sid: The service instance unique identifier.
            address: The address.
            port: The port.
            version: An API version identifier for the service.

        Returns:
            A zero-argument callback which can be used to de-register this
            registered service.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def discover_events_service(self, version: str) -> List[str]:
        """Discovers any available events services.

        Args:
            version: An API version identifier to filter on.

        Returns:
            A list of ipv4 addresses

        """
        raise NotImplementedError

    @abc.abstractmethod
    def register_processor_service(self, name, sid, address, port, version):
        raise NotImplementedError

    @abc.abstractmethod
    def discover_processor_service(self, processor_name, version):
        raise NotImplementedError

    @classmethod
    def register(cls, name: str) -> Callable[[T], T]:
        def decorator(dm_cls: T) -> T:
            DiscoveryMechanism.registry[name] = dm_cls
            return dm_cls

        return decorator


@DiscoveryMechanism.register('consul')
class ConsulDiscovery(DiscoveryMechanism):
    def __init__(self):
        import consul
        config = _config.Config()
        host = config['consul.host']
        self.interval = config['consul.interval']
        self.c = consul.Consul(host=host,
                               port=config['consul.port'],
                               scheme=config['consul.scheme'])

    def register_events_service(self, sid, address, port, version):
        name = constants.EVENTS_SERVICE_NAME
        self.c.agent.service.register(name,
                                      service_id=sid,
                                      port=port,
                                      check={
                                          'grpc': "{}:{}/{}".format(address,
                                                                    port,
                                                                    name),
                                          'interval': self.interval,
                                          'status': 'passing'
                                      },
                                      tags=[version])

        def deregister():
            self.c.agent.service.deregister(service_id=sid)

        return deregister

    def discover_events_service(self, version):
        """Delegates discovery to grpc's dns name resolution.

        """
        name = constants.EVENTS_SERVICE_NAME
        _, services = self.c.health.service(name, tag='v1')
        addresses = []
        if len(services) == 0:
            raise ValueError('No addresses found for events service')
        for service in services:
            addresses.append("{}:{}".format(service['Node']['Address'],
                                            service['Service']['Port']))
        return addresses

    def register_processor_service(self, name, sid, address, port, version):
        self.c.agent.service.register(name,
                                      service_id=sid,
                                      port=port,
                                      check={
                                          'grpc': "{}:{}/{}".format(address,
                                                                    port,
                                                                    name),
                                          'interval': self.interval,
                                          'status': 'passing'
                                      },
                                      tags=[constants.PROCESSING_SERVICE_TAG])

        def deregister():
            self.c.agent.service.deregister(service_id=sid)

        return deregister

    def discover_processor_service(self, processor_name, version):
        tag = constants.PROCESSING_SERVICE_TAG
        _, services = self.c.health.service(processor_name, tag=tag)
        addresses = []
        for service in services:
            addresses.append("{}:{}".format(service['Node']['Address'],
                                            service['Service']['Port']))
        return "ipv4:" + ','.join(addresses)
