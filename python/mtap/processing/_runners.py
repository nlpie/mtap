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
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from typing import Optional, Dict, Any, TYPE_CHECKING

import grpc
import math

from mtap import _discovery, _structs
from mtap.api.v1 import processing_pb2, processing_pb2_grpc
from mtap import data
from mtap.processing import _base

if TYPE_CHECKING:
    import mtap
    from mtap import processing

logger = logging.getLogger(__name__)


class ProcessorRunner(_base.ProcessingComponent):
    def __init__(self,
                 proc: 'mtap.EventProcessor',
                 client: 'mtap.EventsClient',
                 identifier: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None):
        self.processor = proc
        self.client = client
        self.component_id = identifier
        self.processed = 0
        self.failure_count = 0
        self.params = params or {}

    def call_process(self, event_id, params):
        self.processed += 1
        p = dict(self.params)
        if params is not None:
            p.update(params)
        with _base.Processor.enter_context() as c, \
                data.Event(event_id=event_id, client=self.client) as event:
            try:
                with _base.Processor.started_stopwatch('process_method') as stopwatch:
                    stopwatch.start()
                    result = self.processor.process(event, p)
                return result, c.times, event.created_indices
            except Exception as e:
                self.failure_count += 1
                logger.error('Processor "%s" failed while processing event with id: %s',
                             self.component_id, event_id, exc_info=1)
                raise _base.ProcessingError() from e

    def close(self):
        self.processor.close()


class RemoteRunner(_base.ProcessingComponent):
    def __init__(self, config, processor_id, component_id, address=None, params=None,
                 enable_proxy=False):
        self._processor_id = processor_id
        self.component_id = component_id
        self._address = address
        self._params = params
        self.processed = 0
        self.failure_count = 0
        self.params = params
        address = self._address
        if address is None:
            discovery = _discovery.Discovery(config)
            address = discovery.discover_processor_service(processor_id, 'v1')
        enable_proxy = enable_proxy or config.get('grpc.enable_proxy', False)
        self._channel = grpc.insecure_channel(address,
                                              [("grpc.lb_policy_name", "round_robin"),
                                               ("grpc.enable_http_proxy", enable_proxy)])
        self._stub = processing_pb2_grpc.ProcessorStub(self._channel)

    def call_process(self, event_id, params):
        self.processed += 1
        p = dict(self.params or {})
        if params is not None:
            p.update(params)

        with _base.Processor.enter_context() as context:
            request = processing_pb2.ProcessRequest(processor_id=self._processor_id,
                                                    event_id=event_id)
            _structs.copy_dict_to_struct(p, request.params, [p])
            with _base.Processor.started_stopwatch('remote_call'):
                try:
                    response = self._stub.Process(request)
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.CANCELLED:
                        logger.error('event_id: %s CANCELLED', event_id)
                    else:
                        self.failure_count += 1
                        logger.error('Processor "%s" failed while processing event with id: %s',
                                     self.component_id, event_id, exc_info=1)
                    raise _base.ProcessingError() from e
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


class TimerStatsAggregator:
    def __init__(self):
        self._count = 0
        self._min = timedelta.max
        self._max = timedelta.min
        self._mean = 0.0
        self._sse = 0.0
        self._sum = timedelta(seconds=0)

    def add_time(self, time):
        if time < self._min:
            self._min = time
        if time > self._max:
            self._max = time

        self._count += 1
        self._sum += time
        time = time.total_seconds()
        delta = time - self._mean
        self._mean += delta / self._count
        delta2 = time - self._mean
        self._sse += delta * delta2

    def finalize(self):
        mean = timedelta(seconds=self._mean)
        variance = self._sse / self._count
        std = math.sqrt(variance)
        std = timedelta(seconds=std)
        return _base.TimerStats(mean=mean, std=std, max=self._max, min=self._min, sum=self._sum)


class ProcessingTimesCollector:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._times_map = {}

    def _add_times(self, times):
        for k, v in times.items():
            try:
                agg = self._times_map[k]
            except KeyError:
                agg = TimerStatsAggregator()
                self._times_map[k] = agg
            agg.add_time(v)

    def add_times(self, times):
        self._executor.submit(self._add_times, times)

    def _get_aggregates(self, prefix):
        return {identifier: stats.finalize()
                for identifier, stats in self._times_map.items() if identifier.startswith(prefix)}

    def get_aggregates(self,
                       identifier=None) -> Dict[str, 'processing.TimerStats']:
        future = self._executor.submit(self._get_aggregates, identifier or '')
        return future.result()

    def close(self):
        self._executor.shutdown()
