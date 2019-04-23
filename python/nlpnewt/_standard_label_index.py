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
"""Internal implementation of a standard non-distinct label index."""
from abc import ABC, abstractmethod
from bisect import bisect_left, bisect_right
from enum import Enum
from operator import attrgetter
from typing import Union, Optional, Any, Iterator, Type, NamedTuple

from .base import Label, L, Location, LabelIndex


class _LabelIndex(LabelIndex):
    def __init__(self, labels):
        self.labels = labels
        self.locations = [label.location for label in labels]

    @property
    def distinct(self):
        return False

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        pass

    def at(self, label: Union[Label, Location], default) -> Union[L, 'LabelIndex[L]']:
        pass

    def __len__(self) -> int:
        return len(self.labels)

    def __contains__(self, item: Any):
        pass

    def __iter__(self) -> Iterator[L]:
        return iter(self.labels)

    def __reversed__(self) -> 'LabelIndex[L]':
        pass

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        pass

    def count(self, x: Any) -> int:
        pass

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def ascending(self) -> 'LabelIndex[L]':
        return self

    def descending(self) -> 'LabelIndex[L]':
        bounds = _Bounds(0, len(self.labels))
        return _View(_Ascending(self, bounds))


def _index(index: _LabelIndex,
           label: Label,
           from_index: int = 0,
           to_index: int = ...) -> int:
    if to_index is ...:
        to_index = len(index)

    i = bisect_left(index.locations, label.location, from_index, to_index)

    if i != len(index) and index[i] == label:
        return i
    raise ValueError


def _location_index(index: _LabelIndex,
                    location: Union[Label, Location],
                    from_index: int = 0,
                    to_index: int = ...) -> int:
    if isinstance(location, Label):
        location = location.location
    if to_index is ...:
        to_index = len(index)

    i = bisect_left(index.locations, location, from_index, to_index)

    if i != len(index) and index.locations[i].location == location:
        return i
    raise ValueError


def _index_lt(index: _LabelIndex,
              location: Union[Label, Location],
              from_index: int = 0,
              to_index: int = ...) -> int:
    if isinstance(location, Label):
        location = location.location
    if to_index is ...:
        to_index = len(index)

    return bisect_left(index.locations, location, from_index, to_index) - 1


def _index_le(index: _LabelIndex,
              location: Union[Label, Location],
              from_index: int = 0,
              to_index: int = ...) -> int:
    if isinstance(location, Label):
        location = location.location
    if to_index is ...:
        to_index = len(index)

    return bisect_right(index.locations, location, from_index, to_index) - 1


def _index_gt(index: _LabelIndex,
              location: Union[Label, Location],
              from_index: int = 0,
              to_index: int = ...) -> int:
    if isinstance(location, Label):
        location = location.location
    if to_index is ...:
        to_index = len(index)

    return bisect_right(index.locations, location, from_index, to_index)


def _index_ge(index: _LabelIndex,
              location: Union[Label, Location],
              from_index: int = 0,
              to_index: int = ...) -> int:
    if isinstance(location, Label):
        location = location.location
    if to_index is ...:
        to_index = len(index)

    return bisect_left(index.locations, location, from_index, to_index)

class _Bounds(NamedTuple):
    left: int
    right: int
    min_start: float = 0
    max_start: float = float('inf')
    min_end: float = 0
    max_end: float = float('inf')

    def contains(self, label: Label) -> bool:
        return (self.min_start <= label.start_index <= self.max_start
                and self.min_end <= label.end_index <= self.max_end)


class _Direction(ABC):

    def __init__(self, label_index: _LabelIndex, bounds: _Bounds):
        self.label_index = label_index
        self.bounds = bounds

    def end_in_bounds(self, index: int):
        return self.bounds.min_end <= self.label_index[index].end_index <= self.bounds.max_end

    def next_index_ascending(self, index: int) -> int:
        while index < self.bounds.right:
            index += 1
            if self.end_in_bounds(index):
                return index
        raise StopIteration

    def next_index_descending(self, index: int) -> int:
        while index > self.bounds.left:
            index -= 1
            if self.end_in_bounds(index):
                return index
        raise StopIteration

    @property
    @abstractmethod
    def first_index(self) -> int:
        ...

    @property
    @abstractmethod
    def last_index(self) -> int:
        ...

    @abstractmethod
    def next_index(self, index: int) -> int:
        ...

    @abstractmethod
    def prev_index(self, index: int) -> int:
        ...


class _Ascending(_Direction):

    @property
    def first_index(self) -> int:
        return self.bounds.left

    @property
    def last_index(self) -> int:
        return self.bounds.right

    def next_index(self, index: int) -> int:
        return self.next_index_ascending(index)

    def prev_index(self, index: int) -> int:
        return self.next_index_descending(index)


class _Descending(_Direction):
    pass


class _View(LabelIndex):
    def __init__(self, direction: _Direction):
        self._direction = direction

    @property
    def distinct(self):
        return False

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        pass

    def at(self, label: Union[Label, Location], default) -> Union[L, 'LabelIndex[L]']:
        pass

    def __len__(self) -> int:
        length = self._len
        if length is None:
            length = 0
            if self._direction.last_index is not None:
                i = self._direction.first_index
                while True:
                    try:
                        length += 1
                        i = self._direction.next_index(i)
                    except StopIteration:
                        break
            self._len = length
        return length

    def __iter__(self) -> Iterator[L]:
        pass

    def __reversed__(self) -> 'LabelIndex[L]':
        pass

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        pass

    def count(self, x: Any) -> int:
        pass

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def ascending(self) -> 'LabelIndex[L]':
        pass

    def descending(self) -> 'LabelIndex[L]':
        pass


def create_standard_label_index(labels):
    labels = sorted(labels, key=attrgetter('location'))
    return _LabelIndex(labels)
