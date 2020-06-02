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
"""Labels functionality."""
import threading
from abc import ABC, abstractmethod, ABCMeta
from queue import Queue
from typing import TYPE_CHECKING, List, Tuple, Set
from typing import TypeVar, NamedTuple, Any, Mapping, Sequence, Union, Optional

if TYPE_CHECKING:
    from mtap.events import Document


class Location(NamedTuple('Location', [('start_index', float), ('end_index', float)])):
    """A location in text, a tuple of (`start_index`, `end_index`).

    Used to perform comparison of labels based on their locations.

    Args:
        start_index (float):
            The start index inclusive of the location in text.
        end_index (float):
            The end index exclusive of the location in text.

    Attributes:
        start_index (float):
            The start index inclusive of the location in text.
        end_index (float):
            The end index exclusive of the location in text.
    """

    def covers(self, other: Union['Location', 'Label']):
        """Whether the span of text covered by this label completely overlaps the span of text
        covered by the ``other`` label or location.

        Args:
            other (~typing.Union[Location, Label]): A location or label to compare against.

        Returns:
            bool: ``True`` if `other` is completely overlapped/covered ``False`` otherwise.
        """
        return self.start_index <= other.start_index and self.end_index >= other.end_index

    def relative_to(self, location: Union['Location', 'Label', int]) -> 'Location':
        """Creates a location relative to the the same origin as ``location`` and makes it relative
        to ``location``.

        Args:
            location (int or Location or Label): A location to relativize this location to.

        Returns:
            Location

        Examples:
            >>> sentence = Location(10, 20)
            >>> token = Location(10, 15)
            >>> token.relative_to(sentence)
            Location(start_index=0, end_index=5)

        """
        try:
            start_index = location.start_index
        except AttributeError:
            start_index = location
        if not isinstance(start_index, int):
            raise ValueError('location must be Label, Location, or an int value')
        return Location(self.start_index - start_index, self.end_index - start_index)

    def offset_by(self, location: Union['Location', 'Label', int]) -> 'Location':
        """Creates a location by offsetting this location by an integer or the ``start_index`` of a
        location / label. Derelativizes this location.

        Args:
            location (int or Location or Label): A location to offset this location by.

        Returns:
            Location

        Examples:
            >>> sentence = Location(10, 20)
            >>> token_in_sentence = Location(0, 5)
            >>> token_in_sentence.offset_by(sentence)
            Location(start_index=10, end_index=15)

        """
        try:
            start_index = location.start_index
        except AttributeError:
            start_index = location
        if not isinstance(start_index, int):
            raise ValueError('location must be Label, Location, or an int value')
        return Location(self.start_index + start_index, self.end_index + start_index)


class Label(ABC, metaclass=ABCMeta):
    """An abstract base class for a label of attributes on text.
    """

    @property
    @abstractmethod
    def document(self) -> 'Document':
        """Document: The parent document this label appears on."""
        ...

    @document.setter
    @abstractmethod
    def document(self, value: 'Document'):
        """Sets the label's document, this will automatically be done when the label is created
        via a Document (i.e. get_label_index) or added to a document (i.e. via labeler or add_labels).
        """
        ...

    @property
    @abstractmethod
    def label_index_name(self) -> str:
        """The label index this label appears on."""
        ...

    @label_index_name.setter
    @abstractmethod
    def label_index_name(self, value: str):
        """Sets the name for the label index this label appears on. Will automatically be called
        when a label is added to a document via labeler or add_labels."""
        ...

    @property
    @abstractmethod
    def identifier(self) -> int:
        """The index of the label within its label index."""
        ...

    @identifier.setter
    @abstractmethod
    def identifier(self, value: int):
        """The index of the label within its label index. Labels will automatically be assigned
        this when added to a document via labeler or add_labels."""
        ...

    @property
    @abstractmethod
    def start_index(self) -> int:
        """int: The index of the first character of the text covered by this label.
        """
        ...

    @start_index.setter
    @abstractmethod
    def start_index(self, value: int):
        ...

    @property
    @abstractmethod
    def end_index(self) -> int:
        """int: The index after the last character of the text covered by this label.
        """
        ...

    @end_index.setter
    @abstractmethod
    def end_index(self, value: int):
        ...

    @property
    def location(self) -> Location:
        """Location: A tuple of (start_index, end_index) used to perform sorting and
            comparison first based on start_index, then based on end_index.
        """
        return Location(self.start_index, self.end_index)

    @property
    def text(self):
        """str: The slice of document text covered by this label. Will retrieve from events server
        if it is not cached locally.
        """
        return self.document.text[self.start_index:self.end_index]

    @abstractmethod
    def shallow_fields_equal(self, other) -> bool:
        """Tests if the fields on this label and locations of references are the same as another
        label.

        Args:
            other: The other label to test.

        Returns:
            True if all of the fields are equal and the references ar

        """
        pass

    @abstractmethod
    def collect_floating_references(self, s):
        pass


