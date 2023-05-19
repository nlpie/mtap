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
import asyncio
import copy
import dataclasses
import logging
import pathlib
from concurrent.futures import Future
from contextlib import contextmanager, ExitStack
from datetime import datetime
from os import PathLike
from typing import (
    Optional,
    Dict,
    Any,
    Union,
    List,
    Callable,
)

from tqdm import tqdm

from mtap import Event
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
)
from mtap.pipeline._remote_runner import RemoteProcessorRunner
from mtap.pipeline._results import (
    PipelineResult,
    PipelineTimes,
)
from mtap.pipeline._sources import ProcessingSourceLike, to_async_source

logger = logging.getLogger('mtap.processing')

PipelineCallback = Callable[[Event, 'PipelineResult'], Any]

POISON = object()


def _cancel_callback(event, read_ahead, cd, close_events):
    def fn(future: Future):
        if close_events:
            event.close()
        read_ahead.task_completed()
        cd.count_down(future.exception() is not None)

    return fn


class PipelineRunner:
    def __init__(
            self,
            components: List[RemoteProcessorRunner],
            mp_config: MpConfig,
            loop: Optional[asyncio.BaseEventLoop] = None,
    ):
        self.components = components
        self.mp_config = mp_config
        self.loop = asyncio.get_running_loop() if loop is None else loop

    async def run_by_event_id(
            self,
            event_id: str,
            event_service_instance_id: str,
            params: Dict[str, Any]
    ) -> 'PipelineResult':
        start = datetime.now()
        results = []
        for component in self.components:
            cr = await component.call_process(
                event_id, event_service_instance_id, params)
            results.append(cr)

        total = datetime.now() - start
        logger.debug('Finished processing event_id: %s', event_id)
        return PipelineResult(results, total)

    async def run(
            self,
            target: EventLike,
            *, params: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        event, params = event_and_params(target, params)
        event_id = event.event_id

        return await self.run_by_event_id(
            event_id,
            event.event_service_instance_id,
            params
        )

    async def mp(self,
                 source: ProcessingSourceLike,
                 total: Optional[int] = None,
                 callback: Optional[PipelineCallback] = None,
                 mp_config: MpConfig = None):
        source = to_async_source(source)
        total = (await source.total()) if total is None else total
        q = asyncio.Queue(mp_config.read_ahead)
        currently_processing = asyncio.Semaphore(mp_config.workers)
        progress = None
        if mp_config.show_progress:
            progress = tqdm(total, unit='events', smoothing=0.01)

        async def process_all():
            async def process(e: Event):
                result = await self.run(e)

                def run_callback():
                    try:
                        callback(e, result)
                    except Exception as exc:
                        logger.error("Error in callback: ", exc)
                    if mp_config.close_events:
                        e.release_lease()
                    progress.update(1)

                await asyncio.to_thread(run_callback)
                currently_processing.release()

            background_tasks = set()
            while True:
                currently_processing.acquire()
                event = await q.get()
                if event is POISON:
                    break
                task = asyncio.create_task(process(event))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

        await asyncio.gather(source.aproduce(q), process_all())


class Pipeline(List[RemoteProcessor]):
    """An object which can be used to build and run a pipeline of remote and
    local processors.

    Pipelines are a :obj:`~typing.MutableSequence` containing
    one or more :class:`~mtap.processing.ComponentDescriptor`,
    a pipeline can be modified after creation using this functionality.

    Args:
        *components: Component descriptors created using
            :class:`RemoteProcessor` or :class:`LocalProcessor`.
    Examples:
        Remote pipeline with name discovery:

        >>> pipeline = Pipeline(RemoteProcessor('processor-1-id'),
        >>>                     RemoteProcessor('processor-2-id'),
        >>>                     RemoteProcessor('processor-3-id'))
        >>>
        >>> with pipeline.events_client() as client:
        >>>     for txt in [...]:
        >>>         with Event(client=client) as event:
        >>>             document = event.add_document('plaintext', txt)
        >>>             results = pipeline.run(document)

        Remote pipeline using addresses:

        >>> pipeline = mtap.Pipeline(
        >>>         RemoteProcessor('processor-1-name',
        >>>                         address='localhost:50052'),
        >>>         RemoteProcessor('processor-2-id',
        >>>                         address='localhost:50053'),
        >>>         RemoteProcessor('processor-3-id',
        >>>                         address='localhost:50054'),
        >>>         events_address='localhost:50051')
        >>> with pipeline.events_client() as client:
        >>>     for txt in texts:
        >>>         with Event(client=client) as event:
        >>>             document = event.add_document('plaintext', txt)
        >>>             results = pipeline.run(document)
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
                 *components: RemoteProcessor,
                 name: Optional[str] = None,
                 events_address: EventsAddressLike = None,
                 mp_config: Optional[MpConfig] = None,
                 error_handlers: List[ProcessingErrorHandler] = None):
        super().__init__(components)
        _check_for_duplicates(self)
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

        pipeline = copy.deepcopy(self)
        mp = dataclasses.asdict(pipeline.mp_config)
        mp.update(kwargs)
        with self.activate() as runner:
            result = runner.mp(source, total=total, callback=callback, mp_config=mp)
        return result

    @contextmanager
    def activate(self) -> PipelineRunner:
        with ExitStack() as exit_stack:
            components = [exit_stack.enter_context(component.create_runner(self.events_address, ))
                          for component in self if component.enabled]
            yield PipelineRunner(components, copy.deepcopy(self.mp_config))

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        _check_for_duplicates(self)

    def insert(self, index, item):
        super().insert(index, item)
        _check_for_duplicates(self)

    def append(self, item):
        super().append(item)
        _check_for_duplicates(self)

    def extend(self, other):
        super().extend(other)
        _check_for_duplicates(self)

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
            self.name, [component.component_id for component in self if component.enabled])


def _check_for_duplicates(seq: List[RemoteProcessor]):
    for i, x in enumerate(seq):
        if any(y.component_id == x.component_id for y in seq[i + 1:]):
            raise ValueError(f"Attempted to insert a duplicate component_id: {x.component_id}")
