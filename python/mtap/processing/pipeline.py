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
from abc import ABC, abstractmethod
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Lock, Condition
from typing import Optional, Dict, Any, Union, List, MutableSequence, Iterable, Callable, \
    NamedTuple, ContextManager

from tqdm import tqdm

from mtap._config import Config
from mtap.events import Event, Document, EventsClient
from mtap.processing._runners import ProcessorRunner, RemoteRunner, ProcessingTimesCollector, \
    ProcessingComponent, ProcessingError
from mtap.processing.base import EventProcessor, ProcessingResult, AggregateTimingInfo

logger = logging.getLogger(__name__)


class ComponentDescriptor(ABC):
    """A component descriptor describes either a local or remote pipeline component and what the
    pipeline needs to do to call the component.
    """

    @abstractmethod
    def create_pipeline_component(self, config: Config,
                                  component_ids: Dict[str, int]) -> ProcessingComponent:
        pass


class RemoteProcessor(ComponentDescriptor):
    """A ``ComponentDescriptor`` for a remote processor that the pipeline will connect to in order
    to perform processing.

    Args:
        processor_id (str): The identifier used for health checking and discovery.

    Keyword Args:
        address (~typing.Optional[str]):
            Optionally an address to use, will use service discovery configuration to locate
            processors if this is None / omitted.
        component_id (~typing.Optional[str]):
            How the processor's results will be identified locally. Will be modified to be unique
            if it is not unique relative to other component in a pipeline.
        params (~typing.Optional[dict, Any]):
            An optional parameter dictionary that will be passed to the processor as parameters
            with every event or document processed. Values should be json-serializable.

    Attributes:
        processor_id (str): The identifier used for health checking and discovery.
        address (~typing.Optional[str]):
            Optionally an address to use, will use service discovery configuration to locate
            processors if this is None / omitted.
        component_id (~typing.Optional[str]):
            How the processor's results will be identified locally. Will be modified to be unique
            if it is not unique relative to other component in a pipeline.
        params (~typing.Optional[dict, Any]):
            An optional parameter dictionary that will be passed to the processor as parameters
            with every event or document processed. Values should be json-serializable.
    """

    def __init__(self, processor_id: str, *, address: Optional[str] = None,
                 component_id: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        self.processor_id = processor_id
        self.address = address
        self.component_id = component_id
        self.params = params

    def create_pipeline_component(self, config: Config,
                                  component_ids: Dict[str, int]) -> ProcessingComponent:
        component_id = self.component_id or self.processor_id
        component_id = _unique_component_id(component_ids, component_id)
        runner = RemoteRunner(config=config, processor_id=self.processor_id, address=self.address,
                              component_id=component_id, params=self.params)
        runner.descriptor = self
        return runner

    def __repr__(self):
        return "RemoteProcessor(processor_id={}, address={}, component_id={}, params={})".format(
            *map(repr, [self.processor_id, self.address, self.component_id, self.params])
        )


class LocalProcessor(ComponentDescriptor):
    """A ``ComponentDescriptor`` for a locally-invoked processor.

    Args:
        proc (EventProcessor): The processor instance to run with the pipeline.

    Keyword Args:
        component_id (str):
            How the processor's results will be identified locally. Will be modified to be unique
            if it is not unique relative to other component in a pipeline.
        client (EventsClient):
            The client used by the local processor to connect to an events service to retrieve
            events and documents. Required because pipeline components are all called using
            identifiers and not concrete objects.
        params (~typing.Optional[dict, Any]):
            An optional parameter dictionary that will be passed to the processor as parameters
            with every event or document processed. Values should be json-serializable.

    Attributes:
        proc (EventProcessor): The processor instance to run with the pipeline.
        component_id (~typing.Optional[str]):
            How the processor's results will be identified locally. Will be modified to be unique
            if it is not unique relative to other component in a pipeline.
        client (EventsClient):
            The client used by the local processor to connect to an events service to retrieve
            events and documents. Required because pipeline components are all called using
            identifiers and not concrete objects.
        params (~typing.Optional[dict, Any]):
            An optional parameter dictionary that will be passed to the processor as parameters
            with every event or document processed. Values should be json-serializable.
    """

    def __init__(self, proc: EventProcessor, *,
                 component_id: str, client: EventsClient,
                 params: Optional[Dict[str, Any]] = None):
        self.proc = proc
        self.component_id = component_id
        self.client = client
        self.params = params

    def create_pipeline_component(self, config: Config,
                                  component_ids: Dict[str, int]) -> ProcessingComponent:
        identifier = _unique_component_id(component_ids, self.component_id)
        runner = ProcessorRunner(proc=self.proc, client=self.client, identifier=identifier,
                                 params=self.params)
        runner.descriptor = self
        return runner

    def __repr__(self):
        return 'LocalProcessor(proc={}, component_id={}, client={}, params={}'.format(
            *map(repr, [
                self.proc,
                self.component_id,
                self.client,
                self.params
            ]))


def _event_and_params(target, params):
    try:
        document_name = target.document_name
        params = dict(params or {})
        params['document_name'] = document_name
        event = target.event
    except AttributeError:
        event = target
    return event, params


def _cancel_callback(event, read_ahead, cd, close_events):
    def fn(future: Future):
        if close_events:
            event.close()
        read_ahead.task_completed()
        cd.count_down(future.exception() is not None)

    return fn


class Pipeline(MutableSequence[ComponentDescriptor]):
    """An object which can be used to build and run a pipeline of remote and local processors.

    Pipelines are a :obj:`~typing.MutableSequence` containing
    one or more :obj:`~mtap.processing.pipeline.ComponentDescriptor`,
    a pipeline can be modified after creation using this functionality.

    Args:
        *components (ComponentDescriptor):
            A list of component descriptors created using :class:`RemoteProcessor` or
            :class:`LocalProcessor`.

    Keyword Args:
        name (~typing.Optional[str]): An optional name for the pipeline, defaults to 'pipeline'.
        config (~typing.Optional[Config]): An optional config override.

    Examples:
        Remote pipeline with name discovery:

        >>> with mtap.Events() as events, mtap.Pipeline(
        >>>         RemoteProcessor('processor-1-id'),
        >>>         RemoteProcessor('processor-2-id'),
        >>>         RemoteProcessor('processor-3-id')
        >>>     ) as pipeline:
        >>>     for txt in txts:
        >>>         with events.open_event() as event:
        >>>             document = event.add_document('plaintext', txt)
        >>>             results = pipeline.run(document)

        Remote pipeline using addresses:

        >>> with mtap.Events(address='localhost:50051') as events, mtap.Pipeline(
        >>>         RemoteProcessor('processor-1-name', address='localhost:50052'),
        >>>         RemoteProcessor('processor-2-id', address='localhost:50053'),
        >>>         RemoteProcessor('processor-3-id', address='localhost:50054')
        >>>     ) as pipeline:
        >>>     for txt in txts:
        >>>         event = events.open_event()
        >>>         document = event.add_document('plaintext', txt)
        >>>         results = pipeline.run(document)

        Modifying pipeline

        >>> pipeline = Pipeline(RemoteProcessor('foo', address='localhost:50000'),
                                RemoteProcessor('bar', address='localhost:50000'))
        >>> pipeline
        Pipeline(RemoteProcessor(processor_id='foo', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='bar', address='localhost:50000', component_id=None, params=None))
        >>> pipeline.append(RemoteProcessor('baz', address='localhost:50001'))
        >>> pipeline
        Pipeline(RemoteProcessor(processor_id='foo', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='bar', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='baz', address='localhost:50001', component_id=None, params=None))
        >>> del pipeline[1]
        >>> pipeline
        Pipeline(RemoteProcessor(processor_id='foo', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='baz', address='localhost:50001', component_id=None, params=None))
        >>> pipeline[1] = RemoteProcessor(processor_id='bar', address='localhost:50003')
        >>> pipeline
        Pipeline(RemoteProcessor(processor_id='foo', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='bar', address='localhost:50003', component_id=None, params=None))
        >>> pipeline += list(pipeline)  # Putting in a new list to prevent an infinite recursion
        >>> pipeline
        Pipeline(RemoteProcessor(processor_id='foo', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='bar', address='localhost:50003', component_id=None, params=None),
                 RemoteProcessor(processor_id='foo', address='localhost:50000', component_id=None, params=None),
                 RemoteProcessor(processor_id='bar', address='localhost:50003', component_id=None, params=None))

    Attributes:
        name (str): The pipeline's name.
    """

    def __init__(self, *components: ComponentDescriptor,
                 name: Optional[str] = None,
                 config: Optional[Config] = None):
        self._config = config or Config()
        self._component_ids = {}
        self.name = name or 'pipeline'
        self._components = [desc.create_pipeline_component(self._config, self._component_ids)
                            for desc in components]

    @property
    def _times_collector(self):
        try:
            return self.__times_collector
        except AttributeError:
            self.__times_collector = ProcessingTimesCollector()
            return self.__times_collector

    def run_multithread(self,
                        source: Union[Iterable[Union[Document, Event]], 'ProcessingSource'], *,
                        params: Optional[Dict[str, Any]] = None,
                        progress: bool = True,
                        total: Optional[int] = None,
                        close_events: bool = True,
                        max_failures: int = 0,
                        n_threads: int = 4,
                        read_ahead: int = 1):
        """Runs this pipeline on a source which provides multiple documents / events.

        Concurrency is per-event, with each event being provided a thread which runs it through the
        pipeline.

        Args:
            source (~typing.Union[~typing.Iterable[~typing.Union[Event, Document]], ProcessingSource])
                A generator of events or documents to process.
            params (dict[str, ~typing.Any])
                Json object containing params specific to processing this event, the existing params
                dictionary defined in :func:`~PipelineBuilder.add_processor` will be updated with
                the contents of this dict.
            progress (bool)
                Whether to print a progress bar using tqdm.
            total (~typing.Optional[int])
                An optional argument indicating the total number of events / documents that will be
                provided by the iterable, for the progress bar.
            close_events (bool)
                Whether the pipeline should close events after they have been fully processed
                through all components.
            max_failures (int)
                The number of acceptable failures. Once this amount is exceeded processing will
                halt. Note that because of the nature of conccurrency processing may continue for a
                short amount of time before termination.
            n_threads (int)
                The number of threads to process documents on.
            read_ahead
                The number of source documents to read ahead into memory before processing.

        Returns:
            Future:
                A future which returns a tuple, the a list of ProcessingResult objects for
                all the processors and the event that was processed.

        Examples:
            >>> docs = list(Path('abc/').glob('*.txt'))
            >>> def document_source():
            >>>     for path in docs:
            >>>         with path.open('r') as f:
            >>>             txt = f.read()
            >>>         with Event(event_id=path.name, client=client) as event:
            >>>             doc = event.create_document('plaintext', txt)
            >>>             yield doc
            >>>
            >>> pipeline.run_multithread(document_source(), total=len(docs))

        """
        with _PipelineMultiRunner(self, source, params, progress, total, close_events, max_failures,
                                  n_threads, read_ahead) as runner:
            result = runner.run()
        return result

    def run(self, target: Union[Event, Document], *,
            params: Optional[Dict[str, Any]] = None) -> 'PipelineResult':
        """Processes the event/document using all of the processors in the pipeline.

        Args:
            target (~typing.Union[Event, Document]): Either an event or a document to process.
            params (dict[str, ~typing.Any]):
                Json object containing params specific to processing this event, the existing params
                dictionary defined in :func:`~PipelineBuilder.add_processor` will be updated with
                the contents of this dict.

        Returns:
            list[ProcessingResult]: The results of all the processors in the pipeline.

        Examples:
            The statement

            >>> pipeline.run(document)

            with a document parameter is an alias for

            >>> pipeline.run(document.event, params={'document_name': document.document_name})

            The 'document_name' param is used to indicate to :obj:`~mtap.processing.DocumentProcessor`
            which document on the event to process.
        """
        event, params = _event_and_params(target, params)
        event_id = event.event_id

        result = _run_by_event_id(self, event_id, params)

        for component_result in result.component_results:
            try:
                event.add_created_indices(component_result.created_indices)
            except AttributeError:
                pass
        return result

    def processor_timer_stats(self) -> List[AggregateTimingInfo]:
        """Returns the timing information for all processors.

        Returns:
            list[AggregateTimingInfo]:
                A list of timing info objects, one for each processor, in the same order
                that the processors were added to the pipeline.
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
        """The aggregated statistics for the global runtime of the pipeline.

        Returns:
            AggregateTimingInfo: The timing stats for the global runtime of the pipeline.

        """
        pipeline_id = self.name
        aggregates = self._times_collector.get_aggregates(pipeline_id)
        aggregates = {k[len(pipeline_id):]: v for k, v in aggregates.items()}
        return AggregateTimingInfo(identifier=self.name, timing_info=aggregates)

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

        Returns:
            EventProcessor: An event processor that can be added to other pipelines or hosted.
        """
        return _PipelineProcessor(self._components)

    def print_times(self):
        """Prints all of the times collected during this pipeline using :func:`print`.
        """
        self.pipeline_timer_stats().print_times()
        for pipeline_timer in self.processor_timer_stats():
            pipeline_timer.print_times()

    def __getitem__(self, item):
        if isinstance(item, slice):
            return [x.descriptor for x in self._components[item]]

        return self._components[item].descriptor

    def __setitem__(self, key, value):
        self._components[key].close()
        self._components[key] = value.create_pipeline_component(self._config, self._component_ids)

    def __delitem__(self, key):
        self._components[key].close()
        del self._components[key]

    def __len__(self):
        return len(self._components)

    def insert(self, index, o) -> None:
        self._components.insert(index,
                                o.create_pipeline_component(self._config, self._component_ids))

    def __repr__(self):
        return "Pipeline(" + ', '.join(
            [repr(component.descriptor) for component in self._components]) + ')'


def _run_by_event_id(pipeline, event_id, params):
    start = datetime.now()
    results = [component.call_process(event_id, params) for component in pipeline._components]
    total = datetime.now() - start
    times = {}
    for (_, component_times, _), component in zip(results, pipeline._components):
        times.update({component.component_id + ':' + k: v for k, v in component_times.items()})
    times[pipeline.name + 'total'] = total
    pipeline._times_collector.add_times(times)
    results = [ProcessingResult(identifier=component.component_id, results=result[0],
                                timing_info=result[1], created_indices=result[2]) for
               component, result in zip(pipeline._components, results)]
    logger.debug('Finished processing event_id: %s', event_id)
    return PipelineResult(results, total)


PipelineResult = NamedTuple('PipelineResult',
                            [('component_results', List[ProcessingResult]),
                             ('elapsed_time', timedelta)])
PipelineResult.__doc__ = """The result of processing an event or document in a pipeline.
"""
PipelineResult.component_results.__doc__ = """list[ProcessingResult]: The processing results for 
each individual component"""
PipelineResult.elapsed_time.__doc__ = """datetime.timedelta: The elapsed time for the entire 
pipeline."""


class ProcessingSource(ContextManager, ABC):
    """Provides events or documents for the multi-threaded pipeline runner. Also has functionality
    for receiving results.

    """
    @abstractmethod
    def provide(self, consume: Callable[[Union[Document, Event]], None]):
        """The method which provides documents for the multi-threaded runner. This method provides
        documents or events to the pipeline.

        Args:
            consume (~typing.Callable[~typing.Union[Document, Event]])
                The consumer method to pass documents or events to process.

        Examples:
            Example implementation for processing text documents in a directory.

            >>> ...
            >>> def provide(self, consume: Callable[[Union[Document, Event]], None]):
            >>>     for file in Path(".").glob("*.txt"):
            >>>         with file.open('r') as fio:
            >>>             txt = fio.read()
            >>>         event = Event()
            >>>         doc = event.create_document('plaintext', txt)
            >>>         consume(doc)

        """
        ...

    def receive_result(self, result: PipelineResult, event: Event):
        """Optional method: Asynchronous callback which returns the results of processing. This
        method is called on a processing worker thread. Default behavior is to do nothing.

        Args:
            result (PipelineResult): The result of processing using the pipeline.
            event (Event): The event processed.

        """
        pass

    def receive_failure(self, exc: ProcessingError) -> bool:
        """Optional method: Asynchronous callback which receives exceptions for any failed
        documents.

        Args:
            exc (ProcessingError): The processing exception.

        Returns:
            bool: Whether the error should be suppressed and not count against maximum failures.

        """
        pass

    def close(self):
        """Optional method: called to clean up after processing is complete.

        Returns:

        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return None


class _IterableProcessingSource(ProcessingSource):
    """Wraps an iterable in a ProcessingSource for the multi-thread processor.

    """
    def __init__(self, source):
        self.source = source

    def provide(self, consume: Callable[[Union[Document, Event]], None]):
        for target in self.source:
            consume(target)


class _PipelineProcessor(EventProcessor):
    def __init__(self, components: List[ProcessingComponent]):
        self._components = components

    def process(self,
                event: Event,
                params: Dict[str, Any] = None):
        results = [component.call_process(event.event_id, params) for component in self._components]
        times = {}
        for _, component_times, _ in results:
            times.update(component_times)
        for k, v in times.items():
            _PipelineProcessor.current_context().add_time(k, v)

        return {'component_results': [result[0] for result in results]}


class _PipelineMultiRunner:
    def __init__(self, pipeline, source, params, progress, total, close_events, max_failures,
                 n_threads, read_ahead):
        self.pipeline = pipeline
        self.failures = 0
        self.max_failures = max_failures
        self.targets_cond = Condition(Lock())
        self.active_targets = 0
        self.close_events = close_events
        self.max_targets = n_threads + read_ahead
        self.executor = ThreadPoolExecutor(max_workers=n_threads)
        self.progress_bar = tqdm(total=total, unit='event', smoothing=0.01) if progress else None

        if not isinstance(source, ProcessingSource):
            if not hasattr(source, '__iter__'):
                raise ValueError('The source needs to either be a ProcessingSource or an Iterable.')
            source = _IterableProcessingSource(source)
        self.source = source
        self.params = params

    def max_failures_reached(self):
        return self.failures > self.max_failures

    def increment_active_tasks(self):
        with self.targets_cond:
            self.active_targets += 1

    def task_completed(self):
        with self.targets_cond:
            if self.progress_bar is not None:
                self.progress_bar.update(1)
            self.active_targets -= 1
            self.targets_cond.notify()

    def tasks_done(self):
        return self.active_targets == 0

    def wait_tasks_completed(self):
        with self.targets_cond:
            self.targets_cond.wait_for(self.tasks_done)

    def read_ready(self):
        return self.active_targets < self.max_targets

    def wait_to_read(self):
        with self.targets_cond:
            self.targets_cond.wait_for(self.read_ready)

    def process_task(self, event, params):
        if self.max_failures_reached():
            return
        try:
            result = _run_by_event_id(self.pipeline, event.event_id, params)
            self.source.receive_result(result, event)
        except ProcessingError as e:
            if not self.source.receive_failure(e):
                self.failures += 1
                raise e
        finally:
            self.task_completed()
            if self.close_events:
                event.release_lease()

    def run(self):
        def consume(target):
            if self.max_failures_reached():
                raise ValueError('Max processing failures exceeded.')
            event, params = _event_and_params(target, self.params)
            try:
                event.lease()
                self.increment_active_tasks()
                self.executor.submit(self.process_task, event, params)
            except BaseException as e:
                # here we failed sometime between taking a new lease and adding the done
                # callback to the future, meaning the lease will never get freed.
                event.release_lease()
                raise e
            self.wait_to_read()

        with self.source:
            self.source.provide(consume)
        self.wait_tasks_completed()
        if self.max_failures_reached():
            raise ValueError('Max processing failures exceeded.')


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.executor.shutdown(wait=True)


def _unique_component_id(component_ids, component_id):
    count = component_ids.get(component_id, 0)
    count += 1
    component_ids[component_id] = count
    component_id = component_id + '-' + str(count)
    return component_id