L = TypeVar('L', bound=Label)

_repr_local = threading.local()


class GenericLabel(Label):
    """Default implementation of the Label class which uses a dictionary to store attributes.

    Will be suitable for the majority of use cases for labels.

    Args:
        start_index (int): The index of the first character in text to be included in the label.
        end_index (int): The index after the last character in text to be included in the label.

    Keyword Args:
        document (~typing.Optional[Document]): The parent document of the label. This will be
            automatically set if a the label is created via labeler.
        **kwargs : Arbitrary, any other fields that should be added to the label, values must be
            json-serializable.

    Examples:
        >>> pos_tag = pos_tag_labeler(0, 5)
        >>> pos_tag.tag = 'NNS'
        >>> pos_tag.tag
        'NNS'

        >>> pos_tag2 = pos_tag_labeler(6, 10, tag='VB')
        >>> pos_tag2.tag
        'VB'
    """

    def __init__(self, start_index: int, end_index: int, *,
                 identifier: Optional[int] = None,
                 document: Optional['Document'] = None,
                 label_index_name: Optional['str'] = None,
                 fields: Optional[dict] = None,
                 reference_field_ids: Optional[dict] = None,
                 **kwargs):
        self._document = document
        self._label_index_name = label_index_name
        self._identifier = identifier
        self._start_index = int(start_index)
        self._end_index = int(end_index)
        if fields is None:
            self.fields = {}
        else:
            self.fields = fields
        if reference_field_ids is None:
            self.reference_field_ids = {}
        else:
            self.reference_field_ids = reference_field_ids
        self.reference_cache = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def document(self) -> 'Document':
        return self._document

    @document.setter
    def document(self, document: 'Document'):
        self._document = document

    @property
    def label_index_name(self) -> str:
        return self._label_index_name

    @label_index_name.setter
    def label_index_name(self, value: str):
        self._label_index_name = value

    @property
    def identifier(self) -> int:
        return self._identifier

    @identifier.setter
    def identifier(self, value: int):
        self._identifier = value

    @property
    def start_index(self) -> int:
        return self._start_index

    @start_index.setter
    def start_index(self, start_index: int):
        self._start_index = start_index

    @property
    def end_index(self) -> int:
        return self._end_index

    @end_index.setter
    def end_index(self, end_index: int):
        self._end_index = end_index

    def _is_reserved(self, key):
        return key in self.__dict__.keys() or key in vars(GenericLabel) or key in vars(Label)

    def __getattr__(self, item):
        try:
            return self.fields[item]
        except KeyError:
            pass
        try:
            return self.reference_cache[item]
        except KeyError:
            pass
        try:
            ref_value = self.reference_field_ids[item]
            self.reference_cache[item] = _dereference(ref_value, self.document)
            return self.reference_cache[item]
        except KeyError:
            raise AttributeError('Key "{}" not in fields, reference cache, or reference ids.'
                                 .format(item))

    def __setattr__(self, key, value):
        if key in ('document', 'label_index_name', 'identifier', 'start_index', 'end_index',
                   '_document', '_label_index_name', '_identifier', '_start_index', '_end_index',
                   'fields', 'reference_field_ids', 'reference_cache'):
            object.__setattr__(self, key, value)
            return
        if self._is_reserved(key):
            raise ValueError('The key "{}" is a reserved key.'.format(key))
        is_ref = _is_referential(value, [id(self)])
        if is_ref:
            self.reference_cache[key] = value
        else:
            self.fields[key] = value

    def __eq__(self, other):
        if not isinstance(other, GenericLabel):
            return False
        if other is self:
            return True
        if not self.location == other.location:
            return False
        return self.shallow_fields_equal(other)

    def shallow_fields_equal(self, other):
        if not self.fields == other.fields:
            return False
        refs = set(self.reference_field_ids.keys()).union(self.reference_cache.keys())
        other_refs = set(other.reference_field_ids.keys()).union(other.reference_cache.keys())
        if not refs == other_refs:
            return False
        for k in refs:
            try:
                if self.reference_field_ids[k] == other.reference_field_ids[k]:
                    continue
            except KeyError:
                pass
            self_k = getattr(self, k)
            other_k = getattr(other, k)
            if not _collect_locations(self_k) == _collect_locations(other_k):
                return False

        return True

    def __repr__(self):
        try:
            stack = _repr_local.stack
        except AttributeError:
            stack = set()
            _repr_local.stack = stack

        if id(self) in stack:
            return 'GenericLabel(...)'
        stack.add(id(self))
        attributes = [repr(self.start_index), repr(self.end_index)]
        for k, v in self.fields.items():
            attributes.append("{}={}".format(k, repr(v)))
        for k, v in self.reference_cache.items():
            attributes.append("{}={}".format(k, repr(v)))
        for k, v in self.reference_field_ids.items():
            if k not in self.reference_cache:
                attributes.append("{}=ref:{}".format(k, repr(v)))
        stack.remove(id(self))
        return "GenericLabel(".format() + ", ".join(attributes) + ")"

    def collect_floating_references(self, s):
        queue = Queue()
        for k, v in self.reference_cache.items():
            if v is not None:
                queue.put(v)
        while not queue.empty():
            o = queue.get_nowait()
            if isinstance(o, Label):
                if o.identifier is None:
                    s.add(id(o))
            elif isinstance(o, Mapping):
                for _, v in o.items():
                    if v is not None:
                        queue.put(v)
            elif isinstance(o, Sequence):
                for v in o:
                    if v is not None:
                        queue.put(v)


