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

import nlpnewt


class Discovery(abc.ABC):
    def __new__(cls, config, *args, **kwargs):
        if config['discovery'] == 'consul':
            cls = ConsulDiscovery
        return super(Discovery, cls).__new__(cls)

    @abc.abstractmethod
    def register_events_service(self, address, port, version):
        raise NotImplementedError

    @abc.abstractmethod
    def discover_events_service(self, version):
        raise NotImplementedError

    @abc.abstractmethod
    def register_processor_service(self, address, port, processor_name, version):
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
        self.dns = config['consul.dns_ip'] + ":" + str(config['consul.dns_port'])

    def register_events_service(self, address, port, version):
        name = nlpnewt.events_service_name()
        self.c.agent.service.register(name,
                                      port=port,
                                      check={
                                          'name': 'gRPC Health Check',
                                          'grpc': f"{address}:{port}",
                                          'interval': "10s",
                                          'status': 'passing'
                                      },
                                      tags=[version])

        def deregister():
            self.c.agent.service.deregister(name)

        return deregister

    def discover_events_service(self, version):
        """Delegates discovery to grpc's dns name resolution.

        """
        name = nlpnewt.events_service_name()
        _, services = self.c.health.service(name, tag='v1')
        port = services[0]['Service']['Port']
        return f"dns://{self.dns}/{version}.{name}.service.consul:{port}"

    def register_processor_service(self, address, port, processor_id, version):
        self.c.agent.service.register(processor_id,
                                      port=port,
                                      check={
                                          'name': 'gRPC Health Check',
                                          'grpc': f"{address}:{port}",
                                          'interval': "10s",
                                          'status': 'passing'
                                      },
                                      tags=[nlpnewt.processing_service_tag()])

        def deregister():
            self.c.agent.service.deregister(service_id=processor_id)

        return deregister

    def discover_processor_service(self, processor_name, version):
        tag = nlpnewt.processing_service_tag()
        _, services = self.c.health.service(processor_name, tag=tag)
        port = services[0]['Service']['Port']
        return f"dns://{self.dns}/{tag}.{processor_name}.service.consul:{port}"
