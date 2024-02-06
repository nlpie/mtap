import copy
import dataclasses
import logging
import pathlib
from concurrent.futures import Future
from contextlib import contextmanager
from datetime import datetime
from os import PathLike
from typing import (
    Optional,
    Dict,
    Any,
    Union,
    List,
    Iterable,
)

from mtap._events_client import EventsAddressLike
from mtap.pipeline._common import EventLike, event_and_params
from mtap.pipeline._error_handling import (
    ProcessingErrorHandler,
    SimpleErrorHandler,
    TerminationErrorHandler,
)
from mtap.pipeline._mp_config import MpConfig
from mtap.pipeline._pipeline_components import (
    RemoteProcessor,
    ComponentDescriptor,
)
from mtap.pipeline._results import (
    PipelineResult,
    PipelineTimes,
    PipelineCallback,
)
from mtap.pipeline._sources import ProcessingSource
from mtap.processing import ProcessingComponent
from mtap.processing.results import ComponentResult

logger = logging.getLogger('mtap.processing')

ProcessingSourceLike = Union[Iterable[EventLike], ProcessingSource]


def _cancel_callback(event, read_ahead, cd, close_events):
    def fn(future: Future):
        if close_events:
            event.close()
        read_ahead.task_completed()
        cd.count_down(future.exception() is not None)

    return fn


