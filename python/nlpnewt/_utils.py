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
"""Internal utilities."""

import datetime
import logging
import typing
from concurrent.futures.thread import ThreadPoolExecutor

import math
from google.protobuf import struct_pb2

import nlpnewt

logger = logging.getLogger("nlpnewt")
logger.setLevel(logging.INFO)


def copy_dict_to_struct(d, struct, parents):
    for k, v in d.items():
        copy_item_to_struct(k, v, struct, parents)


def copy_item_to_struct(k, v, struct, parents):
    if isinstance(v, (str, float, bool, int)) or v is None:
        struct[k] = v
    elif isinstance(v, list):
        _check_for_reference_cycle(v, parents)
        copy_list_to_list_value(v, struct.get_or_create_list(k), parents + [v])
    elif isinstance(v, dict):
        _check_for_reference_cycle(v, parents)
        copy_dict_to_struct(v, struct.get_or_create_struct(k), parents + [v])
    elif isinstance(v, object):
        _check_for_reference_cycle(v, parents)
        copy_dict_to_struct(v.__dict__, struct.get_or_create_struct(k), parents + [v])
    else:
        raise TypeError("Unrecognized type:", type(v))


def copy_list_to_list_value(lst, list_value, parents):
    for v in lst:
        if isinstance(v, (str, float, bool, int)) or v is None:
            list_value.append(v)
        elif isinstance(v, list):
            _check_for_reference_cycle(v, parents)
            copy_list_to_list_value(v, list_value.add_list(), parents + [v])
        elif isinstance(v, dict):
            _check_for_reference_cycle(v, parents)
            copy_dict_to_struct(v, list_value.add_struct(), parents + [v])
        elif isinstance(v, object):
            _check_for_reference_cycle(v, parents)
            copy_dict_to_struct(v.__dict__, list_value.add_struct(), parents + [v])
        else:
            raise TypeError("Unrecognized type:", type(v))


def _check_for_reference_cycle(o, parents):
    for parent in parents:
        if o is parent:
            raise ValueError("Reference cycle while preparing for serialization.")


def copy_list_value_to_list(list_value, lst):
    for v in list_value:
        if isinstance(v, (str, float, bool, int)) or v is None:
            lst.append(v)
        elif isinstance(v, struct_pb2.ListValue):
            lst2 = []
            copy_list_value_to_list(v, lst2)
            lst.append(lst2)
        elif isinstance(v, struct_pb2.Struct):
            d = {}
            copy_struct_to_dict(v, d)
            lst.append(d)
        else:
            raise TypeError("Unrecognized type:", type(v))


def copy_struct_to_dict(struct, dictionary):
    try:
        items = struct.items()
    except AttributeError:
        return
    for k, v in items:
        if isinstance(v, (str, float, bool, int)) or v is None:
            dictionary[k] = v
        elif isinstance(v, struct_pb2.ListValue):
            lst = []
            copy_list_value_to_list(v, lst)
            dictionary[k] = lst
        elif isinstance(v, struct_pb2.Struct):
            d = {}
            copy_struct_to_dict(v, d)
            dictionary[k] = d
        else:
            raise TypeError("Unrecognized type:", type(v))


class TimerStatsAggregator:
    def __init__(self):
        self._count = 0
        self._min = datetime.timedelta.max
        self._max = datetime.timedelta.min
        self._mean = 0.0
        self._sse = 0.0
        self._sum = datetime.timedelta(seconds=0)

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
        mean = datetime.timedelta(seconds=self._mean)
        variance = self._sse / self._count
        std = math.sqrt(variance)
        std = datetime.timedelta(seconds=std)
        return nlpnewt.TimerStats(mean=mean, std=std, max=self._max, min=self._min, sum=self._sum)


class ProcessingTimesCollector:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1,
                                            thread_name_prefix='processing_times_listener')
        self._times_map = {}

    def _add_times(self, times):
        for k, v in times.items():
            try:
                agg = self._times_map[k]
            except KeyError:
                agg = TimerStatsAggregator()
                self._times_map[k] = agg
            agg.add_time(v)

    def add_times(self, times):
        self._executor.submit(self._add_times, times)

    def _get_aggregates(self, prefix):
        return {identifier: stats.finalize()
                for identifier, stats in self._times_map.items() if identifier.startswith(prefix)}

    def get_aggregates(self,
                       identifier=None) -> typing.Dict[str, nlpnewt.TimerStats]:
        future = self._executor.submit(self._get_aggregates, identifier or '')
        return future.result()

    def shutdown(self):
        self._executor.shutdown(wait=True)
