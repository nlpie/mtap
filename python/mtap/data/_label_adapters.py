#  Copyright 2020 Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Any, Optional, Sequence, TypeVar

import typing

import mtap._structs as _structs
import mtap.data._label_indices as _label_indices
import mtap.data._labels as _labels

if typing.TYPE_CHECKING:
    import mtap
    import mtap.api.v1.events_pb2 as events_pb2
    import mtap.data as data

L = TypeVar('L', bound='data.Label')


class ProtoLabelAdapter(ABC, Generic[L]):
    """Responsible for marshalling and unmarshalling of label objects to and from proto messages.
    """

    @abstractmethod
    def create_label(self, *args, **kwargs) -> L:
        """Called by labelers to create labels.

        Should include the positional arguments `start_index` and `end_index`, because those are
        required properties of labels.

        Args:
            args: Arbitrary args used to create the label.
            kwargs: Arbitrary keyword args used to create the label.

        Returns:
            Label: An object of the label type.
        """
        ...

    @abstractmethod
    def create_index_from_response(
            self,
            response: 'events_pb2.GetLabelsResponse'
    ) -> 'data.LabelIndex[L]':
        """Creates a LabelIndex from the response from an events service.

        Args:
            response (mtap.api.v1.events_pb2.GetLabelsResponse): The response protobuf message from
                the events service.

        Returns:
            LabelIndex[L]: A label index containing all the labels from the events service.
        """
        ...

    @abstractmethod
    def create_index(self, labels: Iterable[L]):
        """Creates a LabelIndex from an iterable of label objects.

        Args:
            labels (~typing.Iterable[L]): Labels to put in index.

        Returns:
            LabelIndex[L]: A label index containing all of the labels in the list.
        """
        ...

    @abstractmethod
    def add_to_message(self, labels: List[L], request: 'events_pb2.AddLabelsRequest'):
        """Adds a list of labels to a request to the event service to add labels.

        Args:
            labels (Iterable[L]): The list of labels that need to be sent to the server.
            request (mtap.api.v1.events_pb2.AddLabelsRequest): The request proto message to add the
                labels to.
        """
        ...

    @abstractmethod
    def pack(self, index: 'data.LabelIndex[L]', *, include_label_text: bool = False) -> Any:
        """Prepares to serialize a label index by transforming the label index into a representation
        that can be dumped to json, yml, pickle, etc.

        Args:
            index: The index itself.
            include_label_text:
                Whether to include the label's text in the serialized representation
                (for informative reasons).

        Returns:
            A dictionary representation of the label index.

        """
        ...

    @abstractmethod
    def unpack(self,
               packed: Any,
               label_index_name: str,
               *, document: Optional['mtap.Document'] = None) -> 'data.LabelIndex[L]':
        """Takes a packed, serializable object and turns it into a full label index.

        Args:
            packed (Any): The packed representation.
            label_index_name (str): The index name of the label index.
            document (Document): The document this label index occurs on.

        Returns:
            LabelIndex[L]: The label index.

        """
        ...

    def store_references(self, labels: Sequence[L]):
        """Take all the references for the labels and turn them into static references.

        Args:
             labels (Sequence[L]): The labels to store the references on.
        """
        ...


class _GenericLabelAdapter(ProtoLabelAdapter['mtap.GenericLabel']):
    def __init__(self, distinct):
        self.distinct = distinct

    def create_label(self, *args, **kwargs):
        return _labels.GenericLabel(*args, **kwargs)

    def create_index(self, labels: List[L]):
        return _label_indices.label_index(labels, self.distinct, adapter=self)

    def create_index_from_response(self, response):
        generic_labels = response.generic_labels
        labels = []
        for label_message in generic_labels.labels:
            fields = {}
            _structs.copy_struct_to_dict(label_message.fields, fields)
            reference_field_ids = {}
            _structs.copy_struct_to_dict(label_message.reference_ids, reference_field_ids)
            generic_label = _labels.GenericLabel(label_message.start_index, label_message.end_index,
                                                 identifier=label_message.identifier, fields=fields,
                                                 reference_field_ids=reference_field_ids)
            labels.append(generic_label)

        return _label_indices.presorted_label_index(labels, generic_labels.is_distinct, adapter=self)

    def add_to_message(self, labels: List['mtap.GenericLabel'], request):
        generic_labels = request.generic_labels
        for label in labels:
            label_message = generic_labels.labels.add()
            label_message.identifier = label.identifier
            label_message.start_index = label.start_index
            label_message.end_index = label.end_index
            _structs.copy_dict_to_struct(label.fields, label_message.fields, [label])
            _structs.copy_dict_to_struct(label.reference_field_ids, label_message.reference_ids,
                                         [label])

    def pack(self,
             index: 'data.LabelIndex[mtap.GenericLabel]',
             *, include_label_text: bool = False) -> Any:
        d = {
            'labels': [_label_to_dict(label, include_label_text) for label in index],
            'distinct': index.distinct
        }
        return d

    def unpack(self, packed: Any,
               label_index_name: str,
               *, document: Optional['mtap.Document'] = None) -> 'data.LabelIndex[L]':
        return _label_indices.label_index(
            [_dict_to_label(d, label_index_name, document) for d in packed['labels']],
            distinct=packed['distinct'], adapter=self
        )

    def store_references(self, labels: Sequence['mtap.GenericLabel']):
        for label in labels:
            for k, v in label.reference_cache.items():
                if k not in label.reference_field_ids:
                    label.reference_field_ids[k] = _convert_to_references(v)


def _convert_to_references(o):
    if o is None:
        return o
    if isinstance(o, _labels.Label):
        ref = '{}:{}'.format(o.label_index_name, o.identifier)
        return ref
    if isinstance(o, typing.Mapping):
        rep = {}
        for k, v in o.items():
            rep[k] = _convert_to_references(v)
        return rep
    if isinstance(o, Sequence):
        rep = [_convert_to_references(v) for v in o]
        return rep


def _label_to_dict(label, include_label_text):
    d = {'start_index': label.start_index,
         'end_index': label.end_index,
         'identifier': label.identifier,
         'fields': label.fields,
         'reference_ids': label.reference_field_ids}
    if include_label_text:
        d['_text'] = label.text
    return d


def _dict_to_label(d, label_index_name, document):
    return _labels.GenericLabel(d['start_index'], d['end_index'], identifier=d['identifier'],
                                fields=d['fields'], reference_field_ids=d['reference_ids'],
                                label_index_name=label_index_name, document=document)


GENERIC_ADAPTER = _GenericLabelAdapter(False)

DISTINCT_GENERIC_ADAPTER = _GenericLabelAdapter(True)