class ActivePipeline:
    __slots__ = (
        'components'
    )

    components: List[ProcessingComponent]

    def __init__(self, components: List[ProcessingComponent]):
        self.components = components

    def run_by_event_id(
            self,
            event_id: str,
            event_service_instance_id: str,
            params: Dict[str, Any]
    ) -> 'PipelineResult':
        start = datetime.now()
        results = []
        for component in self.components:
            d, ti, ci = component.call_process(event_id,
                                               event_service_instance_id,
                                               params)
            pr = ComponentResult(
                identifier=component.component_id,
                result_dict=d,
                timing_info=ti,
                created_indices=ci
            )
            results.append(pr)

        total = datetime.now() - start
        logger.debug('Finished processing event_id: %s', event_id)
        return PipelineResult(results, total)

    def run(
            self,
            target: EventLike,
            *, params: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        event, params = event_and_params(target, params)
        event_id = event.event_id

        return self.run_by_event_id(
            event_id,
            event.event_service_instance_id,
            params
        )


class Pipeline(List[ComponentDescriptor]):
    """An object which can be used to build and run a pipeline of remote and
    local processors.

    Pipelines are a :obj:`~typing.MutableSequence` containing
    one or more :class:`~mtap.processing.ComponentDescriptor`,
    a pipeline can be modified after creation using this functionality.

    Args:
        *components: Component descriptors created using
            :class:`RemoteProcessor` or :class:`LocalProcessor`.
    """
    __slots__ = (
        'name',
        'events_address',
        'mp_config',
        'error_handlers',
    )

    name: str
    """The pipeline's name."""

    events_address: EventsAddressLike
    """Optional events address. Required if using local processors."""

    mp_config: MpConfig
    """The multiprocessing configuration for the pipeline."""

    error_handlers: List[ProcessingErrorHandler]
    """The error handlers to use when running the pipeline."""

    def __init__(self,
                 *components: ComponentDescriptor,
                 name: Optional[str] = None,
                 events_address: EventsAddressLike = None,
                 mp_config: Optional[MpConfig] = None,
                 error_handlers: List[ProcessingErrorHandler] = None):
        super().__init__(components)
        self.name = name or 'pipeline'
        self.events_address = events_address
        self.mp_config = mp_config or MpConfig()
        self.error_handlers = error_handlers or [
            SimpleErrorHandler(),
            TerminationErrorHandler()
        ]

    def __reduce__(self):
        params = (
            self.name,
            self.events_address,
            self.mp_config,
            self.error_handlers,
        )

        return Pipeline._reconstruct, params, None, iter(self)

    @staticmethod
    def _reconstruct(name, events_address, mp_config, error_handlers):
        pipeline = Pipeline(
            name=name,
            events_address=events_address,
            mp_config=mp_config,
            error_handlers=error_handlers
        )
        return pipeline

    @staticmethod
    def from_yaml_file(conf_path: Union[str, bytes, PathLike]) -> 'Pipeline':
        """Creates a pipeline from a yaml pipeline configuration file.

        Args:
            conf_path: The path to the configuration file.

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
        return Pipeline.from_dict(conf)

    @staticmethod
    def from_dict(conf: Dict) -> 'Pipeline':
        """Creates a pipeline from a pipeline configuration dictionary.

        Args:
            conf: The pipeline configuration dictionary.

        Returns:
            Pipeline created from the configuration.

        """
        bad_keys = [k for k in conf.keys() if
                    k not in ['name', 'events_addresses', 'events_address',
                              'components', 'mp_config', 'error_handlers']]
        if len(bad_keys) > 0:
            raise ValueError('Unrecognized keys in pipeline configuration: {}'.format(bad_keys))

        name = conf.get('name', None)

        if 'events_address' in conf.keys() \
                and 'events_addresses' in conf.keys():
            raise ValueError("Only one of 'events_address' and "
                             "'events_addresses' should be specified.")
        events_address = conf.get('events_address', None) or conf.get('events_addresses', None)

        components = []
        conf_components = conf.get('components', [])
        for conf_component in conf_components:
            if 'processor_id' in conf_component:
                logger.warning(
                    "The 'processor_id' field has been renamed to 'name' "
                    "in pipeline configurations."
                    "For now it is automatically migrated, but it may fail "
                    "in a future version"
                )
                conf_component['name'] = conf_component['processor_id']
            components.append(RemoteProcessor(**conf_component))

        error_handlers = []
        conf_error_handlers = conf.get('error_handlers', [])
        for conf_error_handler in conf_error_handlers:
            handler = ProcessingErrorHandler.from_dict(conf_error_handler)
            error_handlers.append(handler)

        mp_config = MpConfig.from_dict(conf.get('mp_config', {}))

        return Pipeline(
            *components,
            name=name,
            events_address=events_address,
            mp_config=mp_config,
            error_handlers=error_handlers,
        )

    def run_multithread(
            self,
            source: ProcessingSourceLike,
            *, total: Optional[int] = None,
            callback: Optional[PipelineCallback] = None,
            **kwargs,
    ) -> PipelineTimes:
        """Runs this pipeline on a source which provides multiple
        documents / events.

        Concurrency is per-event, with each event being provided a thread
        which runs it through the pipeline.

        Args:
            source: The processing source.
            total: Total documents in the processing source.
            callback: A callback that receives events and their associated
                results from the finished pipeline.
            kwargs: Override for any of the :class:`MpConfig` attributes.

        Raises:
            PipelineTerminated: If an error handler terminates the pipeline before it is completed.

        Examples:
            >>> docs = list(pathlib.Path('abc/').glob('*.txt'))
            >>>
            >>> def document_source():
            >>>     for path in docs:
            >>>         with path.open('r') as f:
            >>>             txt = f.read()
            >>>         with Event(event_id=path.name,
            >>>                    client=pipeline.events_client) as event:
            >>>             doc = event.create_document('plaintext', txt)
            >>>             yield doc
            >>>
            >>> pipeline.run_multithread(document_source(), total=len(docs))
        """
        from mtap.pipeline._mp_pipeline import MpPipelineRunner, MpPipelinePool
        pipeline = copy.deepcopy(self)
        mp_config = dataclasses.asdict(pipeline.mp_config)
        mp_config.update(kwargs)
        pipeline.mp_config = MpConfig(**mp_config)
        with MpPipelinePool(pipeline) as pool:
            runner = MpPipelineRunner(pool, source, total, callback)
            result = runner.run()
        return result

    def run(
            self,
            target: EventLike,
            *, params: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """Processes the event/document using all the processors in the
        pipeline.

        Args:
            target: Either an event or a document to process.
            params: Json object containing params specific to processing this
                event, the existing params dictionary defined in
                :func:`~PipelineBuilder.add_processor` will be updated with
                the contents of this dict.

        Returns:
            The results of all the processors in the pipeline.

        Examples:
            >>> e = mtap.Event()
            >>> document = mtap.Document('plaintext', text="...", event=e)
            >>> pipeline.run(document)
        """
        with self.activate() as active:
            return active.run(target, params=params)

    @contextmanager
    def activate(self) -> ActivePipeline:
        components = []
        try:
            components = [
                component.create_pipeline_component(
                    self.events_address
                ) for component in self if component.enabled
            ]
            yield ActivePipeline(components)
        finally:
            for component in components:
                component.close()

    def _check_for_duplicates(self, component: ComponentDescriptor):
        component_id = component.component_id
        if any(x.component_id == component_id for x in self if x != component):
            raise ValueError(f"Attempted to insert a duplicate component_id: "
                             f"{component_id}")

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._check_for_duplicates(value)

    def insert(self, index, item):
        super().insert(index, item)
        self._check_for_duplicates(item)

    def append(self, item):
        super().append(item)
        self._check_for_duplicates(item)

    def extend(self, other):
        super().extend(other)
        for item in other:
            self._check_for_duplicates(item)

    def create_times(self) -> PipelineTimes:
        """Creates a timing object that can be used to store run times.

        Returns:
            A timing object.

        Examples:

        >>> times = pipeline.create_times()
        >>> result = pipeline.run(document)
        >>> times.add_result_times(result)
        """
        return PipelineTimes(
            self.name,
            [component.component_id for component in self if component.enabled]
        )
