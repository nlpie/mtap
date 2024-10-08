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

import copy
import logging
import sys
from typing import Optional, Dict, Any

import grpc
from grpc import insecure_channel

from mtap import Config
from mtap._event import Event
from mtap._events_client import events_client, EventsAddressLike, EventsClient
from mtap._structs import copy_dict_to_struct, copy_struct_to_dict
from mtap.api.v1 import processing_pb2_grpc, processing_pb2
from mtap.processing._exc import ProcessingException, NotStatusException
from mtap.processing._processing_component import ProcessingComponent
from mtap.processing._processor import Processor, EventProcessor

logger = logging.getLogger('mtap.processing')


class LocalRunner(ProcessingComponent):
    def __init__(self,
                 processor: EventProcessor,
                 events_address: EventsAddressLike,
                 component_id: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None,
                 client: Optional[EventsClient] = None):
        self._processor = processor
        self._events_address = events_address
        self._processor_name = processor.metadata['name']
        self._component_id = component_id or self.processor_name
        self._params = params or {}
        self.metadata = processor.metadata
        self._client = client
        self._client_created = False

    @property
    def processor_name(self) -> str:
        return self._processor_name

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def _events_client(self) -> EventsClient:
        if self._client is None:
            self._client = events_client(self._events_address)
            self._client_created = True
        return self._client

    def call_process(self, event_id, event_instance_id, params):
        p = copy.deepcopy(self._params)
        if params is not None:
            p.update(params)

        with Processor.enter_context() as c:
            event = Event(
                event_id=event_id,
                event_service_instance_id=event_instance_id,
                client=self._events_client,
                label_adapters=self._processor.custom_label_adapters,
                lease=False  # The client / pipeline should hold the lease.
            )
            try:
                with Processor.started_stopwatch('process_method'):
                    result = self._processor.process(event, p)
            except KeyError as e:
                if e == KeyError('document_name'):
                    raise ProcessingException.from_local_exception(
                        *sys.exc_info(), self.component_id,
                        message="This error is likely caused by attempting "
                                "to run an event through a document processor. "
                                "Either call the pipeline with a document or "
                                "set the 'document_name' processor parameter."
                    )
                raise e
            except Exception as e:
                msg = None
                if e == ValueError('Cannot invoke RPC on closed channel!'):
                    msg = "Channel was closed when trying to process."
                raise ProcessingException.from_local_exception(
                    *sys.exc_info(), self.component_id, msg
                )
            return result, c.times, event.created_indices

    def close(self):
        if self._client_created and self._client is not None:
            self._client.close()
            self._client = None


class RemoteRunner(ProcessingComponent):
    def __init__(
            self,
            processor_name,
            component_id,
            address=None,
            params=None,
            enable_proxy=None,
            call_timeout=None,
            channel=None
    ):
        self._processor_name = processor_name
        self._component_id = component_id or processor_name
        self._address = address
        self._params = params or {}
        address = self._address
        config = Config()
        if enable_proxy is not None:
            config['grpc.processor_options.gprc.enable_http_proxy'] = enable_proxy
        if address is None or not isinstance(address, str) or len(address) == 0:
            raise ValueError("address should be a nonnull, nonempty str")
        channel_options = config.get('grpc.processor_options', {})
        self._channel = channel
        if channel is None:
            self._channel = insecure_channel(address, options=list(channel_options.items()))
        self._stub = processing_pb2_grpc.ProcessorStub(self._channel)
        self._call_timeout = call_timeout or 10.0

    @property
    def processor_name(self) -> str:
        return self._processor_name

    @property
    def component_id(self) -> str:
        return self._component_id

    def call_process(self, event_id, event_instance_id, params):
        logger.debug('calling process (%s, %s) on event: (%s, %s)',
                     self.processor_name, self._address, event_id,
                     event_instance_id)
        p = copy.deepcopy(self._params)
        if params is not None:
            p.update(params)

        with Processor.enter_context() as context:
            request = processing_pb2.ProcessRequest(
                processor_id=self.processor_name,
                event_id=event_id,
                event_service_instance_id=event_instance_id
            )
            copy_dict_to_struct(p, request.params, [p])
            with Processor.started_stopwatch('remote_call'):
                try:
                    response = self._stub.Process(
                        request,
                        timeout=self._call_timeout,
                        metadata=[('service-name', self.processor_name)])
                except grpc.RpcError as rpc_error:
                    exc_info = sys.exc_info()
                    try:
                        raise ProcessingException.from_rpc_error(
                            rpc_error, self.component_id, self._address
                        )
                    except NotStatusException:
                        msg = None
                        if rpc_error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                            msg = f'Deadline exceeded waiting for "{self.processor_name}" to process an event.'
                        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
                            msg = f'Failed to connect to "{self.processor_name}", check '
                            "that the service is running and the address is "
                            "correctly configured."
                        raise ProcessingException.from_local_exception(
                            *exc_info, self.component_id, self._address, msg
                        )
                except Exception as e:
                    msg = None
                    if e == ValueError('Cannot invoke RPC on closed channel!'):
                        msg = "Channel was closed when trying to process."
                    raise ProcessingException.from_local_exception(
                        *sys.exc_info(), self.component_id, self._address, msg
                    )

            r = {}
            copy_struct_to_dict(response.result, r)

            timing_info = response.timing_info
            for k, v in timing_info.items():
                context.add_time(k, v.ToTimedelta())

            created_indices = {}
            for created_index in response.created_indices:
                try:
                    doc_created_indices = created_indices[
                        created_index.document_name]
                except KeyError:
                    doc_created_indices = []
                    created_indices[
                        created_index.document_name] = doc_created_indices
                doc_created_indices.append(created_index.index_name)

            return r, context.times, created_indices

    def close(self):
        self._channel.close()
