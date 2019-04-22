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
from typing import Union, Optional, Any, Iterator

from nlpnewt.base import Label, L
from .base import LabelIndex


class _LabelIndex(LabelIndex):
    """

    """
    def __init__(self, labels):
        self.labels = labels
        self.locations = [label.location for label in labels]

    @property
    def distinct(self):
        return False

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        pass

    def __len__(self) -> int:
        pass

    def __contains__(self, item: Any):
        pass

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
