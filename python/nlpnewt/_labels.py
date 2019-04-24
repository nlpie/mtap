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
from typing import Union, Optional, Any, Iterator

from .base import Label, L, Location, LabelIndex
from . import _utils, base, constants
from ._distinct_label_index import create_distinct_label_index
from ._standard_label_index import create_standard_label_index


class _GenericLabelAdapter(base.ProtoLabelAdapter):

    def __init__(self, distinct):
        self.distinct = distinct

    def create_label(self, *args, **kwargs):
        return base.GenericLabel(*args, **kwargs)

    def create_index_from_response(self, response):
        json_labels = response.json_labels
        labels = []
        for label in json_labels.labels:
            d = {}
            _utils.copy_struct_to_dict(label, d)
            generic_label = base.GenericLabel(**d)
            labels.append(generic_label)

        return (create_distinct_label_index(labels)
                if self.distinct
                else create_standard_label_index(labels))

    def add_to_message(self, labels, request):
        json_labels = request.json_labels
        for label in labels:
            _utils.copy_dict_to_struct(label.fields, json_labels.labels.add(), [label])


generic_adapter = _GenericLabelAdapter(False)

distinct_generic_adapter = _GenericLabelAdapter(True)

_label_adapters = {
    constants.DISTINCT_GENERIC_LABEL_ID: distinct_generic_adapter,
    constants.GENERIC_LABEL_ID: generic_adapter
}


def get_label_adapter(label_type_id):
    return _label_adapters[label_type_id]


def register_proto_label_adapter(label_type_id, label_adapter):
    _label_adapters[label_type_id] = label_adapter


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


EMPTY_INDEX = _Empty()
