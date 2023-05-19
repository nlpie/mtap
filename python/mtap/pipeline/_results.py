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
import copy
from dataclasses import field, dataclass
from datetime import timedelta
from typing import NamedTuple, List, overload

from mtap.processing.results import (
    add_times,
    create_timer_stats,
    AggregateTimingInfo,
    ComponentResult,
    TimesMap,
)


class PipelineResult(NamedTuple):
    """The result of processing an event or document in a pipeline."""

    component_results: List[ComponentResult]
    """The processing results for each individual component"""

    elapsed_time: timedelta
    """The elapsed time for the entire pipeline."""

    def component_result(self, identifier: str) -> ComponentResult:
        """Returns the component result for a specific identifier.

        Args:
            identifier: The processor's identifier in the pipeline.

        Returns:
            ComponentResult: The result for the specified processor.

        """
        try:
            return next(filter(lambda x: x.identifier == identifier,
                               self.component_results))
        except StopIteration:
            raise KeyError('No result for identifier: ' + identifier)


def add_result_times(times_map: TimesMap,
                     result: PipelineResult,
                     pipeline_name: str):
    times = {}
    for component_id, _, component_times, _ in result.component_results:
        times.update({component_id + ':' + k: v for k, v in
                      component_times.items()})
    times[pipeline_name + ':total'] = result.elapsed_time
    add_times(times_map, times)


@dataclass
class PipelineTimes:
    name: str
    component_ids: List[str]
    _times_map: TimesMap = field(default_factory=dict)

    def add_other(self, other: 'PipelineTimes'):
        """Merges all the times from the other times into this.

        Args:
            other: Another pipeline times.
        """
        if self.component_ids != other.component_ids:
            raise ValueError("component_ids need to match")
        _times_map = dict()
        for k in self._times_map:
            if k in other._times_map:
                _times_map[k] = self._times_map[k].merge(other._times_map[k])
        for k in other._times_map:
            if k not in self._times_map:
                _times_map[k] = copy.copy(other._times_map[k])

    @overload
    def processor_timer_stats(self) -> List[AggregateTimingInfo]:
        """Returns the timing information for all processors.

        Returns:
            A list of timing info objects, one for each processing component,
            in the same order as in the pipeline.
        """
        ...

    @overload
    def processor_timer_stats(
            self,
            identifier: str
    ) -> AggregateTimingInfo:
        """Returns the timing info for one processor.

        Args:
            identifier: The pipeline component_id for the processor to return
                timing info.

        Returns:
            The timing info for the specified processor.

        """
        ...

    def processor_timer_stats(self, identifier=None):
        if identifier is not None:
            aggregates = create_timer_stats(self._times_map,
                                            identifier + ':')
            aggregates = {k[(len(identifier) + 1):]: v for k, v in
                          aggregates.items()}
            return AggregateTimingInfo(identifier=identifier,
                                       timing_info=aggregates)
        timing_infos = []
        for component_id in self.component_ids:
            aggregates = create_timer_stats(self._times_map,
                                            component_id + ':')
            aggregates = {k[(len(component_id) + 1):]: v
                          for k, v in aggregates.items()}
            timing_infos.append(
                AggregateTimingInfo(identifier=component_id,
                                    timing_info=aggregates))

        return timing_infos

    def aggregate_timer_stats(self) -> AggregateTimingInfo:
        """The aggregated statistics for the global runtime of the pipeline.

        Returns:
            AggregateTimingInfo: The timing stats for the global runtime of
                the pipeline.

        """
        aggregates = create_timer_stats(self._times_map, self.name)
        aggregates = {k[(len(self.name) + 1):]: v
                      for k, v in aggregates.items()}
        return AggregateTimingInfo(identifier=self.name,
                                   timing_info=aggregates)

    def print(self):
        """Prints all the times collected during this pipeline using
        :func:`print`.
        """
        self.aggregate_timer_stats().print()
        for pipeline_timer in self.processor_timer_stats():
            pipeline_timer.print()

    def add_result_times(self, result: PipelineResult):
        """Adds the times from the result to these times.

        Args:
            result: A pipeline result.
        """
        add_result_times(self._times_map, result, self.name)
