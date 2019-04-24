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
from abc import abstractmethod, ABCMeta
from bisect import bisect_left, bisect_right
from operator import attrgetter
from typing import Union, Optional, Any, Iterator, NamedTuple, Generic, List

from ._labels import EMPTY_INDEX
from .base import Label, L, Location, LabelIndex


class _SortedLabels:
    def __init__(self, labels: List[Label]):
        self.labels = labels

    @property
    def locations(self) -> List[Location]:
        try:
            return self._locations
        except AttributeError:
            self._locations = [label.location for label in self.labels]

    def index(self,
              label: Label,
              from_index: int = 0,
              to_index: int = ...) -> int:
        if not isinstance(label, Label):
            raise ValueError
        if to_index is ...:
            to_index = len(self.labels)

        i = bisect_left(self.locations, label.location, from_index, to_index)

        if i != to_index and self.labels[i] == label:
            return i
        raise ValueError

    def index_location(self,
                       location: Union[Label, Location],
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        location = _location(location)
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_left(self.locations, location, from_index, to_index)

        if i != to_index and self.locations[i] == location:
            return i
        raise ValueError

    def index_lt(self,
                 location: Union[Label, Location],
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if isinstance(location, Label):
            location = location.location
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_left(self.locations, location, from_index, to_index)
        if i > from_index:
            return i - 1
        raise ValueError

    def index_le(self,
                 location: Union[Label, Location],
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if isinstance(location, Label):
            location = location.location
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_right(self.locations, location, from_index, to_index)
        if i > from_index:
            return i - 1
        raise ValueError

    def index_gt(self,
                 location: Union[Label, Location],
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if isinstance(location, Label):
            location = location.location
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_right(self.locations, location, from_index, to_index)
        if i != to_index:
            return i
        raise ValueError

    def index_ge(self,
                 location: Union[Label, Location],
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if isinstance(location, Label):
            location = location.location
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_left(self.locations, location, from_index, to_index)
        if i != to_index:
            return i
        raise ValueError

    def view_delegate(self, start=0, end=...):
        if end is ...:
            end = len(self.locations)
        bounds = _Bounds(start, end)
        return _Ascending(self, bounds)


class _LabelIndex(LabelIndex):
    def __init__(self, labels: _SortedLabels):
        self._l = labels

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        if isinstance(idx, int):
            return self._l.labels[idx]
        elif isinstance(idx, slice):
            if idx.step != 1:
                raise IndexError("Step values other than 1 are not supported.")
            bounds = _Bounds(idx.start, idx.stop - 1)
            return _View(_Ascending(self._l, bounds))
        else:
            raise TypeError("Index must be int or slice.")

    def at(self, label: Union[Label, Location], default=...) -> Union[L, 'LabelIndex[L]']:
        location = _location(label)
        l = self._l
        start = l.index_location(location)
        end = start
        while end < len(l.labels) - 1 and l.labels[end + 1].location == location:
            end += 1

        if start == end:
            return l.labels[start]
        else:
            return _View(l.view_delegate(start, end))

    def __len__(self) -> int:
        return len(self._l.labels)

    def __contains__(self, item: Any) -> bool:
        try:
            self.index(item)
            return True
        except ValueError:
            return False

    def __iter__(self) -> Iterator[L]:
        return iter(self._l.labels)

    def __reversed__(self) -> 'LabelIndex[L]':
        return _View(_Descending(self._l, _Bounds(0, len(self._l.labels) - 1)))

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        return self._l.index(x)

    def count(self, x: Any) -> int:
        try:
            i = self.index(x)
        except ValueError:
            return 0
        count = 1
        l = self._l
        while i < len(l.locations) - 1 and l.locations[i + 1] == x.location:
            i += 1
            label = l.labels[i]
            if label == x:
                count += 1
        return count

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        return _View(self._l.view_delegate()).covering(x, end)

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        return _View(self._l.view_delegate()).inside(x, end)

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        return _View(self._l.view_delegate()).beginning_inside(x, end)

    def ascending(self) -> 'LabelIndex[L]':
        return self

    def descending(self) -> 'LabelIndex[L]':
        l = self._l
        bounds = _Bounds(0, len(l.labels))
        return _View(_Descending(l, bounds))


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

    def update_ends(self, left, right) -> '_Bounds':
        return _Bounds(left, right, self.min_start, self.max_start, self.min_end, self.max_end)


class _ViewDelegate(Generic[L], metaclass=ABCMeta):

    def __init__(self, labels: _SortedLabels, bounds: _Bounds):
        self.l = labels
        self.bounds = bounds
        self._indices = None

    @property
    def indices(self) -> List[int]:
        try:
            return self._indices
        except AttributeError:
            def it():
                i = self.first_index
                while True:
                    try:
                        i = self.next_index(i)
                        yield i
                    except StopIteration:
                        break

            self._indices = [i for i in it()]

    def __getitem__(self, idx) -> Label:
        return self.l.labels[self.indices[idx]]

    def __iter__(self) -> Iterator[Label]:
        for idx in self.indices:
            yield self.l.labels[idx]

    def __len__(self):
        return len(self.indices)

    def end_in_bounds(self, index: int) -> bool:
        return self.bounds.min_end <= self.l.locations[index].end_index <= self.bounds.max_end

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
                      *,
                      min_start=0,
                      max_start=float('inf'),
                      min_end=0,
                      max_end=float('inf')) -> '_ViewDelegate':
        bounds = self.bounds
        min_start = max(bounds.min_start, min_start)
        max_start = min(bounds.max_start, max_start)
        min_end = max(bounds.min_end, min_end)
        max_end = max(bounds.max_end, max_end)
        left = self.l.index_lt(Location(min_start, min_end),
                               bounds.left, bounds.right + 1) + 1
        right = self.l.index_gt(Location(max_start, max_end),
                                left, bounds.right + 1) - 1

        while right >= left:
            if self.l.labels[right].end_index <= max_end:
                break
            right -= 1

        if right < left:
            raise ValueError

        bounds = _Bounds(left, right, min_start, max_start, min_end, max_end)
        return self.__class__(self.l, bounds)

    def update_ends(self, left: int, right: int) -> '_ViewDelegate':
        bounds = self.bounds.update_ends(left, right)
        return self.__class__(self.l, bounds)

    def at(self, location: Location) -> Union[L, LabelIndex[L]]:
        l = self.l
        start = l.index_location(location, self.bounds.left, self.bounds.right + 1)
        end = start
        while end < self.bounds.right and l.locations[end + 1] == location:
            end += 1

        if start == end:
            return l.labels[start]
        else:
            bounds = self.bounds.update_ends(start, end)
            return _View(self.__class__(l, bounds))

    @property
    @abstractmethod
    def first_index(self) -> int:
        ...

    @property
    @abstractmethod
    def last_index(self) -> int:
        ...

    @property
    @abstractmethod
    def ascending(self) -> bool:
        ...

    @abstractmethod
    def next_index(self, index: int) -> int:
        ...

    @abstractmethod
    def reversed(self):
        ...


class _Ascending(_ViewDelegate):
    @property
    def first_index(self) -> int:
        return self.bounds.left

    @property
    def last_index(self) -> int:
        return self.bounds.right

    @property
    def ascending(self) -> bool:
        return True

    def next_index(self, index: int) -> int:
        return self.next_index_ascending(index)

    def reversed(self):
        return _Descending(self.l, self.bounds)


class _Descending(_ViewDelegate):
    @property
    def first_index(self) -> int:
        return self.bounds.right

    @property
    def last_index(self) -> int:
        return self.bounds.left

    @property
    def ascending(self) -> bool:
        return True

    def next_index(self, index: int) -> int:
        return self.next_index_descending(index)

    def reversed(self):
        return _Descending(self.l, self.bounds)


def _start_and_end(x: Union[Label, int], end: Optional[int] = None) -> Location:
    if end is None:
        x = _location(x)
        start = x.start_index
        end = x.end_index
    else:
        if not isinstance(x, int):
            raise TypeError
        if not isinstance(end, int):
            raise TypeError
        start = x
        if end is None:
            end = float('inf')
    return Location(start, end)


def _location(x):
    if isinstance(x, Label):
        x = x.location
    if not isinstance(x, Location):
        raise TypeError
    return x


class _View(LabelIndex):
    def __init__(self, delegate: _ViewDelegate):
        self._d = delegate  # internal directional delegate

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        d = self._d
        if isinstance(idx, int):
            return d[idx]
        elif isinstance(idx, slice):
            if idx.step != 1:
                raise IndexError("Step values other than 1 are not supported.")
            return _View(d.update_ends(d.indices[idx.start], d.indices[idx.stop - 1]))
        else:
            raise TypeError("Index must be int or slice.")

    def at(self, label: Union[Label, Location], default=...) -> Union[L, 'LabelIndex[L]']:
        location = _location(label)
        try:
            return self._d.at(location)
        except ValueError as e:
            if default is not ...:
                return default
            raise e

    def __contains__(self, item: Any) -> bool:
        try:
            self.index(item)
            return True
        except ValueError:
            return False

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self) -> Iterator[L]:
        return iter(self._d)

    def __reversed__(self) -> 'LabelIndex[L]':
        return self._d.reversed()

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        d = self._d
        if not isinstance(x, Label) or not d.bounds.contains(x):
            raise ValueError
        return d.l.index(x, d.bounds.left, d.bounds.right + 1)

    def count(self, x: Any) -> int:
        d = self._d
        try:
            i = self.index(x)
        except ValueError:
            return 0
        count = 1
        while i < d.bounds.right and d.l.locations[i + 1] == x.location:
            i += 1
            label = d.l.labels[d.indices[i]]
            if d.bounds.contains(label) and label == x:
                count += 1
        return count

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        d = self._d
        try:
            new_delegate = d.update_bounds(max_start=start, min_end=end)
            return _View(new_delegate)
        except ValueError:
            return EMPTY_INDEX

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        d = self._d
        try:
            new_delegate = d.update_bounds(min_start=start, max_start=end - 1, min_end=start,
                                           max_end=end)
            return _View(new_delegate)
        except ValueError:
            return EMPTY_INDEX

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        d = self._d
        try:
            new_delegate = d.update_bounds(min_start=start, max_start=end - 1)
            return _View(new_delegate)
        except ValueError:
            return EMPTY_INDEX

    def ascending(self) -> 'LabelIndex[L]':
        d = self._d
        if not d.ascending:
            return _View(_Ascending(d.l, d.bounds))
        else:
            return self

    def descending(self) -> 'LabelIndex[L]':
        d = self._d
        if d.ascending:
            return _View(_Descending(d.l, d.bounds))
        else:
            return self


def create_standard_label_index(labels):
    labels = sorted(labels, key=attrgetter('location'))
    return _LabelIndex(_SortedLabels(labels))
