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
from uuid import uuid1

from mtap import constants


class Discovery(abc.ABC):
    def __new__(cls, config, *args, **kwargs):
        if config['discovery'] == 'consul':
            cls = ConsulDiscovery
        return super(Discovery, cls).__new__(cls)

    @abc.abstractmethod
    def register_events_service(self, sid, address, port, version):
        raise NotImplementedError

    @abc.abstractmethod
    def discover_events_service(self, version):
        raise NotImplementedError

    @abc.abstractmethod
    def register_processor_service(self, name, sid, address, port, version):
        raise NotImplementedError

    @abc.abstractmethod
    def discover_processor_service(self, processor_name, version):
        raise NotImplementedError


class ConsulDiscovery(Discovery):
    def __init__(self, config):
        import consul
        host = config['consul.host']
        self.c = consul.Consul(host=host,
                               port=config['consul.port'],
                               scheme=config['consul.scheme'])

    def register_events_service(self, sid, address, port, version):
        name = constants.EVENTS_SERVICE_NAME
        self.c.agent.service.register(name,
                                      service_id=sid,
                                      port=port,
                                      check={
                                          'grpc': "{}:{}/{}".format(address, port, name),
                                          'interval': "10s",
                                          'status': 'passing'
                                      },
                                      tags=[version])

        def deregister():
            self.c.agent.service.deregister(name, service_id=sid)

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
            addresses.append("{}:{}".format(service['Node']['Address'], service['Service']['Port']))
        return "ipv4:" + ','.join(addresses)

    def register_processor_service(self, name, sid, address, port, version):
        self.c.agent.service.register(name,
                                      service_id=sid,
                                      port=port,
                                      check={
                                          'grpc': "{}:{}/{}".format(address, port, name),
                                          'interval': "10s",
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
            addresses.append("{}:{}".format(service['Node']['Address'], service['Service']['Port']))
        return "ipv4:" + ','.join(addresses)
