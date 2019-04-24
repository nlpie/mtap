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
from typing import Callable, Dict, TypeVar

import nlpnewt
from . import constants, _utils
from ._distinct_label_index import create_distinct_label_index
from ._empty_label_index import INSTANCE as EMPTY_INDEX
from ._standard_label_index import create_standard_label_index
from .base import Label, LabelIndex, ProtoLabelAdapter

__all__ = (['distinct_label_index',
            'standard_label_index',
            'GenericLabel',
            'proto_label_adapter',
            'get_label_adapter'])

L = TypeVar('L', bound=Label)


def distinct_label_index(*labels: L) -> LabelIndex[L]:
    """Creates a distinct label index from the labels.

    Parameters
    ----------
    labels: *Label
        Zero or more labels to create a label index from.

    Returns
    -------
    nlpnewt.base.LabelIndex

    """
    if len(labels) == 0:
        return EMPTY_INDEX
    return create_distinct_label_index(labels)


def standard_label_index(*labels: L) -> LabelIndex[L]:
    """Creates a standard label index from the labels.

    Parameters
    ----------
    labels: *Label
        Zero or more labels to create a standard label index from.

    Returns
    -------
    nlpnewt.base.LabelIndex

    """
    if len(labels) == 0:
        return EMPTY_INDEX
    return create_standard_label_index(labels)


class GenericLabel(Label):
    """Default implementation of the Label class which uses a dictionary to store attributes.

    Will be suitable for the majority of use cases for labels.

    Attributes
    ----------
    start_index
    end_index
    *: Any
        Other attributes dynamically set on the label.

    Parameters
    ----------
    start_index : int, required
        The index of the first character in text to be included in the label.
    end_index : int, required
        The index after the last character in text to be included in the label.
    kwargs : dynamic
        Any other fields that should be added to the label.


    Examples
    --------
    >>> pos_tag = pos_tag_labeler(0, 5)
    >>> pos_tag.tag = 'NNS'
    >>> pos_tag.tag
    'NNS'

    >>> pos_tag2 = pos_tag_labeler(6, 10, tag='VB')
    >>> pos_tag2.tag
    'VB'

    """

    def __init__(self, start_index: int, end_index: int, **kwargs):
        self.__dict__['fields'] = dict(kwargs)
        self.fields['start_index'] = start_index
        self.fields['end_index'] = end_index

    @property
    def start_index(self):
        return self.fields['start_index']

    @start_index.setter
    def start_index(self, value):
        self.fields['start_index'] = value

    @property
    def end_index(self):
        return self.fields['end_index']

    @end_index.setter
    def end_index(self, value):
        self.fields['end_index'] = value

    def __getattr__(self, item):
        fields = self.__dict__['fields']
        if item == 'fields':
            return fields
        else:
            return fields[item]

    def __setattr__(self, key, value):
        """Sets the value of a field on the label.

        Parameters
        ----------
        key: str
            Name of the string.
        value: json serialization compliant
            Some kind of value, must be able to be serialized to json.

        """
        self.__dict__['_fields'][key] = value

    def __eq__(self, other):
        if not isinstance(other, GenericLabel):
            return False
        return self.fields == other.fields

    def __hash__(self):
        return hash((self.__class__, self.fields))

    def __repr__(self):
        return f"GenericLabel({str(self.fields)})"


def proto_label_adapter(label_type_id: str):
    """Registers a :obj:`ProtoLabelAdapter` for a specific identifier.

    When that id is referenced in the document :func:`~Document.get_labeler`
    and  :func:`~Document.get_label_index`.

    Parameters
    ----------
    label_type_id: hashable
        This can be anything as long as it is hashable, good choices are strings or the label types
        themselves if they are concrete classes.

    Returns
    -------
    decorator
        Decorator object which invokes the callable to create the label adapter.

    Examples
    --------
    >>> @nlpnewt.proto_label_adapter("example.Sentence")
    >>> class SentenceAdapter(nlpnewt.ProtoLabelAdapter):
    >>>    # ... implementation of the ProtoLabelAdapter for sentences.

    >>> with document.get_labeler("sentences", "example.Sentence") as labeler
    >>>     # add labels

    >>> label_index = document.get_label_index("sentences", "example.Sentence")
    >>>     # do something with labels
    """

    def decorator(func: Callable[[], ProtoLabelAdapter]):
        _label_adapters[label_type_id] = func()
        return func

    return decorator


class _GenericLabelAdapter(ProtoLabelAdapter):

    def __init__(self, distinct):
        self.distinct = distinct

    def create_label(self, *args, **kwargs):
        return GenericLabel(*args, **kwargs)

    def create_index_from_response(self, response):
        json_labels = response.json_labels
        labels = []
        for label in json_labels.labels:
            d = {}
            _utils.copy_struct_to_dict(label, d)
            generic_label = nlpnewt.GenericLabel(**d)
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

_label_adapters: Dict[str, ProtoLabelAdapter] = {
    constants.DISTINCT_GENERIC_LABEL_ID: distinct_generic_adapter,
    constants.GENERIC_LABEL_ID: generic_adapter
}


def get_label_adapter(label_type_id):
    return _label_adapters[label_type_id]

