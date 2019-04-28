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
from abc import ABCMeta, abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import List, Union, ContextManager, Any, Dict, NamedTuple, Optional

import grpc
import math
from grpc_health.v1 import health, health_pb2_grpc

from . import _utils, _discovery, events
from ._config import Config
from .api.v1 import processing_pb2_grpc, processing_pb2
from .events import Event, Document, Events

_logger = logging.getLogger(__name__)

_processors = {}  # processors registry
_processor_local = threading.local()  # processor context thread local

__all__ = [
    'ProcessorContext',
    'processor',
    'EventProcessor',
    'DocumentProcessor',
    'ProcessingResult',
    'TimerStats',
    'AggregateTimingInfo',
    'Pipeline',
    'ProcessorServer',
]


class ProcessorContext:
    """A processing context which gets passed to processors."""
    def __init__(self, processor_id, health_servicer, args: List[str]):
        self._processor_id = processor_id
        self._health_servicer = health_servicer
        self._args = args

    def update_serving_status(self, status: str):
        """Updates the serving status of the processor for health checking.

        Parameters
        ----------
        status: str
            One of "SERVING", "NOT_SERVING", "UNKNOWN".

        """
        self._health_servicer.set(self._processor_id, status)

    def stopwatch(self, key: str) -> ContextManager:
        """An object that can be used to time aspects of processing.

        Parameters
        ----------
        key: str
            The key to store the time under

        Returns
        -------
        ContextManager
            A context manager object that is used to do the timing.

        Examples
        --------
        >>> # In a process method
        >>> with context.stopwatch('something'):
        >>>     # do work
        >>>

        """
        return _processor_local.context.stopwatch(key)

    def args(self) -> List[str]:
        """Additional arguments from startup.

        Returns
        -------
        list
            List of string arguments.

        """
        return self._args


def processor(name: str):
    """Decorator which attaches a service name to a processor for launching with the nlpnewt command
    line


    Parameters
    ----------
    name: str
        Identifying service name both for launching via command line and for service registration.

        Should be a mix of alphanumeric characters and dashes so that they play nice with the DNS
        name requirements of stuff like Consul.

        This can be modified for service registration at runtime by overriding
        :func:'Processor.registration_processor_name'.

    Returns
    -------
    decorator
        This decorator should be applied to a 0-arg or 1-arg functions.

    Examples
    --------
    >>> @processor('example-text-converter')
    >>> class TextConverter(EventProcessor):
    >>>     def __init__(self):
    >>>         # not necessary to have arguments parameter.

    or

    >>> @processor('example-sentence-detector')
    >>> class SentenceDetector(DocumentProcessor):
    >>>     def __init__(self, processor_context):
    >>>         # parse and use args

    These are all valid ways of registering processors.

    """
    def decorator(func):
        _processors[name] = func
        return func

    return decorator


