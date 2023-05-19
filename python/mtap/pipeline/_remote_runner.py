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
import copy
import logging
from typing import ContextManager

from grpc import RpcError, StatusCode
from grpc.aio import insecure_channel

from mtap import Config
from mtap._structs import copy_dict_to_struct, copy_struct_to_dict
from mtap.api.v1 import processing_pb2_grpc, processing_pb2
from mtap.processing import ProcessingException
from mtap.processing import Processor
from mtap.processing.results import ComponentResult

logger = logging.getLogger('mtap.processing')


class RemoteProcessorRunner(ContextManager['RemoteRunner']):
    def __init__(
            self,
            processor_name,
            component_id,
            address=None,
            params=None,
            enable_proxy=None
    ):
        self.processor_name = processor_name
        self.component_id = component_id or processor_name
        self.address = address
        self.params = params or {}
        address = self.address
        config = Config()
        if enable_proxy is not None:
            config['grpc.processor_options.gprc.enable_http_proxy'] \
                = enable_proxy
        if address is None:
            from mtap.discovery import DiscoveryMechanism
            discovery = DiscoveryMechanism()
            address = discovery.discover_processor_service(processor_name,
                                                           'v1')
        channel_options = config.get('grpc.processor_options', {})
        self._channel = insecure_channel(address, options=list(
            channel_options.items()))
        self._stub = processing_pb2_grpc.ProcessorStub(self._channel)

    def __exit__(self, __exc_type, __exc_value, __traceback):
        self.close()

    async def call_process(self, event_id, event_instance_id, params):
        logger.debug('calling process (%s, %s) on event: (%s, %s)',
                     self.processor_name, self.address, event_id,
                     event_instance_id)
        p = copy.deepcopy(self.params)
        if params is not None:
            p.update(params)

        with Processor.enter_context() as context:
            request = processing_pb2.ProcessRequest(
                processor_id=self.processor_name,
                event_id=event_id,
                event_service_instance_id=event_instance_id
            )
            copy_dict_to_struct(p, request.params, [p])
            stopwatch = Processor.started_stopwatch('remote_call')
            try:
                response = await self._stub.Process(
                    request,
                    metadata=[('service-name', self.processor_name)])
            except RpcError as e:
                if e.code() == StatusCode.UNAVAILABLE:
                    raise ProcessingException.from_local_exception(
                        e,
                        self.component_id,
                        "Failed to connect to processor service, check "
                        "that the service is running and the address is "
                        "correctly configured."
                    )
                raise ProcessingException.from_rpc_error(
                    e, self.component_id, self.address
                ) from e
            except Exception as e:
                raise ProcessingException.from_local_exception(
                    e, self.component_id
                ) from e
            stopwatch.stop()
            times = copy.deepcopy(context.times)

        r = {}
        copy_struct_to_dict(response.result, r)

        timing_info = response.timing_info
        for k, v in timing_info.items():
            times[k] = v.ToTimedelta()

        return ComponentResult(self.component_id, r, times)

    def close(self):
        self._channel.close()
