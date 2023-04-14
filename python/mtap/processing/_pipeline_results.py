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
import math
from dataclasses import dataclass, field
from datetime import timedelta
from typing import overload, List, NamedTuple, Dict, Generator, Optional


class ComponentResult(NamedTuple):
    """The result of processing one document or event through a single
    processing component.
    """

    identifier: str
    """The id of the processor with respect to the pipeline."""

    result_dict: Dict
    """The json object returned by the processor as its results."""

    timing_info: Dict[str, timedelta]
    """A dictionary of the times taken processing this document."""

    created_indices: Dict[str, List[str]]
    """Any indices that have been added to documents by this processor."""


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


class TimerStats(NamedTuple):
    """Statistics about a specific keyed measured duration recorded by a
    :obj:`~mtap.processing.base.Stopwatch`.
    """

    mean: timedelta
    """The sample mean of all measured durations."""

    std: timedelta
    """The sample standard deviation of all measured durations."""

    min: timedelta
    """The minimum of all measured durations."""

    max: timedelta
    """The maximum of all measured durations."""

    sum: timedelta
    """The sum of all measured durations."""


class AggregateTimingInfo(NamedTuple):
    """Collection of all the timing info for a specific item / component."""

    identifier: str
    """The ID of the processor with respect to the pipeline."""

    timing_info: 'Dict[str, TimerStats]'
    """A map from all the timer keys for the processor to the 
    aggregated duration statistics.
    """

    def print_times(self):
        """Prints the aggregate timing info for all processing components
        using ``print``.
        """
        print(self.identifier)
        print("-------------------------------------")
        for key, stats in self.timing_info.items():
            print("  [{}]\n"
                  "    mean: {}\n"
                  "    std: {}\n"
                  "    min: {}\n"
                  "    max: {}\n"
                  "    sum: {}".format(key, stats.mean, stats.std, stats.min,
                                       stats.max, stats.sum))
        print("")

    @staticmethod
    def csv_header() -> str:
        """Returns the header for CSV formatted timing data.

        Returns:
            A string containing the column headers.
        """
        return 'key,mean,std,min,max,sum\n'

    def timing_csv(self) -> Generator[str, None, None]:
        """Returns the timing data formatted as a string, generating each

        Returns:
            A generator of string rows for csv.
        """
        for key, stats in self.timing_info.items():
            yield '{}:{},{},{},{},{},{}\n'.format(self.identifier,
                                                  key,
                                                  stats.mean,
                                                  stats.std,
                                                  stats.min,
                                                  stats.max,
                                                  stats.sum)


TimesMap = 'Dict[str, TimerStatsAggregator]'


@dataclass
class BatchPipelineResult:
    name: str
    component_ids: List[str]
    _times_map: TimesMap = field(default_factory=dict)

    @overload
    def processor_timer_stats(self) -> 'List[AggregateTimingInfo]':
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
    ) -> 'AggregateTimingInfo':
        """Returns the timing info for one processor.

        Args:
            identifier: The pipeline component_id for the processor to return
                timing info.

        Returns:
            AggregateTimingInfo: The timing info for the specified processor.

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
            aggregates = {k[(len(component_id) + 1):]: v for k, v in
                          aggregates.items()}
            timing_infos.append(
                AggregateTimingInfo(identifier=component_id,
                                    timing_info=aggregates))

        return timing_infos

    def aggregate_timer_stats(self) -> 'AggregateTimingInfo':
        """The aggregated statistics for the global runtime of the pipeline.

        Returns:
            AggregateTimingInfo: The timing stats for the global runtime of
                the pipeline.

        """
        aggregates = create_timer_stats(self._times_map, self.name)
        aggregates = {k[len(self.name):]: v for k, v in aggregates.items()}
        return AggregateTimingInfo(identifier=self.name,
                                   timing_info=aggregates)

    def print_times(self):
        """Prints all the times collected during this pipeline using
        :func:`print`.
        """
        self.aggregate_timer_stats().print_times()
        for pipeline_timer in self.processor_timer_stats():
            pipeline_timer.print_times()

    def add_result_times(self, result: PipelineResult):
        add_result_times(self._times_map, result, self.name)


def add_times(times_map: TimesMap, times: Dict[str, timedelta]):
    for k, v in times.items():
        try:
            agg = times_map[k]
        except KeyError:
            agg = TimerStatsAggregator()
            times_map[k] = agg
        agg.add_time(v)


def create_timer_stats(times_map: TimesMap,
                       prefix: Optional[str] = None) -> TimesMap:
    return {identifier: stats.finalize()
            for identifier, stats in times_map.items() if
            identifier.startswith(prefix)}


def add_result_times(times_map: TimesMap,
                     result: PipelineResult,
                     pipeline_name: str):
    times = {}
    for component_id, _, component_times, _ in result.component_results:
        times.update({component_id + ':' + k: v for k, v in
                      component_times.items()})
    times[pipeline_name + '_total'] = result.elapsed_time
    add_times(times_map, times)


@dataclass
class TimerStatsAggregator:
    count: int = 0
    min: timedelta = timedelta.max
    max: timedelta = timedelta.min
    mean: float = 0.0
    sse: float = 0.0
    sum: timedelta = field(default_factory=lambda: timedelta(seconds=0))

    def add_time(self, time: timedelta):
        if time < self.min:
            self.min = time
        if time > self.max:
            self.max = time

        self.count += 1
        self.sum += time
        time = time.total_seconds()
        delta = time - self.mean
        self.mean += delta / self.count
        delta2 = time - self.mean
        self.sse += delta * delta2

    def finalize(self) -> TimerStats:
        mean = timedelta(seconds=self.mean)
        variance = self.sse / self.count
        std = math.sqrt(variance)
        std = timedelta(seconds=std)
        return TimerStats(
            mean=mean,
            std=std,
            max=self.max,
            min=self.min,
            sum=self.sum
        )