class EventProcessor(metaclass=ABCMeta):
    """Abstract base class for an event processor.

    Implementation should either have the default constructor or one which takes a single argument
    of type :obj:`ProcessorContext`.

    Examples
    --------
    >>> class ExampleProcessor(EventProcessor):
    >>>     def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          pass
    >>>


    >>> class ExampleProcessor(EventProcessor):
    >>>     def __init__(self, processor_context: ProcessorContext):
    >>>         self.context = processor_context
    >>>
    >>>     def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          with self.context.stopwatch('key'):
    >>>               # use stopwatch

    """

    @abstractmethod
    def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs processing on an event.

        Parameters
        ----------
        event: Event
            The event object to be processed.
        params: typing.Dict[str, Any]
            Processing parameters. A dictionary of strings mapped to json-serializable values.

        Returns
        -------
        typing.Dict[str, Any], optional
            A dictionary of strings mapped to strings. This likewise may be replaced with a json
            struct at a later point.

        """
        ...

    def close(self):
        """Used for cleaning up anything that needs to be cleaned up.

        """
        pass


class DocumentProcessor(metaclass=ABCMeta):
    """Abstract base class for a document processor.

    Examples
    --------
    >>> class ExampleProcessor(DocumentProcessor):
    >>>     def process(self, document: Document, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          pass
    >>>


    >>> class ExampleProcessor(DocumentProcessor):
    >>>     def __init__(self, processor_context: ProcessorContext):
    >>>         self.context = processor_context
    >>>
    >>>     def process(self, document: Document, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          with self.context.stopwatch('key'):
    >>>               # use stopwatch

    """

    @abstractmethod
    def process(self, document: Document, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Implemented by the subclass, your processor.

        Parameters
        ----------
        document: Document
            The document object to be processed.
        params: typing.Dict[str, Any]
            Processing parameters. A dictionary of strings mapped to json-serializable values.

        Returns
        -------
        typing.Dict[str, Any], optional
            A dictionary of strings mapped to strings. This likewise may be replaced with a json
            struct at a later point.

        """
        ...

    def close(self):
        """Used for cleaning up anything that needs to be cleaned up.

        """
        pass

    def as_processor(self) -> EventProcessor:
        """Adapts this Document processor as event processor by returning an object which has an
        event processing method that retrieves the document name using the 'document_name'
        parameter.

        Returns
        -------

        """
        return _DocumentProcessorAdapter(self)


class ProcessingResult(NamedTuple):
    """The result of processing one document or event."""
    identifier: str
    results: Dict
    timing_info: Dict
    created_indices: Dict[str, List[str]]


ProcessingResult.identifier.__doc__ = "str: The id of the processor with respect to the pipeline."
ProcessingResult.results.__doc__ = "dict[str, typing.Any]: The json object returned by the processor as its results."
ProcessingResult.timing_info.__doc__ = "dict[str, datetime.timedelta]: A dictionary of the times taken processing this document"
ProcessingResult.created_indices.__doc__ = "dict[str, list[str]]: Any indices that have been added to documents by this processor."


class TimerStats(NamedTuple):
    """Statistics about a labeled runtime."""
    mean: timedelta
    std: timedelta
    min: timedelta
    max: timedelta
    sum: timedelta


TimerStats.mean.__doc__ = "datetime.timedelta: The mean duration."
TimerStats.std.__doc__ = "datetime.timedelta: The standard deviation of all times."
TimerStats.max.__doc__ = "datetime.timedelta: The minimum of all times."
TimerStats.min.__doc__ = "datetime.timedelta: The maximum of all times."
TimerStats.sum.__doc__ = "datetime.timedelta: The sum of all times."


class AggregateTimingInfo(NamedTuple):
    """Collection of all of the timing info for a specific processor."""
    identifier: str
    timing_info: Dict[str, TimerStats]

    def print_times(self):
        print(self.identifier)
        print("-------------------------------------")
        for key, stats in self.timing_info.items():
            print(f"  [{key}]\n"
                  f"    mean: {str(stats.mean)}\n"
                  f"    std: {str(stats.std)}\n"
                  f"    min: {str(stats.min)}\n"
                  f"    max: {str(stats.max)}\n"
                  f"    sum: {str(stats.sum)}")
        print("")


AggregateTimingInfo.identifier.__doc__ = "str: The ID of the processor with respect to the pipeline."
AggregateTimingInfo.timing_info.__doc__ = "dict[str, TimerStats]: A map from all of the timer labels to their aggregate values."


class Pipeline:
    """An object which can be used to build and run a pipeline of remote and local processors.

    Examples
    --------
    Remote pipeline with name discovery:

    >>> with nlpnewt.Pipeline() as pipeline, nlpnewt.Events() as events:
    >>>     pipeline.add_processor('processor-1-id')
    >>>     pipeline.add_processor('processor-2-id')
    >>>     pipeline.add_processor('processor-3-id')
    >>>     for txt in txts:
    >>>         with events.open_event() as event:
    >>>             document = event.add_document('plaintext', txt)
    >>>             results = pipeline.run(document)

    Remote pipeline using addresses:

    >>> with nlpnewt.Pipeline() as pipeline, nlpnewt.Events('localhost:50051') as events:
    >>>     pipeline.add_processor('processor-1-name', 'localhost:50052')
    >>>     pipeline.add_processor('processor-2-name', 'localhost:50053')
    >>>     pipeline.add_processor('processor-3-name', 'localhost:50054')
    >>>     for txt in txts:
    >>>         event = events.open_event()
    >>>         document = event.add_document('plaintext', txt)
    >>>         results = pipeline.run(document)

    The statement

    >>> pipeline.run(document)

    with a document parameter is an alias for

    >>> pipeline.run(document.event, params={'document_name': document.document_name})

    The 'document_name' param is used to indicate to :obj:`DocumentProcessor` which document on
    the event to process.

    """

    def __init__(self):
        self._config = Config()
        self._component_ids = {}
        self._components = []

    @property
    def _times_collector(self):
        try:
            return self.__times_collector
        except AttributeError:
            self.__times_collector = _ProcessingTimesCollector()
            return self.__times_collector

    def add_processor(self, name, address=None, *, identifier=None, params=None):
        """Adds a processor in serial to the pipeline.

        Parameters
        ----------
        name: str
            The processor as declared using the :func:`processor` decorator.
        address: str, optional
            Optionally an address to use, will use service discovery configuration to locate
            processors if this is None / omitted.
        identifier: str
            How the processor's results will be identified locally.
        params: dict, optional
            An optional parameter dictionary that will be passed to the processor as parameters
            with every document.

        """
        processor_id = identifier or name
        component_id = _unique_component_id(self._component_ids, processor_id)
        runner = _RemoteRunner(config=self._config,
                               processor_id=processor_id,
                               address=address,
                               component_id=component_id,
                               params=params)
        self._components.append(runner)

    def add_local_processor(self, processor, identifier, events, *, params=None):
        """Adds a processor to the pipeline which will run locally (in the same process as the
        pipeline).

        Parameters
        ----------
        processor: EventProcessor
            The processor instance to run with the pipeline.
        identifier: str
            An identifier for processor in the context of the pipeline.
        events: Events
            The events object that will be used to open copies of the event.
        params: dict, optional
            An optional parameter dictionary that will be passed to the processor as parameters
            with every document.
        """
        identifier = _unique_component_id(self._component_ids, identifier)
        runner = _ProcessorRunner(processor=processor,
                                  events=events,
                                  identifier=identifier,
                                  params=params)
        self._components.append(runner)

    def run(self, target, *, params=None) -> List[ProcessingResult]:
        """Processes the event/document using all of the processors in the pipeline.

        Parameters
        ----------
        target: Event or Document
            Either an event or a document to process.
        params: dict
            Json object containing params specific to processing this event, the existing params
            dictionary defined in :func:`~PipelineBuilder.add_processor` will be updated with
            the contents of this dict.
        Returns
        -------
        list[ProcessingResult]
            The results of all the processors in the pipeline.

        Examples
        --------
        The statement

        >>> pipeline.run(document)

        with a document parameter is an alias for

        >>> pipeline.run(document.event, params={'document_name': document.document_name})

        The 'document_name' param is used to indicate to :obj:`DocumentProcessor` which document on
        the event to process.

        """
        try:
            document_name = target.document_name
            params = dict(params or {})
            params['document_name'] = document_name
            event = target.event
        except AttributeError:
            event = target

        start = datetime.now()
        results = [component.call_process(event.event_id, params) for component in self._components]
        total = datetime.now() - start
        times = {}
        for _, component_times, _ in results:
            times.update(component_times)
        times['pipeline:total'] = total
        self._times_collector.add_times(times)

        for result in results:
            try:
                event.add_created_indices(result[2])
            except AttributeError:
                pass

        return [ProcessingResult(identifier=component.component_id, results=result[0],
                                 timing_info=result[1], created_indices=result[2])
                for component, result in zip(self._components, results)]

    def processor_timer_stats(self) -> List[AggregateTimingInfo]:
        """Returns the aggregated timing infos for all processors individually.

        Returns
        -------
        list[AggregateTimingInfo]
            A list of AggregateTimingInfo objects, one for each processor, in the same order that
            the processors were added to the pipeline.

        """
        timing_infos = []
        for component in self._components:
            component_id = component.component_id
            aggregates = self._times_collector.get_aggregates(component_id + ':')
            aggregates = {k[(len(component_id) + 1):]: v for k, v in aggregates.items()}
            timing_infos.append(
                AggregateTimingInfo(identifier=component_id, timing_info=aggregates))

        return timing_infos

    def pipeline_timer_stats(self) -> AggregateTimingInfo:
        """The aggregated statistics for the runtime of the pipeline on the whole.

        Returns
        -------
        AggregateTimingInfo
            The timing stats for the pipeline specfically.

        """
        pipeline_id = 'pipeline:'
        aggregates = self.__times_collector.get_aggregates(pipeline_id)
        aggregates = {k[len(pipeline_id):]: v for k, v in aggregates.items()}
        return AggregateTimingInfo(identifier='pipeline', timing_info=aggregates)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Closes any open connections to remote processors.
        """
        for component in self._components:
            try:
                component.close()
            except AttributeError:
                pass

    def as_processor(self) -> EventProcessor:
        """Returns the pipeline as a processor.

        Returns
        -------
        EventProcessor
            An event processor that can be added to other pipelines or hosted.

        """
        return _PipelineProcessor(self._components)


class ProcessorServer:
    """Host a NLP-NEWT processor as a service.

    Parameters
    ----------
    processor_name: str
        The name of the processor as regsitered with :func:`processor`.
    address: str
        The address / hostname / IP to host the server on.
    port: int
        The port to host the server on, or 0 to use a random port.
    register: bool, optional
        Whether to register the processor with service discovery.
    events_address: str, optional
        The address of the events server, or omitted / None if the events service should be
        discovered.
    processor_id: str, optional
        The identifier to register the processor under, if omitted the processor name will be used.
    workers: int, optional
        The number of workers that should handle requests.
    params: Dict[str, Any]
        A set of default parameters that will be passed to the processor every time it runs.
    args: List[str]
        Any additional command line arguments that should be passed to the processor on
        instantiation.

    """

    def __init__(self,
                 processor_name: str,
                 address: str,
                 port: int,
                 *,
                 register: bool = False,
                 events_address: str = None,
                 processor_id: str = None,
                 workers: int = None,
                 params: Dict[str, Any] = None,
                 args: List[str] = None):
        self.processor_name = processor_name
        self.address = address
        self._port = port
        self.processor_id = processor_id or processor_name
        self.params = params or {}
        self.events_address = events_address

        self._health_servicer = health.HealthServicer()
        self._servicer = _ProcessorServicer(
            config=Config(),
            processor_name=processor_name,
            address=address,
            health_servicer=self._health_servicer,
            register=register,
            processor_id=processor_id,
            params=params,
            events_address=events_address,
            args=args
        )
        prefix = self.processor_id + "-worker-"
        workers = workers or 10
        thread_pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix=prefix)
        self._server = grpc.server(thread_pool)
        health_pb2_grpc.add_HealthServicer_to_server(self._health_servicer, self._server)
        processing_pb2_grpc.add_ProcessorServicer_to_server(self._servicer, self._server)
        self._port = self._server.add_insecure_port(f"{self.address}:{port}")

    @property
    def port(self) -> int:
        """Returns the port that the server is listening on.

        Returns
        -------
        int
            Bound port.

        """
        return self._port

    def start(self):
        """Starts the service.
        """
        self._server.start()
        self._servicer.start(self.port)
        _logger.info('Started processor server with id: "%s"  on address: "%s:%d"',
                     self.processor_id, self.address, self.port)

    def stop(self, *, grace=None):
        """De-registers (if registered with service discovery) the service and immediately stops
        accepting requests, completely stopping the service after a specified `grace` time.

        During the grace period the server will continue to process existing requests, but it will
        not accept any new requests. This function is idempotent, multiple calls will shutdown
        the server after the soonest grace to expire, calling the shutdown event for all calls to
        this function.

        Parameters
        ----------
        grace: float, optional
            The grace period that the server should continue processing requests for shutdown.

        Returns
        -------
        threading.Event
            A shutdown event for the server.
        """
        self._servicer.shutdown()
        shutdown_event = self._server.stop(grace=grace)
        return shutdown_event


@contextlib.contextmanager
def _enter_context(identifier: str) -> ContextManager['_ProcessorThreadContext']:
    try:
        old_context = _processor_local.context
        identifier = old_context.identifier + '.' + identifier
    except AttributeError:
        old_context = None
    try:
        context = _ProcessorThreadContext(identifier)
        _processor_local.context = context
        yield context
    finally:
        del _processor_local.context
        if old_context is not None:
            _processor_local.context = old_context


class _ProcessorThreadContext:
    def __init__(self, identifier):
        self.times = {}
        self.identifier = identifier

    @contextlib.contextmanager
    def stopwatch(self, key: str) -> ContextManager:
        start = datetime.now()
        try:
            yield
        finally:
            stop = datetime.now()
            duration = stop - start
            self.add_time(key, duration)

    def add_time(self, key, duration):
        self.times[self.identifier + ':' + key] = duration


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
        with _enter_context(self.component_id) as context, self.events.open_event(
                event_id) as event:
            try:
                with context.stopwatch('process_method'):
                    result = self.processor.process(event, p)
                return result, context.times, event.created_indices
            except Exception as e:
                self.failure_count += 1
                raise e

    def close(self):
        self.events.close()
        self.processor.close()


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

        with _enter_context(self.component_id) as context:
            try:
                request = processing_pb2.ProcessRequest(event_id=event_id)
                _utils.copy_dict_to_struct(p, request.params, [p])
                with context.stopwatch('remote_call'):
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


class _PipelineProcessor(EventProcessor):
    def __init__(self, components: List[Union[_ProcessorRunner, _RemoteRunner]]):
        self._components = components

    def process(self,
                event: Event,
                params: Dict[str, Any] = None):
        results = [component.call_process(event.event_id, params) for component in self._components]
        times = {}
        for _, component_times, _ in results:
            times.update(component_times)
        for k, v in times.items():
            _processor_local.context.add_time(k, v)

        return {'component_results': [result[0] for result in results]}

    def close(self):
        for component in self._components:
            try:
                component.close()
            except AttributeError:
                pass


def _unique_component_id(component_ids, component_id):
    count = component_ids.get(component_id, 0)
    count += 1
    component_ids[component_id] = count
    component_id = component_id + '-' + str(count)
    return component_id


class _ProcessorServicer(processing_pb2_grpc.ProcessorServicer):
    def __init__(self,
                 config: Config,
                 processor_name: str,
                 address: str,
                 health_servicer: health.HealthServicer,
                 events_address=None,
                 register: bool = False,
                 processor_id=None,
                 params: Dict[str, Any] = None,
                 args: List[str] = None
                 ):
        self.config = config
        self.processor_name = processor_name
        self.address = address
        self.processor_id = processor_id or processor_name
        self.events_address = events_address
        self.register = register
        self.params = params

        self.health_servicer = health_servicer

        self._context = ProcessorContext(self.processor_id, self.health_servicer, args)
        self._runner = None

        self._times_collector = _ProcessingTimesCollector()

    def start(self, port: int):
        # instantiate processor
        func = _processors.get(self.processor_name)
        try:
            processor = func(self._context)
        except TypeError:
            processor = func()

        if not isinstance(processor, EventProcessor):
            try:
                processor = processor.as_processor()
            except AttributeError:
                raise TypeError('Processor type is not of type EventProcessor '
                                'and does not have as_processor method.')

        # instantiate runner
        events = Events(address=self.events_address)
        self._runner = _ProcessorRunner(processor, events=events, identifier=self.processor_id,
                                        params=self.params)

        self.health_servicer.set(self.processor_id, 'SERVING')

        if self.register:
            from nlpnewt._discovery import Discovery
            service_registration = Discovery(config=self.config)
            self._deregister = service_registration.register_processor_service(
                self.address,
                port,
                self._runner.component_id,
                'v1'
            )

    def shutdown(self):
        self.health_servicer.set(self.processor_id, 'NOT_SERVING')
        try:
            self._deregister()
        except AttributeError:
            pass
        self._runner.close()

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


class _TimerStatsAggregator:
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
        return TimerStats(mean=mean, std=std, max=self._max, min=self._min, sum=self._sum)


class _ProcessingTimesCollector:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1,
                                            thread_name_prefix='processing_times_listener')
        self._times_map = {}

    def _add_times(self, times):
        for k, v in times.items():
            try:
                agg = self._times_map[k]
            except KeyError:
                agg = _TimerStatsAggregator()
                self._times_map[k] = agg
            agg.add_time(v)

    def add_times(self, times):
        self._executor.submit(self._add_times, times)

    def _get_aggregates(self, prefix):
        return {identifier: stats.finalize()
                for identifier, stats in self._times_map.items() if identifier.startswith(prefix)}

    def get_aggregates(self,
                       identifier=None) -> Dict[str, TimerStats]:
        future = self._executor.submit(self._get_aggregates, identifier or '')
        return future.result()

    def shutdown(self):
        self._executor.shutdown(wait=True)


class _DocumentProcessorAdapter(EventProcessor):
    def __init__(self, document_processor: 'DocumentProcessor'):
        self.document_processor = document_processor

    def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calls the subclass's implementation of :func:`process_document` """
        document = event[params['document_name']]
        return self.document_processor.process(document, params)

    def close(self):
        self.document_processor.close()