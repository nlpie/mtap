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
from operator import attrgetter
from typing import Union, Optional, Any, Iterator, NamedTuple

from .base import Label, L, Location, LabelIndex


class _LabelIndex(LabelIndex):
    def __init__(self, labels):
        self.labels = labels
        self.locations = [label.location for label in labels]

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

    if i != to_index and index[i] == label:
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

    if i != to_index and index.locations[i].location == location:
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


def _covering(index: LabelIndex,
              x: Union[Label, int],
              end: Optional[int] = None,
              from_index: int = 0,
              to_index: int = ...):
    pass


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

    def update_bounds(self,
                      min_start=0,
                      max_start=float('inf'),
                      min_end=0,
                      max_end=float('inf')):
        bounds = self.bounds
        min_start = max(bounds.min_start, min_start)
        max_start = min(bounds.max_start, max_start)
        min_end = max(bounds.min_end, min_end)
        max_end = max(bounds.max_end, max_end)
        left = _index_lt(self.label_index, Location(min_start, min_end), bounds.left, bounds.right + 1)

        if right < left:
            raise ValueError

        bounds = _Bounds(left, right, min_start, max_start, min_end, max_end)
        return self.__class__(self.label_index, bounds)

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

    @abstractmethod
    def ascending(self) -> bool:
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
        self._d = direction  # internal directional delegate

    @property
    def distinct(self):
        return False

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        pass

    def at(self, label: Union[Label, Location], default) -> Union[L, 'LabelIndex[L]']:
        pass

    def __contains__(self, item: Any) -> bool:
        try:
            self.index(item)
            return True
        except ValueError:
            return False

    def __len__(self) -> int:
        length = self._len
        if length is None:
            length = 0
            if self._d.last_index is not None:
                i = self._d.first_index
                while True:
                    try:
                        length += 1
                        i = self._d.next_index(i)
                    except StopIteration:
                        break
            self._len = length
        return length

    def __iter__(self) -> Iterator[L]:
        pass

    def __reversed__(self) -> 'LabelIndex[L]':
        pass

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        d = self._d
        if not isinstance(x, Label) or not d.bounds.contains(x):
            raise ValueError
        return _index(d.label_index, x, d.bounds.left, d.bounds.right + 1)

    def count(self, x: Any) -> int:
        d = self._d
        try:
            i = self.index(x)
        except ValueError:
            return 0
        count = 1
        while i < d.bounds.right:
            i += 1
            label = d.label_index[i]
            if d.bounds.contains(label) and label == x:
                count += 1
        return count

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        if end is None:
            if isinstance(x, Label):
                x = x.location
            if not isinstance(x, Location):
                raise TypeError
            start = x.start_index
            end = x.end_index
        else:
            if not isinstance(x, int):
                raise TypeError
            if not isinstance(end, int):
                raise TypeError
            start = x

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        pass

    def ascending(self) -> 'LabelIndex[L]':
        d = self._d
        if not d.ascending:
            return _View(_Ascending(d.label_index, d.bounds))
        else:
            return self

    def descending(self) -> 'LabelIndex[L]':
        d = self._d
        if d.ascending:
            return _View(_Descending(d.label_index, d.bounds))
        else:
            return self


def create_standard_label_index(labels):
    labels = sorted(labels, key=attrgetter('location'))
    return _LabelIndex(labels)
