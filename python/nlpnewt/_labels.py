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

from abc import ABCMeta

import nlpnewt
from nlpnewt import _utils


def create_distinct_index(labels):
    return _DistinctLabelIndexBase(labels)


def create_standard_index(labels):
    return _StandardLabelIndexBase(labels)


class _LabelIndexBase(nlpnewt.LabelIndex, metaclass=ABCMeta):
    def __init__(self, labels):
        self._labels = labels
        self._begins = None
        self._ends = None

    @property
    def begins(self):
        if self._begins is None:
            self._begins = [label.begin for label in self._labels]
        return self._begins

    def __getitem__(self, item):
        return self._labels[item]

    def __len__(self):
        return len(self._labels)

    def __iter__(self):
        return iter(self._labels)


class _DistinctLabelIndexBase(_LabelIndexBase):
    def __init__(self, labels):
        super(_DistinctLabelIndexBase, self).__init__(labels)

    @property
    def distinct(self):
        return True


class _StandardLabelIndexBase(_LabelIndexBase):
    def __init__(self, labels):
        super(_StandardLabelIndexBase, self).__init__(labels)

    @property
    def distinct(self):
        return False


class _GenericLabelAdapter(nlpnewt.ProtoLabelAdapter):

    def __init__(self, distinct):
        self.distinct = distinct

    def create_label(self, *args, **kwargs):
        return nlpnewt.GenericLabel(*args, **kwargs)

    def create_index_from_response(self, response):
        json_labels = response.json_labels
        labels = []
        for label in json_labels.labels:
            d = {}
            _utils.copy_struct_to_dict(label, d)
            generic_label = nlpnewt.GenericLabel(**d)
            labels.append(generic_label)

        return (create_distinct_index(labels)
                if self.distinct
                else create_standard_index(labels))

    def add_to_message(self, labels, request):
        json_labels = request.json_labels
        for label in labels:
            _utils.copy_dict_to_struct(label.fields, json_labels.labels.add(), [label])


generic_adapter = _GenericLabelAdapter(False)
distinct_generic_adapter = _GenericLabelAdapter(True)
