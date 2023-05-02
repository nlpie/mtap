# Copyright 2023 Regents of the University of Minnesota.
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
import asyncio
import atexit
import logging
import traceback
from concurrent.futures import Executor
from contextvars import ContextVar
from typing import NamedTuple

from grpc_status import rpc_status

from mtap._event import Event
from mtap._events_client import EventsClient, events_client, EventsAddressLike
from mtap._structs import copy_dict_to_struct, copy_struct_to_dict
from mtap.api.v1 import processing_pb2_grpc, processing_pb2
from mtap.processing import ProcessingException, Processor
from mtap.processing._processor import EventProcessor
from mtap.processing.results import create_timer_stats, add_times

logger = logging.getLogger('mtap.processing')


class ProcessorLocal(NamedTuple):
    processor: EventProcessor
    client: EventsClient
    processor_name: str


processor_local: ContextVar[ProcessorLocal] = ContextVar('processor_local')


def init_local(processor: EventProcessor, events_address: EventsAddressLike, processor_name: str):
    client = events_client(events_address)
    local = ProcessorLocal(processor, client, processor_name)
    processor_local.set(local)
    atexit.register(processor.close)
    atexit.register(client.close)


def do_process(request):
    processor, client, processor_name = processor_local.get()

    event_id = request.event_id
    event_service_instance_id = request.event_service_instance_id
    params = {}
    copy_struct_to_dict(request.params, params)

    with Processor.enter_context() as c, \
            Event(
                event_id=event_id,
                event_service_instance_id=event_service_instance_id,
                client=client,
                label_adapters=processor.custom_label_adapters
            ) as event:
        with Processor.started_stopwatch('process_method'):
            try:
                result = processor.process(event, params)
            except KeyError as e:
                if e.args[0] == 'document_name':
                    raise ProcessingException.from_local_exception(
                        e, processor_name,
                        "This error is likely caused by attempting "
                        "to run an event through a document processor. "
                        "Either call the pipeline with a document or "
                        "set the 'document_name' processor parameter."
                    ) from e
                raise e
            except Exception as e:
                raise ProcessingException.from_local_exception(
                    e, processor_name
                ) from e

        response = processing_pb2.ProcessResponse()
        times = dict(c.times)
        for k, l in times.items():
            response.timing_info[k].FromTimedelta(l)

        for document_name, l in event.created_indices.items():
            for index_name in l:
                created_index = response.created_indices.add()
                created_index.document_name = document_name
                created_index.index_name = index_name

    if result is not None:
        copy_dict_to_struct(result, response.result, [])
    return response, times


class ProcessorServicer(processing_pb2_grpc.ProcessorServicer):
    def __init__(self, processor_name: str, sid: str, metadata: dict, executor: Executor):
        self.processor_name = processor_name
        self.sid = sid

        self.executor = executor

        self.times_map = {}
        self.processed = 0
        self.failure_count = 0

        self.get_info_response = processing_pb2.GetInfoResponse()
        copy_dict_to_struct(metadata, self.get_info_response.metadata)

    async def Process(self, request, context=None):
        event_id = request.event_id
        event_service_instance_id = request.event_service_instance_id
        logger.debug(
            '%s received process request on event: (%s, %s)',
            self.processor_name, event_id, event_service_instance_id)
        self.processed += 1
        try:
            loop = asyncio.get_event_loop()
            response, times = await loop.run_in_executor(self.executor, do_process, request)
            add_times(self.times_map, times)
            return response
        except ProcessingException as e:
            self.failure_count += 1
            logger.error(str(e))
            logger.error(traceback.format_exc())
            context.abort_with_status(rpc_status.to_status(e.to_rpc_status()))

    async def GetStats(self, request, context):
        r = processing_pb2.GetStatsResponse(processed=self.processed,
                                            failures=self.failure_count)
        tsd = create_timer_stats(self.times_map, self.processor_name)
        for k, v in tsd.items():
            ts = r.timing_stats[k]
            ts.mean.FromTimedelta(v.mean)
            ts.std.FromTimedelta(v.std)
            ts.max.FromTimedelta(v.max)
            ts.min.FromTimedelta(v.min)
            ts.sum.FromTimedelta(v.sum)
        return r

    async def GetInfo(self, request, context):
        return self.get_info_response