def label(start_index: int,
          end_index: int,
          *, document: Optional['Document'] = None,
          **kwargs) -> GenericLabel:
    """An alias for :class:`GenericLabel`.

    Args:
        start_index (int): The index of the first character in text to be included in the label.
        end_index (int): The index after the last character in text to be included in the label.
        document (~typing.Optional[Document]): The parent document of the label. This will be
            automatically set if a the label is created via labeler.
        **kwargs : Arbitrary, any other fields that should be added to the label, values must be
            json-serializable.

    """
    return GenericLabel(start_index, end_index, document=document, **kwargs)


def _staticize(labels: Sequence['Label'],
               document: 'Document',
               label_index_name: str) -> Tuple[List['Label'], Set[int]]:
    """Prepares a label index for serialization by finalizing sort order and setting label
    identifiers.

    Args:
        labels (~typing.Sequence[GenericLabel]): The labels in a label index.

    Returns:
        List['GenericLabel']: The labels sorted by position.
        Set[int]: A set of labels which a referenced by labels in this index.

    """
    labels = sorted(labels, key=lambda x: x.location)
    waiting_on = set()
    for i, l in enumerate(labels):
        l.document = document
        l.identifier = i
        l.label_index_name = label_index_name
    for l in labels:
        l.collect_floating_references(waiting_on)
    return labels, waiting_on


def _is_referential(o: Any, parents=None) -> bool:
    if parents is None:
        parents = [id(o)]
    if isinstance(o, (str, float, bool, int)) or o is None:
        return False
    elif isinstance(o, Label):
        return True
    elif isinstance(o, Mapping):
        map_is_ref = None
        for v in o.values():
            if id(v) in parents:
                raise ValueError('Recursive loop')
            x = _is_referential(v, parents + [id(v)])
            if map_is_ref is None:
                map_is_ref = x
            elif x != map_is_ref:
                raise TypeError('Label dictionaries cannot have mixes of references to labels'
                                'and primitive types.')
        return map_is_ref
    elif isinstance(o, Sequence):
        seq_is_ref = None
        for v in o:
            if id(v) in parents:
                raise ValueError('Recursive loop')
            x = _is_referential(v, parents + [id(v)])
            if seq_is_ref is None:
                seq_is_ref = x
            elif x != seq_is_ref:
                raise TypeError('Label lists cannot have mixes of references to labels'
                                'and primitive types.')
        return seq_is_ref
    else:
        raise TypeError('Unrecognized type')


def _dereference(o: Any, document: 'Document') -> Any:
    if o is None:
        return o
    if isinstance(o, str):
        label_index_name, label_id = o.split(':')
        label_index = document.labels[label_index_name]
        label_ = label_index[int(label_id)]
        return label_
    if isinstance(o, Mapping):
        replacement = {}
        for k, v in o.items():
            replacement[k] = _dereference(v, document)
        return replacement
    if isinstance(o, Sequence):
        replacement = [_dereference(v, document) for v in o]
        return replacement


def _collect_locations(o):
    if o is None:
        return None
    if isinstance(o, Label):
        return o.location
    if isinstance(o, Mapping):
        return {k: _collect_locations(v) for k, v in o.items()}
    if isinstance(o, Sequence):
        return [_collect_locations(v) for v in o]
