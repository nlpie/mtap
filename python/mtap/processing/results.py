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
from typing import List, NamedTuple, Dict, Generator, Optional


__all__ = (
    'AggregateTimingInfo',
    'ComponentResult',
    'TimerStats',
    'TimerStatsAggregator',
    'TimesMap',
    'add_times',
    'create_timer_stats',
)


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
