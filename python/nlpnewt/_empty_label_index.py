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
"""Internal labels functionality."""
from typing import Union, TypeVar, Any, Iterator, Optional

from .base import LabelIndex, Label, Location

L = TypeVar('L', bound=Label)


class _Empty(LabelIndex):
    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        raise IndexError

    def at(self, label: Union[Label, Location], default=...) -> Union[L, 'LabelIndex[L]']:
        if default is not ...:
            return default
        raise ValueError

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


INSTANCE = _Empty()