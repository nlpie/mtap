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
from typing import Optional, Dict, Any, TYPE_CHECKING

import grpc

from mtap import _discovery, _structs, Config
from mtap import data
from mtap.api.v1 import processing_pb2, processing_pb2_grpc
from mtap.processing import _base

if TYPE_CHECKING:
    import mtap

logger = logging.getLogger(__name__)


class ProcessorRunner(_base.ProcessingComponent):
    __slots__ = ('processor', 'component_id', 'params', 'metadata', 'processor_id', 'client')

    def __init__(self,
                 proc: 'mtap.EventProcessor',
                 client: 'Optional[mtap.EventsClient]',
                 identifier: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None):
        self.processor = proc
        self.params = params or {}
        self.metadata = proc.metadata
        self.processor_id = identifier
        self.component_id = identifier
        self.client = client

    def call_process(self, event_id, event_instance_id, params):
        p = dict(self.params)
        if params is not None:
            p.update(params)

        with _base.Processor.enter_context() as c, \
                data.Event(event_id=event_id,
                           event_service_instance_id=event_instance_id,
                           client=self.client) as event:
            with _base.Processor.started_stopwatch('process_method'):
                try:
                    result = self.processor.process(event, p)
                except Exception as e:
                    logger.error(
                        "Error while processing event_id %s through pipeline component  '%s'",
                        event_id, self.component_id)
                    raise e
            return result, c.times, event.created_indices

    def close(self):
        pass


class RemoteRunner(_base.ProcessingComponent):
    __slots__ = ('processor_id', 'component_id', '_address', 'params', '_channel', '_stub')

    def __init__(self, processor_id, component_id, address=None, params=None,
                 enable_proxy=False):
        self.processor_id = processor_id
        self.component_id = component_id
        self._address = address
        self.params = params
        address = self._address
        config = Config()
        if address is None:
            discovery = _discovery.Discovery(config)
            address = discovery.discover_processor_service(processor_id, 'v1')
        enable_proxy = enable_proxy or config.get('grpc.enable_proxy', False)
        self._channel = grpc.insecure_channel(address,
                                              options=[
                                                  ("grpc.lb_policy_name", "round_robin"),
                                                  ("grpc.enable_http_proxy", enable_proxy),
                                                  ('grpc.max_send_message_length',
                                                   config.get('grpc.max_send_message_length')),
                                                  ('grpc.max_receive_message_length',
                                                   config.get('grpc.max_receive_message_length'))
                                              ])
        self._stub = processing_pb2_grpc.ProcessorStub(self._channel)

    def call_process(self, event_id, event_instance_id, params):
        logger.debug('processor_id: %s calling process on event_id: %s with event_instance_id: %s',
                     self.processor_id, event_id, event_instance_id)
        p = dict(self.params or {})
        if params is not None:
            p.update(params)

        with _base.Processor.enter_context() as context:
            request = processing_pb2.ProcessRequest(processor_id=self.processor_id,
                                                    event_id=event_id,
                                                    event_service_instance_id=event_instance_id)
            _structs.copy_dict_to_struct(p, request.params, [p])
            with _base.Processor.started_stopwatch('remote_call'):
                try:
                    response = self._stub.Process(request)
                except Exception as e:
                    logger.error("Error while processing event_id %s through remote pipeline "
                                 "component  '%s'", event_id, self.component_id)
                    raise e
            r = {}
            _structs.copy_struct_to_dict(response.result, r)

            timing_info = response.timing_info
            for k, v in timing_info.items():
                context.add_time(k, v.ToTimedelta())

            created_indices = {}
            for created_index in response.created_indices:
                try:
                    doc_created_indices = created_indices[created_index.document_name]
                except KeyError:
                    doc_created_indices = []
                    created_indices[created_index.document_name] = doc_created_indices
                doc_created_indices.append(created_index.index_name)

            return r, context.times, created_indices

    def close(self):
        self._channel.close()
