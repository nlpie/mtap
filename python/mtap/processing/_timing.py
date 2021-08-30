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
from datetime import timedelta
import math
import typing
from typing import TYPE_CHECKING

from mtap.processing import _base

if TYPE_CHECKING:
    import mtap
    from mtap import processing


class TimerStatsAggregator:
    __slots__ = ('_count', '_min', '_max', '_mean', '_sse', '_sum')

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
        return _base.TimerStats(mean=mean, std=std, max=self._max, min=self._min, sum=self._sum)


def add_times(times_map, times):
    for k, v in times.items():
        try:
            agg = times_map[k]
        except KeyError:
            agg = TimerStatsAggregator()
            times_map[k] = agg
        agg.add_time(v)


def create_timer_stats(times_map, prefix=None) -> typing.Dict[str, 'processing.TimerStats']:
    return {identifier: stats.finalize()
            for identifier, stats in times_map.items() if identifier.startswith(prefix)}
