#  Copyright 2021 Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import multiprocessing
import pathlib
import signal
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import Future
from datetime import datetime
from threading import Lock, Condition
from typing import Optional, Dict, Any, Union, List, MutableSequence, Iterable, Callable, \
    ContextManager, TYPE_CHECKING, overload

from tqdm import tqdm

from mtap import EventsClient, Config
from mtap.data import Event
from mtap.processing import _base, _runners, _timing

if TYPE_CHECKING:
    import mtap
    from mtap import processing

logger = logging.getLogger(__name__)


class RemoteProcessor(_base.ComponentDescriptor):
    """A configuration for a remote processor that the pipeline will connect to in order
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
    __slots__ = ('processor_id', 'address', 'component_id', 'params', 'enable_proxy')

    def __init__(self, processor_id: str, *, address: Optional[str] = None,
                 component_id: Optional[str] = None, params: Optional[Dict[str, Any]] = None,
                 enable_proxy: bool = False):
        self.processor_id = processor_id
        self.address = address
        self.component_id = component_id
        self.params = params
        self.enable_proxy = enable_proxy

    def create_pipeline_component(
            self,
            component_ids: Dict[str, int],
            client: 'mtap.EventsClient'
    ) -> 'processing.ProcessingComponent':
        component_id = self.component_id or self.processor_id
        component_id = _unique_component_id(component_ids, component_id)
        runner = _runners.RemoteRunner(processor_id=self.processor_id,
                                       address=self.address, component_id=component_id,
                                       params=self.params, enable_proxy=self.enable_proxy)
        return runner

    def __repr__(self):
        return "RemoteProcessor(processor_id={}, address={}, component_id={}, params={})".format(
            *map(repr, [self.processor_id, self.address, self.component_id, self.params])
        )


class LocalProcessor(_base.ComponentDescriptor):
    """A configuration of a locally-invoked processor.

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
    __slots__ = ('proc', 'component_id', 'params')

    def __init__(self, proc: 'mtap.EventProcessor',
                 *, component_id: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None):
        self.proc = proc
        self.component_id = component_id or proc.metadata['name']
        self.params = params

    def create_pipeline_component(
            self,
            component_ids: Dict[str, int],
            client: 'Callable[[], mtap.EventsClient]'
    ) -> 'processing.ProcessingComponent':
        identifier = _unique_component_id(component_ids, self.component_id)
        runner = _runners.ProcessorRunner(proc=self.proc,
                                          identifier=identifier,
                                          params=self.params,
                                          client=client())
        return runner

    def __repr__(self):
        return 'LocalProcessor(proc={}, component_id={}, params={}'.format(
            *map(repr, [
                self.proc,
                self.component_id,
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


def _create_pipeline(name: Optional[str] = None,
                     events_address: Optional[str] = None,
                     events_client: Optional[EventsClient] = None,
                     mp_config: 'Optional[MpConfig]' = None,
                     *components: 'processing.ComponentDescriptor'):
    return Pipeline(*components, name=name, events_address=events_address,
                    events_client=events_client, mp_config=mp_config)


class MpConfig:
    """Configuration object for pipeline multiprocessing.

    Args:
        max_failures (~typing.Optional[int])
            Override for maximum number of failures before cancelling the pipeline run. Default is
            0.
        show_progress (~typing.Optional[bool])
            Override for whether progress should be displayed in console. Default is true.
        workers (~typing.Optional[int])
            Number of workers to concurrently process events through the pipeline. Default is 4.
        read_ahead (~typing.Optional[int])
            The number of documents to read onto the events service(s) to queue for processing.
            Default is equal to number of workers.
        close_events (~typing.Optional[bool])
            Whether any events passed from the source to the pipeline should be closed when the
            pipeline is completed. Default is true.
        mp_start_method (~typing.Optional[str])
            The start method for multiprocessing processes see: :meth:`multiprocessing.get_context`.
    """
    __slots__ = ("max_failures", "show_progress", "workers", "read_ahead", "close_events",
                 "mp_start_method")

    def __init__(self,
                 max_failures: Optional[int] = None,
                 show_progress: Optional[bool] = None,
                 workers: Optional[int] = None,
                 read_ahead: Optional[int] = None,
                 close_events: Optional[bool] = None,
                 mp_start_method: Optional[str] = None):
        self.max_failures = 0 if max_failures is None else max_failures
        if not type(self.max_failures) == int or self.max_failures < 0:
            raise ValueError("max_failures must be None or non-negative integer")
        self.show_progress = True if show_progress is None else show_progress
        if not type(self.show_progress) == bool:
            raise ValueError("show_progress must be boolean.")
        self.workers = 4 if workers is None else workers
        if not type(self.workers) == int or self.workers <= 0:
            raise ValueError("workers must be None or positive integer.")
        self.read_ahead = self.workers if read_ahead is None else read_ahead
        if not type(self.read_ahead) == int or self.read_ahead < 0:
            raise ValueError("read_ahead must be None or a non-negative integer")
        self.close_events = True if close_events is None else close_events
        if not type(self.close_events) == bool:
            raise ValueError("close_events must be None or a bool.")
        self.mp_start_method = "spawn" if mp_start_method is None else mp_start_method

    @staticmethod
    def from_configuration(conf: Dict) -> 'MpConfig':
        return MpConfig(**conf)


class Pipeline(MutableSequence['processing.ComponentDescriptor']):
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
    __slots__ = ['_component_ids', 'name', '_component_descriptors', 'events_address',
                 'mp_config', '_created_events_client', '_provided_events_client', 'times_map',
                 '__components', '_events_client']

    def __init__(self, *components: 'processing.ComponentDescriptor',
                 name: Optional[str] = None,
                 events_address: Optional[str] = None,
                 events_client: Optional[EventsClient] = None,
                 mp_config: Optional[MpConfig] = None):
        self._component_ids = {}
        self.name = name or 'pipeline'
        self._component_descriptors = list(components)
        self.events_address = events_address
        self._created_events_client = False
        self._provided_events_client = events_client
        self._events_client = events_client
        self.mp_config = mp_config or MpConfig()
        self.times_map = {}

    def __reduce__(self):
        return _create_pipeline, (self.name,
                                  self.events_address,
                                  self._provided_events_client,
                                  self.mp_config) + tuple(self._component_descriptors)

    @staticmethod
    def from_yaml_file(conf_path: Union[pathlib.Path, str]) -> 'Pipeline':
        """Creates a pipeline from a yaml pipeline configuration file.

        Args:
            conf_path (str or pathlib.Path): The path to the configuration file.

        Returns:
            Pipeline object from the configuration.

        """
        conf_path = pathlib.Path(conf_path)
        from yaml import load
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        with conf_path.open('rb') as f:
            conf = load(f, Loader=Loader)
        return Pipeline.load_configuration(conf)

    @staticmethod
    def load_configuration(conf: Dict) -> 'Pipeline':
        """Creates a pipeline from a pipeline configuration dictionary.

        Args:
            conf (Dict): The pipeline configuration dictionary.

        Returns:
            Pipeline created from the configuration.

        """
        name = conf.get('name', None)
        events_address = conf.get('events_address', None) or conf.get('events_addresses', None)
        components = []
        conf_components = conf.get('components', [])
        for conf_component in conf_components:
            components.append(
                RemoteProcessor(
                    processor_id=conf_component['processor_id'],
                    address=conf_component['address'],
                    component_id=conf_component.get('component_id', None),
                    params=dict(conf_component.get('params', {}))
                )
            )
        mp_config = MpConfig.from_configuration(conf.get('mp_config', {}))
        return Pipeline(*components, name=name, events_address=events_address, mp_config=mp_config)

    @property
    def events_client(self) -> EventsClient:
        if self._events_client is not None:
            return self._events_client
        self._created_events_client = True
        self._events_client = EventsClient(address=self.events_address)
        return self._events_client

    @events_client.setter
    def events_client(self, value: EventsClient):
        self._events_client = value

    @property
    def _components(self) -> 'List[processing.ProcessingComponent]':
        try:
            return self.__components
        except AttributeError:
            self.__components = [desc.create_pipeline_component(self._component_ids,
                                                                lambda: self.events_client)
                                 for desc in self._component_descriptors]
            return self.__components

    @_components.deleter
    def _components(self):
        for component in self.__components:
            component.close()
        del self.__components

    def run_multithread(
            self,
            source: Union[
                Iterable[Union['mtap.Document', 'mtap.Event']], 'processing.ProcessingSource'],
            *, params: Optional[Dict[str, Any]] = None,
            show_progress: Optional[bool] = None,
            total: Optional[int] = None,
            close_events: Optional[bool] = None,
            max_failures: Optional[int] = None,
            workers: Optional[int] = None,
            read_ahead: Optional[int] = None,
            mp_context=None
    ):
        """Runs this pipeline on a source which provides multiple documents / events.

        Concurrency is per-event, with each event being provided a thread which runs it through the
        pipeline.

        Args:
            source (~typing.Union[~typing.Iterable[~typing.Union[Event, Document]], ProcessingSource])
                A generator of events or documents to process. This should be an
                :obj:`~typing.Iterable` of either :obj:`Event` or :obj:`Document` objects or a
                :obj:`~mtap.processing.ProcessingSource`.
            params (~typing.Optional[dict[str, ~typing.Any]])
                Json object containing params specific to processing this event, the existing params
                dictionary defined in :func:`~PipelineBuilder.add_processor` will be updated with
                the contents of this dict.
            show_progress (~typing.Optional[bool])
                Whether to print a progress bar using tqdm.
            total (~typing.Optional[int])
                An optional argument indicating the total number of events / documents that will be
                provided by the iterable, for the progress bar.
            close_events (~typing.Optional[bool])
                Whether the pipeline should close events after they have been fully processed
                through all components.
            max_failures (~typing.Optional[int])
                The number of acceptable failures. Once this amount is exceeded processing will
                halt. Note that because of the nature of conccurrency processing may continue for a
                short amount of time before termination.
            workers (~typing.Optional[int])
                The number of threads to process documents on.
            read_ahead (~typing.Optional[int])
                The number of source documents to read ahead into memory before processing.
            mp_context (multiprocessing context, optional)
                An optional override for the multiprocessing context.

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
        show_progress = show_progress if show_progress is not None else self.mp_config.show_progress
        close_events = close_events if close_events is not None else self.mp_config.close_events
        max_failures = max_failures if max_failures is not None else self.mp_config.max_failures
        workers = workers if workers is not None else self.mp_config.workers
        mp_context = (multiprocessing.get_context(self.mp_config.mp_start_method)
                      if mp_context is None else mp_context)
        read_ahead = read_ahead if read_ahead is not None else self.mp_config.read_ahead
        with _PipelineMultiRunner(self, source, params, show_progress, total, close_events,
                                  max_failures, workers, read_ahead, mp_context) as runner:
            runner.run()

    def run(self, target: Union['mtap.Event', 'mtap.Document'], *,
            params: Optional[Dict[str, Any]] = None) -> 'processing.PipelineResult':
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
            >>> e = mtap.Event()
            >>> document = mtap.Document('plaintext', text="...", event=e)
            >>> with Pipeline(...) as pipeline:
            >>>     pipeline.run(document)
            >>>     # is equivalent to pipeline.run(document.event, params={'document_name': document.document_name})

            The 'document_name' param is used to indicate to :obj:`~mtap.DocumentProcessor`
            which document on the event to process.
        """
        event, params = _event_and_params(target, params)
        event_id = event.event_id

        result = self._run_by_event_id(event_id, event.event_service_instance_id, params)
        self._add_result_times(result)

        for component_result in result.component_results:
            try:
                event.add_created_indices(component_result.created_indices)
            except AttributeError:
                pass
        return result

    def _run_by_event_id(self, event_id, event_service_instance_id, params):
        start = datetime.now()
        results = [component.call_process(event_id, event_service_instance_id, params)
                   for component in self._components]
        total = datetime.now() - start
        results = [_base.ProcessingResult(identifier=component.component_id, result_dict=result[0],
                                          timing_info=result[1], created_indices=result[2]) for
                   component, result in zip(self._components, results)]
        logger.debug('Finished processing event_id: %s', event_id)
        return _base.PipelineResult(results, total)

    def _add_result_times(self, result):
        times = {}
        for component_id, _, component_times, _ in result.component_results:
            times.update({component_id + ':' + k: v for k, v in component_times.items()})
        times[self.name + 'total'] = result.elapsed_time
        _timing.add_times(self.times_map, times)

    @overload
    def processor_timer_stats(self) -> 'List[processing.AggregateTimingInfo]':
        """Returns the timing information for all processors.

        Returns:
            List[AggregateTimingInfo]:
                A list of timing info objects, one for each processor, in the same order
                that the processors were added to the pipeline.
        """
        ...

    @overload
    def processor_timer_stats(self, identifier: str) -> 'processing.AggregateTimingInfo':
        """Returns the timing info for one processor.

        Args:
            identifier (Optional[str]): The pipeline component_id for the processor to return
                timing info.

        Returns:
            AggregateTimingInfo: The timing info for the specified processor.

        """
        ...

    def processor_timer_stats(self, identifier=None):
        if identifier is not None:
            aggregates = _timing.create_timer_stats(self.times_map, identifier + ':')
            aggregates = {k[(len(identifier) + 1):]: v for k, v in aggregates.items()}
            return _base.AggregateTimingInfo(identifier=identifier, timing_info=aggregates)
        timing_infos = []
        for component in self._components:
            component_id = component.component_id
            aggregates = _timing.create_timer_stats(self.times_map, component_id + ':')
            aggregates = {k[(len(component_id) + 1):]: v for k, v in aggregates.items()}
            timing_infos.append(
                _base.AggregateTimingInfo(identifier=component_id, timing_info=aggregates))

        return timing_infos

    def pipeline_timer_stats(self) -> 'processing.AggregateTimingInfo':
        """The aggregated statistics for the global runtime of the pipeline.

        Returns:
            AggregateTimingInfo: The timing stats for the global runtime of the pipeline.

        """
        pipeline_id = self.name
        aggregates = _timing.create_timer_stats(self.times_map, pipeline_id)
        aggregates = {k[len(pipeline_id):]: v for k, v in aggregates.items()}
        return _base.AggregateTimingInfo(identifier=self.name, timing_info=aggregates)

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
        if self._created_events_client:
            self._provided_events_client.close()

    def as_processor(self) -> 'processing.EventProcessor':
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
        return self._component_descriptors[item]

    def __setitem__(self, key, value):
        self._clear_components()
        self._component_descriptors[key] = value

    def __delitem__(self, key):
        self._clear_components()
        del self._component_descriptors[key]

    def __len__(self):
        return len(self._component_descriptors)

    def _clear_components(self):
        try:
            del self._components
        except AttributeError:
            pass

    def insert(self, index, o) -> None:
        self._clear_components()
        self._component_descriptors.insert(index, o)

    def __repr__(self):
        return "Pipeline(" + ', '.join(
            [repr(component) for component in self._component_descriptors]) + ')'


class ProcessingSource(ContextManager, ABC):
    """Provides events or documents for the multi-threaded pipeline runner. Also has functionality
    for receiving results.

    """
    __slots__ = ('_total',)

    @property
    def total(self) -> Optional[int]:
        """The total number of documents this source will provide.

        Returns:
            str or None count of the total events or None if not known.

        """
        try:
            return self._total
        except AttributeError:
            return None

    @total.setter
    def total(self, count: Optional[int]):
        self._total = count

    @abstractmethod
    def provide(self, consume: Callable[[Union['mtap.Document', 'mtap.Event']], None]):
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

    def receive_result(self, result: 'processing.PipelineResult', event: 'mtap.Event'):
        """Optional method: Asynchronous callback which returns the results of processing. This
        method is called on a processing worker thread. Default behavior is to do nothing.

        Args:
            result (PipelineResult): The result of processing using the pipeline.
            event (Event): The event processed.

        """
        pass

    def receive_failure(self, exc: 'processing.ProcessingError') -> bool:
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
    __slots__ = ('it',)

    def __init__(self, source):
        # We use an iterator here so we can ensure that it gets closed on unexpected / early
        # termination and any caller context managers are exited before their client gets shut down.
        # Using a for-in loop we're not guaranteed, which can cause zombie unclosed events on the
        # event service.
        self.it = iter(source)

    def provide(self, consume: Callable[[Union['mtap.Document', 'mtap.Event']], None]):
        while True:
            try:
                target = next(self.it)
            except StopIteration:
                break
            consume(target)

    def close(self):
        try:
            self.it.close()
        except AttributeError:
            pass


class _PipelineProcessor(_base.EventProcessor):
    __slots__ = ('_components',)

    def __init__(self, components: List['processing.ProcessingComponent']):
        self._components = components

    def process(self, event: 'mtap.Event', params: Dict[str, Any] = None):
        results = [component.call_process(event.event_id, event.event_service_instance_id, params)
                   for component in self._components]
        times = {}
        for _, component_times, _ in results:
            times.update(component_times)
        for k, v in times.items():
            _PipelineProcessor.current_context().add_time(k, v)

        return {'component_results': [result[0] for result in results]}


_mp_pipeline = None


def _mp_process_init(config, pipeline):
    global _mp_pipeline
    Config(config).enter_context()
    _mp_pipeline = pipeline

    def cleanup_pipeline(*_):
        _mp_pipeline.close()

    signal.signal(signal.SIGINT, cleanup_pipeline)


def _mp_process_event(event_id, event_service_instance_id, params):
    assert isinstance(_mp_pipeline, Pipeline)
    try:
        result = _mp_pipeline._run_by_event_id(event_id, event_service_instance_id, params)
    except Exception:
        return event_id, None, traceback.format_exc()
    return event_id, result, None


class _PipelineMultiRunner:
    __slots__ = ('pipeline', 'failures', 'max_failures', 'targets_cond', 'active_targets',
                 'close_events', 'max_targets', 'n_threads', 'progress_bar', 'source', 'params',
                 'pool', 'active_events')

    def __init__(self, pipeline, source, params, progress, total, close_events, max_failures,
                 n_threads, read_ahead, mp_context):
        self.pipeline = pipeline
        self.failures = 0
        self.max_failures = max_failures
        self.targets_cond = Condition(Lock())
        self.active_targets = 0
        self.close_events = close_events
        if read_ahead is None:
            read_ahead = n_threads
        self.max_targets = n_threads + read_ahead
        self.n_threads = n_threads
        total = (source.total if hasattr(source, 'total') else None) or total
        self.progress_bar = tqdm(total=total, unit='event', smoothing=0.01) if progress else None

        if not isinstance(source, ProcessingSource):
            if not hasattr(source, '__iter__'):
                raise ValueError('The source needs to either be a ProcessingSource or an Iterable.')
            source = _IterableProcessingSource(source)
        self.source = source
        self.params = params

        self.pool = mp_context.Pool(
            self.n_threads,
            initializer=_mp_process_init,
            initargs=(dict(Config()), pipeline)
        )
        self.active_events = {}

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

    def run(self):
        def result_handler(result):
            event_id, result, error = result
            event = self.active_events.pop(event_id)
            if result is not None:
                self.pipeline._add_result_times(result)
                self.source.receive_result(result, event)
            else:
                if not self.source.receive_failure(error):
                    logger.error('Error while processing event_id: %s\n%s', event_id, error)
                    self.failures += 1
            self.task_completed()
            if self.close_events:
                event.release_lease()

        def error_handler(error):
            logger.error('Unexpected error')
            raise error

        def consume(target):
            if self.max_failures_reached():
                raise ValueError('Max processing failures exceeded.')
            event, params = _event_and_params(target, self.params)
            try:
                event.lease()
                event_id = event.event_id
                self.active_events[event_id] = event
                self.pool.apply_async(_mp_process_event, args=(event_id,
                                                               event.event_service_instance_id,
                                                               params),
                                      callback=result_handler, error_callback=error_handler)
                self.increment_active_tasks()
            except BaseException as e:
                # here we failed sometime between taking a new lease and adding the done
                # callback to the future, meaning the lease will never get freed.
                event.release_lease()
                raise e
            self.wait_to_read()

        try:
            with self.source:
                self.source.provide(consume)
            self.wait_tasks_completed()
        except KeyboardInterrupt:
            print('Pipeline terminated by user (KeyboardInterrupt).')
        if self.max_failures_reached():
            raise ValueError('Max processing failures exceeded.')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.pool.terminate()
        self.pool.join()
        if self.close_events:
            for event in self.active_events.values():
                event.close()


def _unique_component_id(component_ids, component_id):
    count = component_ids.get(component_id, 0)
    count += 1
    component_ids[component_id] = count
    if count > 1:
        component_id = component_id + '-' + str(count)
    return component_id


class FilesInDirectoryProcessingSource(ProcessingSource):
    """Processing source for pipelines which iterates over files in a directory.

    Args:
        client (mtap.EventsClient): The events client to send documents to.
        directory (pathlib.Path or str): The path to the directory of files to process.

    Keyword Args:
         document_name (str): The name of the document to create and add text to.
         extension_glob (str): The glob for which files to create events and documents for.
         count_total (bool): Whether to count the total number of documents before processing.
         errors (~typing.Optional[str]): The errors argument for :func:`open`.

    """
    __slots__ = ('client', 'input_directory', 'document_name', 'extension_glob', 'errors', 'total')

    def __init__(self, client: 'mtap.EventsClient',
                 directory: Union[pathlib.Path, str],
                 *, document_name: str = 'plaintext',
                 extension_glob: str = '*.txt',
                 count_total: bool = True,
                 errors: Optional[str] = None):
        self.client = client
        self.input_directory = pathlib.Path(directory)
        if not self.input_directory.is_dir():
            raise ValueError('Invalid / non-existing input directory: ' + str(self.input_directory))
        self.document_name = document_name
        self.extension_glob = extension_glob
        self.errors = errors
        if count_total:
            self.total = sum(1 for _ in self.input_directory.rglob(self.extension_glob))

    def provide(self, consume: Callable[[Union['mtap.Document', 'mtap.Event']], None]):
        for path in self.input_directory.rglob(self.extension_glob):
            with path.open('r', errors=self.errors) as f:
                txt = f.read()
            relative = str(path.relative_to(self.input_directory))
            with Event(event_id=relative, client=self.client,
                       only_create_new=True) as e:
                doc = e.create_document(self.document_name, txt)
                consume(doc)
