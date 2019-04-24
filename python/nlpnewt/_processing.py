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
"""Internal processors and pipelines functionality."""

import contextlib
import logging
import threading
import typing as _typing
from concurrent import futures
from datetime import datetime

import grpc

from . import _utils, _discovery, _events_client, base
from .base import Event, ProcessingResult, AggregateTimingInfo
from .api.v1 import processing_pb2_grpc, processing_pb2, health_pb2_grpc, health_pb2

_processor_local = threading.local()
_processors = {}  # processors registry

_logger = logging.getLogger(__name__)


@contextlib.contextmanager
def stopwatch(key):
    start = datetime.now()
    try:
        yield
    finally:
        stop = datetime.now()
        _processor_local.context.add_time(key, stop - start)


def register_processor(name, func):
    _processors[name] = func


class _ProcessorContext:
    def __init__(self):
        self.times = {}
        self._scope = []

    @property
    def identifier(self):
        return ".".join(self._scope)

    @contextlib.contextmanager
    def enter(self, identifier):
        old_times = self.times
        self.times = {}
        self._scope.append(identifier)
        try:
            yield self
        finally:
            self.times = old_times
            self._scope.pop()

    def add_time(self, key, delta):
        self.times[self.identifier + ':' + key] = delta


class _ProcessorRunner:
    def __init__(self, processor, events, identifier=None, params=None):
        self.processor = processor
        self.events = events
        self.component_id = identifier
        self.processed = 0
        self.failure_count = 0
        self.params = params or {}

    def call_process(self, event_id, params):
        self.processed += 1
        p = dict(self.params)
        p.update(params)
        try:
            context = _processor_local.context
        except AttributeError:
            _processor_local.context = _ProcessorContext()
            context = _processor_local.context

        with context.enter(self.component_id), self.events.open_event(event_id) as event:
            try:
                with stopwatch('process_method'):
                    result = self.processor.process(event, p)

                return result, context.times, event.created_indices
            except Exception as e:
                self.failure_count += 1
                raise e

    def close(self):
        self.events.close()
        self.processor.close()


class _ProcessorServicer(processing_pb2_grpc.ProcessorServicer, health_pb2_grpc.HealthServicer):
    def __init__(self, runner: _ProcessorRunner):
        self._runner = runner
        self._times_collector = _utils.ProcessingTimesCollector()

    @property
    def processor_name(self):
        return self._runner

    def Process(self, request, context=None):
        params = {}
        _utils.copy_struct_to_dict(request.params, params)
        try:
            response = processing_pb2.ProcessResponse()
            result, times, added_indices = self._runner.call_process(request.event_id, params)
            if result is not None:
                _utils.copy_dict_to_struct(result, response.result, [])

            self._times_collector.add_times(times)
            for k, l in times.items():
                response.timing_info[k].FromTimedelta(l)
            for document_name, l in added_indices.items():
                for index_name in l:
                    created_index = response.created_indices.add()
                    created_index.document_name = document_name
                    created_index.index_name = index_name
            return response
        except Exception as e:
            try:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
            except AttributeError:
                pass
            raise e

    def GetStats(self, request, context):
        r = processing_pb2.GetStatsResponse(processed=self._runner.processed,
                                            failures=self._runner.failure_count)
        for k, v in self._times_collector.get_aggregates(self._runner.component_id).items():
            ts = r.timing_stats[k]
            ts.mean.FromTimedelta(v.mean)
            ts.std.FromTimedelta(v.std)
            ts.max.FromTimedelta(v.max)
            ts.min.FromTimedelta(v.min)
            ts.sum.FromTimedelta(v.sum)
        return r

    def GetInfo(self, request, context):
        return processing_pb2.GetInfoResponse(name=self.processor_name)

    def Check(self, request, context):
        if request.service is None or request.service == '':
            return health_pb2.HealthCheckResponse(status='SERVING')
        elif request.service == self._runner.component_id:
            return health_pb2.HealthCheckResponse(status=self._runner.processor.status)
        else:
            return health_pb2.HealthCheckResponse(status='NOT_SERVING')


class _ProcessorServer(base.Server):
    def __init__(self, config, thread_pool, address, port, runner):
        server = grpc.server(thread_pool)
        servicer = _ProcessorServicer(runner)
        processing_pb2_grpc.add_ProcessorServicer_to_server(servicer, server)
        health_pb2_grpc.add_HealthServicer_to_server(servicer, server)
        self._port = server.add_insecure_port(f'{address}:{port}')
        self._server = server
        self._config = config
        self._address = address
        self._runner = runner

    @property
    def port(self) -> int:
        return self._port

    def start(self, *, register: bool):
        _logger.info("Starting processor server identifier: %s address: %s port: %d",
                     self._runner.component_id, self._address, self._port)
        self._server.start()
        if register:
            from nlpnewt._discovery import Discovery
            service_registration = Discovery(config=self._config)
            self._deregister = service_registration.register_processor_service(self._address,
                                                                               self._port,
                                                                               self._runner.component_id,
                                                                               'v1')

    def stop(self, *, grace=None):
        try:
            self._deregister()
        except AttributeError:
            pass
        shutdown_event = self._server.stop(grace=grace)
        return shutdown_event


