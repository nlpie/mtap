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
"""Internal implementation of a distinct label index."""
import abc
from bisect import bisect_right, bisect_left
from typing import TypeVar, Union, Any, Iterator, Optional

from . import base
from .base import Label, LabelIndex, Location

L = TypeVar('L', bound=Label)


class _DistinctLabelIndex(LabelIndex):
    def __init__(self, labels):
        self.labels = labels
        self.starts = [label.start_index for label in labels]

    @property
    def distinct(self):
        return True

    def __getitem__(self, key: Union[int, slice, Label, Location]) -> Union[L, LabelIndex[L]]:
        if isinstance(key, int):
            return self.labels[key]
        elif isinstance(key, slice):
            if key.step is not None and key.step is not 1:
                raise IndexError("Only step values of 1 are supported.")
            return _AscendingView(self.labels, key.start, key.stop - 1)
        elif isinstance(key, Label):
            key = key.location

        if isinstance(key, Location):
            return _at_location(self, key)
        else:
            raise TypeError("Key must be int, slice, Label, or Location.")

    def __len__(self) -> int:
        return len(self.labels)

    def __contains__(self, item: Any):
        pass

    def __iter__(self) -> Iterator[L]:
        pass

    def __reversed__(self) -> LabelIndex[L]:
        pass

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        if start is ...:
            start = 0
        if end is ...:
            end = len(self.labels)
        if not isinstance(x, Label):
            raise ValueError("Not found")

        return _index_of(self.labels, x, start, end)

    def count(self, x: Any) -> int:
        pass

    def covering(self,
                 x: Union[Label, int],
                 end: Optional[int] = None) -> LabelIndex[L]:
        pass

    def inside(self,
               x: Union[Label, int],
               end: Optional[int] = None) -> LabelIndex[L]:
        pass

    def beginning_inside(self,
                         x: Union[Label, int],
                         end: Optional[int] = None) -> LabelIndex[L]:
        pass

    def ascending(self) -> LabelIndex[L]:
        pass

    def descending(self) -> LabelIndex[L]:
        pass


def _covering_index(index: _DistinctLabelIndex,
                    location: Location,
                    from_index: int = ...,
                    to_index: int = ...):
    if len(index) == 0:
        return -1
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(index)

    i = bisect_right(index.starts, location.start_index, from_index, to_index)

    if i in range(from_index + 1, to_index + 1) and index.labels[i].location.covers(location):
        return i - 1
    raise ValueError


def _at_location(index: _DistinctLabelIndex,
                 location: Location,
                 from_index: int = ...,
                 to_index: int = ...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(index)

    i = bisect_right(index.starts, location.start_index, from_index, to_index)

    if i in range(from_index + 1, to_index + 1) and index.labels[i].location == location:
        return index[i - 1]
    else:
        return None


def _index_of(index: _DistinctLabelIndex,
              label: Label,
              from_index: int = ...,
              to_index: int = ...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(index)

    i = bisect_right(index.starts, label.start_index, from_index, to_index)

    if i in range(from_index + 1, to_index + 1) and index.labels[i] == label:
        return i - 1
    raise ValueError


def _higher_index(index: _DistinctLabelIndex,
                  text_index: int,
                  from_index: int = ...,
                  to_index: int = ...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(index)

    i = bisect_left(index.starts, text_index, from_index, to_index)

    if i in range(from_index, to_index):
        return i
    raise ValueError


def _lower_index(index: _DistinctLabelIndex,
                 text_index: int,
                 from_index: int = ...,
                 to_index: int = ...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(index)

    i = bisect_left(index.starts, text_index, from_index, to_index)

    if i and index.labels[i - 1].end_index > text_index:
        i = i - 1

    if i in range(from_index + 1, to_index + 1):
        return i - 1
    raise ValueError


def _lower_start(index: _DistinctLabelIndex,
                 text_index: int,
                 from_index: int = ...,
                 to_index: int = ...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(index)

    i = bisect_left(index.starts, text_index, from_index, to_index)

    if i in range(from_index + 1, to_index + 1):
        return i - 1
    raise ValueError


class _View(base.LabelIndex, metaclass=abc.ABCMeta):
    def __init__(self, parent, left=None, right=None):
        self.parent = parent
        self.left = left or 0
        self.right = right if right is not None else len(parent)

    @property
    @abc.abstractmethod
    def first_index(self):
        ...

    @property
    @abc.abstractmethod
    def last_index(self):
        ...

    @abc.abstractmethod
    def update_ends(self, left, right):
        ...


class _AscendingView(_View):
    def __init__(self, labels, left, right):
        super().__init__(labels, left, right)

    pass

class _DescendingView(_View):
    def __init__(self, labels, left, right):
        super().__init__(labels, left, right)

    pass


def create_distinct_index(labels):
    labels = sorted(labels, key=lambda x: x.location)
    return _DistinctLabelIndex(labels)
