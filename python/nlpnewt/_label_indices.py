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
from abc import ABCMeta
from bisect import bisect_left, bisect_right
from operator import attrgetter
from typing import Union, Optional, Any, Iterator, List, Tuple, TypeVar, \
    Iterable

from .base import Label, Location, LabelIndex

L = TypeVar('L', bound=Label)


def label_index(labels: List[L], distinct: bool = False) -> LabelIndex[L]:
    """Creates a label index from the labels.

    Parameters
    ----------
    labels: List[L]
        Zero or more labels to create a label index from.
    distinct:

    Returns
    -------
    nlpnewt.base.LabelIndex

    """
    labels = sorted(labels, key=attrgetter('location'))
    return internal_label_index(labels, distinct)


def internal_label_index(labels: List[L], distinct: bool = False) -> LabelIndex[L]:
    if len(labels) == 0:
        return EMPTY[distinct]
    return _LabelIndex(distinct, _View(labels))


class _View(metaclass=ABCMeta):
    def __init__(self, labels, indices: Iterable[int] = ..., locations: List[Location] = ...):
        self._labels = labels
        if indices is ...:
            indices = range(len(labels))
        self._indices = indices
        if locations is ...:
            locations = [labels[i].location for i in indices]
        self._locations = locations

    def create_indices_and_locations(self):
        return self._indices

    def __getitem__(self, idx) -> Union[Label, '_View']:
        if isinstance(idx, int):
            return self._labels[self._indices[idx]]
        elif isinstance(idx, slice):
            return _View(self._labels, self._indices[idx])

    def __iter__(self) -> Iterator[Label]:
        for idx in self._indices:
            yield self._labels[idx]

    def __len__(self):
        return len(self._indices)

    def index_location(self,
                       location: Location,
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self._locations)
        i = bisect_left(self._locations, location, from_index, to_index)

        if i != to_index and self._locations[i] == location:
            return i
        raise ValueError

    def last_index_location(self,
                            location: Location,
                            from_index: int = 0,
                            to_index: int = ...):
        if to_index is ...:
            to_index = len(self._locations)
        i = bisect_right(self._locations, location, from_index, to_index)

        if i != to_index and self._locations[i] == location:
            return i
        raise ValueError

    def index_lt(self,
                 location: Location,
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self._locations)

        i = bisect_left(self._locations, location, from_index, to_index)
        if i > from_index:
            return i - 1
        raise ValueError

    def index_le(self,
                 location: Location,
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self._locations)

        i = bisect_right(self._locations, location, from_index, to_index)
        if i > from_index:
            return i - 1
        raise ValueError

    def index_gt(self,
                 location: Location,
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if isinstance(location, Label):
            location = location.location
        if to_index is ...:
            to_index = len(self._locations)

        i = bisect_right(self._locations, location, from_index, to_index)
        if i != to_index:
            return self._indices[i]
        raise ValueError

    def index_ge(self,
                 location: Location,
                 from_index: int = 0,
                 to_index: int = ...) -> int:
        if isinstance(location, Label):
            location = location.location
        if to_index is ...:
            to_index = len(self._locations)

        i = bisect_left(self._locations, location, from_index, to_index)
        if i != to_index:
            return self._indices[i]
        raise ValueError

    def filter(self,
               min_start: float = 0,
               max_start: float = float('inf'),
               min_end: float = 0,
               max_end: float = float('inf')) -> Iterator[int]:
        left = self.index_lt(Location(min_start, min_end)) + 1

        if left == len(self):
            raise ValueError

        for i in self._indices[left:]:
            label = self._labels[i]
            if label.start_index > max_start:
                break
            if min_end <= label.end_index <= max_end:
                yield i

    def bound(self,
              min_start: float = 0,
              max_start: float = float('inf'),
              min_end: float = 0,
              max_end: float = float('inf')) -> '_View':
        return _View(self._labels, [i for i in self.filter(min_start, max_start, min_end, max_end)])


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


def _check_indices(arr: List, start: int, end: int = ...) -> Union[int, Tuple[int, int]]:
    if start is None:
        start = 0
    if start < 0:
        start = len(arr) - 1 + start
    if end is None:
        end = len(arr)
    if end is not ...:
        if end < 0:
            end = len(arr) + end
        if end < start:
            raise IndexError("end: {} < start: {}".format(end, start))
    if end is not None:
        return start, end
    else:
        return start


class _LabelIndex(LabelIndex[L]):
    def __init__(self, distinct: bool, view: _View):
        self._distinct = distinct
        self._view = view

    @property
    def distinct(self) -> bool:
        return self._distinct

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        if isinstance(idx, int):
            return self._view[idx]
        elif isinstance(idx, slice):
            return _LabelIndex(self.distinct, self._view[idx])
        else:
            raise TypeError("Index must be int or slice.")

    def at(self, label: Union[Label, Location]) -> Union[L, 'LabelIndex[L]']:
        location = _location(label)
        try:
            updated_view = self._view.bound(min_start=location.start_index, max_start=location.start_index,
                                 min_end=location.end_index, max_end=location.end_index)
        except ValueError:
            return EMPTY[self.distinct]
        return _LabelIndex(self.distinct, updated_view)

    def __contains__(self, item: Any) -> bool:
        try:
            self.index(item)
            return True
        except ValueError:
            return False

    def __len__(self) -> int:
        return len(self._view)

    def __iter__(self) -> Iterator[L]:
        return iter(self._view)

    def __reversed__(self) -> 'LabelIndex[L]':
        return self._view.reversed()

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        if not isinstance(x, Label):
            raise ValueError
        try:
            i = self._view.index_location(x.location)
        except ValueError:
            return 0

    def count(self, x: Any) -> int:
        if not isinstance(x, Label):
            return False
        try:
            i = self._view.index_location(x.location)
        except ValueError:
            return 0
        count = 1
        for label in self._view[i + 1:]:
            if not label.location == x.location:
                break
            if label == x:
                count += 1
        return count

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        d = self._view
        try:
            return _LabelIndex(self.distinct, self._view.bound(max_start=start, min_end=end))
        except ValueError:
            return EMPTY[self.distinct]

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        try:
            return _LabelIndex(self.distinct, self._view.bound(min_start=start,
                                                               max_start=end - 1,
                                                               min_end=start,
                                                               max_end=end))
        except ValueError:
            return EMPTY[self.distinct]

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        try:
            new_delegate = self._view.update_bounds(min_start=start, max_start=end - 1)
            return _LabelIndex(self.distinct, new_delegate)
        except ValueError:
            return EMPTY[self.distinct]

    def ascending(self) -> 'LabelIndex[L]':
        return _LabelIndex(self.distinct, self._view.ascending())

    def descending(self) -> 'LabelIndex[L]':
        d = self._view
        return _LabelIndex(self.distinct, self._view.descending())

    def __repr__(self):
        return ("label_index(["
                + ", ".join(repr(l) for l in self)
                + "], distinct={})".format(self.distinct))

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for s, o in zip(self, other):
            if s != o:
                return False
        return True


class _Empty(LabelIndex):
    def __init__(self, distinct):
        self._distinct = distinct

    @property
    def distinct(self) -> bool:
        return self._distinct

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        raise IndexError

    def at(self, label: Union[Label, Location]) -> Union[L, 'LabelIndex[L]']:
        return self

    def __len__(self) -> int:
        return 0

    def __contains__(self, item: Any) -> bool:
        return False

    def __iter__(self) -> Iterator[L]:
        return iter([])

    def __reversed__(self) -> 'LabelIndex[L]':
        return self

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        raise ValueError

    def count(self, x: Any) -> int:
        return 0

    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        return self

    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        return self

    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        return self

    def ascending(self) -> 'LabelIndex[L]':
        return self

    def descending(self) -> 'LabelIndex[L]':
        return self

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for s, o in zip(self, other):
            if s != o:
                return False
        return True

    def __repr__(self):
        return ("label_index([], distinct={})".format(self.distinct))


EMPTY = {
    True: _Empty(True),
    False: _Empty(False)
}