class _RemoteRunner:
    def __init__(self, config, processor_id, component_id, address=None, params=None):
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
        self._channel = grpc.insecure_channel(address)
        self._stub = processing_pb2_grpc.ProcessorStub(self._channel)

    def call_process(self, event_id, params):
        self.processed += 1
        p = dict(self.params or {})
        p.update(params)
        try:
            context = _processor_local.context
        except AttributeError:
            _processor_local.context = _ProcessorContext()
            context = _processor_local.context

        with context.enter(self.component_id):
            try:
                request = processing_pb2.ProcessRequest(event_id=event_id)
                _utils.copy_dict_to_struct(p, request.params, [p])
                with stopwatch('remote_call'):
                    response = self._stub.Process(request)
                r = {}
                _utils.copy_struct_to_dict(response.result, r)

                timing_info = response.timing_info
                for k, v in timing_info.items():
                    context.add_time(k, v.ToTimedelta())

                created_indices = {}
                for created_index in response.created_indices:
                    try:
                        l = created_indices[created_index.document_name]
                    except KeyError:
                        l = []
                        created_indices[created_index.document_name] = l
                    l.append(created_index.index_name)

                return r, context.times, created_indices
            except Exception as e:
                self.failure_count += 1
                raise e

    def close(self):
        self._channel.close()


class _Pipeline(base.Pipeline, base.DocumentProcessor):
    def __init__(self, config):
        self._config = config
        self.ids = {}
        self._components = []

    @property
    def times_collector(self):
        try:
            return self._times_collector
        except AttributeError:
            self._times_collector = _utils.ProcessingTimesCollector()
            return self._times_collector

    def add_processor(self, processor_identifier, address=None, *, component_id=None, params=None):
        component_id = component_id or processor_identifier
        count = self.ids.get(component_id, 0)
        count += 1
        self.ids[component_id] = count
        component_id = component_id + '-' + str(count)
        runner = _RemoteRunner(config=self._config,
                               processor_id=processor_identifier,
                               address=address,
                               component_id=component_id,
                               params=params)
        self._components.append(runner)

    def add_local_processor(self, processor, identifier, events, *, params=None):
        runner = _ProcessorRunner(processor=processor,
                                  events=events,
                                  identifier=identifier,
                                  params=params)
        self._components.append(runner)

    def run(self, target, *, params=None):
        try:
            document_name = target.document_name
            params = dict(params or {})
            params['document_name'] = document_name
            event = target.event
        except AttributeError:
            event = target

        start = datetime.now()
        results = [component.call_process(event, params) for component in self._components]
        total = datetime.now() - start
        times = {}
        for _, component_times in results:
            times.update(component_times)
        times['pipeline:total'] = total
        self.times_collector.add_times(times)

        for result in results:
            event.add_created_indices(result[2])

        return [ProcessingResult(identifier=component.component_id, results=result[0],
                                 timing_info=result[1], created_indices=result[2])
                for component, result in zip(self._components, results)]

    def process(self,
                event: Event,
                params: _typing.Dict[str, str] = None):
        results = self.call_process_components(event, params)
        return {'component_results': results}

    def process_document(self, document, params=None):
        event = document.event
        params = params or {}
        params['document_name'] = document.document_name
        results = self.call_process_components(event, params)
        return {'component_results': results}

    def call_process_components(self, event, params):
        results = [component.call_process(event, params) for component in self._components]
        times = {}
        for _, component_times in results:
            times.update(component_times)
        for k, v in times.items():
            _processor_local.context.add_time(k, v)
        return [result[0] for result in results]

    def processor_timer_stats(self) -> _typing.List[AggregateTimingInfo]:
        l = []
        for component in self._components:
            component_id = component.component_id
            aggregates = self._times_collector.get_aggregates(component_id + ':')
            aggregates = {k[(len(component_id) + 1):]: v for k, v in aggregates.items()}
            l.append(AggregateTimingInfo(identifier=component_id, timing_info=aggregates))

        return l

    def pipeline_timer_stats(self) -> AggregateTimingInfo:
        pipeline_id = 'pipeline:'
        aggregates = self._times_collector.get_aggregates(pipeline_id)
        aggregates = {k[len(pipeline_id):]: v for k, v in aggregates.items()}
        return AggregateTimingInfo(identifier='pipeline', timing_info=aggregates)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        for component in self._components:
            try:
                component.close()
            except AttributeError:
                pass


def create_pipeline(config):
    return _Pipeline(config)


def create_runner(config,
                  events_address,
                  processor_name,
                  identifier=None,
                  params=None,
                  processor_args=None,
                  processor_kwargs=None):
    func = _processors.get(processor_name)
    has_processor_args = processor_args is None or len(processor_args) == 0
    has_processor_kwargs = processor_kwargs is None or len(processor_kwargs) == 0
    if has_processor_args and has_processor_kwargs:
        processor = func()
    else:
        processor = func(*processor_args, **processor_kwargs)
    identifier = identifier or processor_name
    events = _events_client.get_events(config, address=events_address)
    runner = _ProcessorRunner(processor, events=events, identifier=identifier, params=params)
    return runner


def create_server(*,
                  config,
                  address,
                  port,
                  runner,
                  workers=10):
    prefix = runner.component_id + "-"
    return _ProcessorServer(config,
                            futures.ThreadPoolExecutor(max_workers=workers,
                                                       thread_name_prefix=prefix),
                            address,
                            port,
                            runner=runner)
