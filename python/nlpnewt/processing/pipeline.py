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
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, List, NamedTuple

from nlpnewt._config import Config
from nlpnewt.events import Event, Events, Document
from nlpnewt.processing._runners import ProcessorRunner, RemoteRunner, ProcessingTimesCollector
from nlpnewt.processing._utils import unique_component_id
from nlpnewt.processing.base import EventProcessor, ProcessingResult, AggregateTimingInfo
from nlpnewt.processing._context import processor_local


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
            self.__times_collector = ProcessingTimesCollector()
            return self.__times_collector

    def add_processor(self, name: str, address: Optional[str] = None, *,
                      identifier: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
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
        component_id = unique_component_id(self._component_ids, processor_id)
        runner = RemoteRunner(config=self._config,
                              processor_id=processor_id,
                              address=address,
                              component_id=component_id,
                              params=params)
        self._components.append(runner)

    def add_local_processor(self, proc: EventProcessor,
                            identifier: str, events: Events, *,
                            params: Optional[Dict[str, Any]] = None):
        """Adds a processor to the pipeline which will run locally (in the same process as the
        pipeline).

        Parameters
        ----------
        proc: EventProcessor
            The processor instance to run with the pipeline.
        identifier: str
            An identifier for processor in the context of the pipeline.
        events: Events
            The events object that will be used to open copies of the event.
        params: dict, optional
            An optional parameter dictionary that will be passed to the processor as parameters
            with every document.
        """
        identifier = unique_component_id(self._component_ids, identifier)

        runner = ProcessorRunner(proc=proc,
                                 events=events,
                                 identifier=identifier,
                                 params=params)
        self._components.append(runner)

    def run(self, target: Union[Event, Document], *,
            params: Optional[Dict[str, Any]] = None) -> List[ProcessingResult]:
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
        """The aggregated statistics for the global runtime of the pipeline.

        Returns
        -------
        AggregateTimingInfo
            The timing stats for the global runtime of the pipeline.

        """
        pipeline_id = 'pipeline:'
        aggregates = self._times_collector.get_aggregates(pipeline_id)
        aggregates = {k[len(pipeline_id):]: v for k, v in aggregates.items()}
        return AggregateTimingInfo(identifier='pipeline', timing_info=aggregates)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_val is not None:
            return False

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

    def print_times(self):
        """Prints all of the times collected during this pipeline.
        """
        self.pipeline_timer_stats().print_times()
        for pipeline_timer in self.processor_timer_stats():
            pipeline_timer.print_times()


class _PipelineProcessor(EventProcessor):
    def __init__(self, components: List[Union[ProcessorRunner, RemoteRunner]]):
        self._components = components

    def process(self,
                event: Event,
                params: Dict[str, Any] = None):
        results = [component.call_process(event.event_id, params) for component in self._components]
        times = {}
        for _, component_times, _ in results:
            times.update(component_times)
        for k, v in times.items():
            processor_local.context.add_time(k, v)

        return {'component_results': [result[0] for result in results]}

    def close(self):
        for component in self._components:
            try:
                component.close()
            except AttributeError:
                pass