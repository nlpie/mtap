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
import typing

from nlpnewt.base import Label, LabelIndex
from . import base


def _covering_index(labels, label, from_index=..., to_index=...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(labels)

    pass


def _at_location(labels, label, from_index=..., to_index=...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(labels)

    pass


def _index_of(labels, label, from_index=..., to_index=...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(labels)

    pass


def _higher_index(labels, label, from_index=..., to_index=...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(labels)

    pass


def _lower_index(labels, label, from_index=..., to_index=...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(labels)

    pass


def _lower_start(labels, label, from_index=..., to_index=...):
    if from_index is ...:
        from_index = 0
    if to_index is ...:
        to_index = len(labels)

    pass


L = typing.TypeVar('L', bound=base.Label)


class _DistinctLabelIndex(LabelIndex):

    def __init__(self, labels):
        self.labels = labels

    @property
    def distinct(self):
        return True

    def __getitem__(self, idx: typing.Union[int, slice, Label]) -> typing.Union[L, LabelIndex[L]]:
        pass

    def __len__(self) -> int:
        pass

    def __contains__(self, item: typing.Any):
        pass

    def __iter__(self) -> typing.Iterator[L]:
        pass

    def __reversed__(self) -> LabelIndex[L]:
        pass

    def index(self, x: typing.Any, start: int = ..., end: int = ...) -> int:
        pass

    def count(self, x: typing.Any) -> int:
        pass

    def covering(self,
                 x: typing.Union[Label, int],
                 end: typing.Optional[int] = None) -> LabelIndex[L]:
        pass

    def inside(self,
               x: typing.Union[Label, int],
               end: typing.Optional[int] = None) -> LabelIndex[L]:
        pass

    def beginning_inside(self,
                         x: typing.Union[Label, int],
                         end: typing.Optional[int] = None) -> LabelIndex[L]:
        pass

    def ascending(self) -> LabelIndex[L]:
        pass

    def descending(self) -> LabelIndex[L]:
        pass


class _View(base.LabelIndex, metaclass=abc.ABCMeta):
    def __init__(self, labels, left, right):
        self.labels = labels
        self.left = left
        self.right = right

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
    pass


def create_distinct_index(labels):
    labels = sorted(labels, key=lambda x: (x.start_index, x.end_index))
    return _DistinctLabelIndex(labels)
