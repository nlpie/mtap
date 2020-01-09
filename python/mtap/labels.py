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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from typing import TypeVar, NamedTuple, Any, Mapping, Iterator, Sequence, Union, Optional

if TYPE_CHECKING:
    from mtap.events import Document


class Location(NamedTuple('Location', [('start_index', float), ('end_index', float)])):
    """A location in text, a tuple of (`start_index`, `end_index`).

    Used to perform comparison of labels based on their locations.

    Args:
        start_index (float):
            The start index inclusive of the location in text.
        end_index (float);
            The end index exclusive of the location in text.

    Attributes:
        start_index (float):
            The start index inclusive of the location in text.
        end_index (float);
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


class Label(ABC):
    """An abstract base class for a label of attributes on text.
    """

    @property
    @abstractmethod
    def document(self) -> 'Document':
        """Document: The parent document this label appears on."""
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


L = TypeVar('L', bound=Label)


class GenericLabel(Label, Mapping[str, Any]):
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

    def __init__(self, start_index: int, end_index: int, *, document: Optional['Document'] = None,
                 **kwargs):
        for v in kwargs.values():
            _check_type(v)
        self.__dict__['_document'] = document
        for key in kwargs.keys():
            if self._is_reserved(key):
                raise ValueError("The key '{}' is a reserved key.".format(key))
        self.__dict__['fields'] = dict(kwargs)
        self.fields['start_index'] = start_index
        self.fields['end_index'] = end_index

    def _is_reserved(self, key):
        return key in self.__dict__ or key in vars(GenericLabel) or key in vars(Label)

    @property
    def document(self) -> 'Document':
        return self._document

    @document.setter
    def document(self, value: 'Document'):
        ...  # This is handled by setattr and will not be  called, it's just here for type checking.

    @property
    def start_index(self):
        return int(self.fields['start_index'])

    @property
    def end_index(self):
        return int(self.fields['end_index'])

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        return self.fields[item]

    def __setattr__(self, key, value):
        if key == 'document':
            self.__dict__['_document'] = value
            return
        if self._is_reserved(key):
            raise ValueError('The key "{}" is a reserved key.'.format(key))
        _check_type(value, [self])
        self.fields[key] = value

    def __eq__(self, other):
        if not isinstance(other, GenericLabel):
            return False
        return self.fields == other.fields

    def __repr__(self):
        return ("GenericLabel(".format()
                + ", ".join([repr(self.fields['start_index']),
                             repr(self.fields['end_index'])] + ["{}={}".format(k, repr(v))
                                                                for k, v in self.fields.items() if
                                                                k not in (
                                                                    'start_index', 'end_index')])
                + ")")

    def __getitem__(self, k: str) -> Any:
        return self.fields[k]

    def __len__(self) -> int:
        return len(self.fields)

    def __iter__(self) -> Iterator[str]:
        return iter(self.fields)


def label(start_index: int,
          end_index: int,
          *, document: Optional['Document'] = None,
          **kwargs) -> GenericLabel:
    """An alias for :class:`GenericLabel`.

    Args:
        start_index (int): The index of the first character in text to be included in the label.
        end_index (int): The index after the last character in text to be included in the label.

    Keyword Args:
        document (~typing.Optional[Document]): The parent document of the label. This will be
            automatically set if a the label is created via labeler.
        **kwargs : Arbitrary, any other fields that should be added to the label, values must be
            json-serializable.

    """
    return GenericLabel(start_index, end_index, document=document, **kwargs)


def _check_type(o: Any, parents=None):
    if parents is None:
        parents = [o]
    if isinstance(o, (str, float, bool, int)) or o is None:
        return
    elif isinstance(o, Mapping):
        for v in o.values():
            if v in parents:
                raise ValueError('Recursive loop')
            _check_type(v, parents + [v])
    elif isinstance(o, Sequence):
        for v in o:
            if v in parents:
                raise ValueError('Recursive loop')
            _check_type(v, parents + [v])
    else:
        raise TypeError('Unrecognized type')
