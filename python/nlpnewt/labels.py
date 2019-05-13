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
from typing import TypeVar, NamedTuple, Any, Mapping, Iterator, Sequence


class Location(NamedTuple):
    """A location in text.

    Used to perform comparison of labels based on their locations.
    """
    start_index: float
    end_index: float

    def covers(self, other):
        return self.start_index <= other.start_index and self.end_index >= other.end_index

Location.start_index.__doc__ = "int or float: The start index inclusive of the location in text."
Location.end_index.__doc__ = "int or float: The end index exclusive of the location in text."


class Label(ABC):
    """An abstract base class for a label of attributes on text.

    Attributes
    ==========
    start_index: int
        The index of the first character of the text covered by this label.
    end_index: int
        The index after the last character of the text covered by this label.
    location: Location
        A tuple of (start_index, end_index) used to perform sorting and
        comparison first based on start_index, then based on end_index.
    """

    @property
    @abstractmethod
    def start_index(self) -> int:
        ...

    @start_index.setter
    @abstractmethod
    def start_index(self, value: int):
        ...

    @property
    @abstractmethod
    def end_index(self) -> int:
        ...

    @end_index.setter
    @abstractmethod
    def end_index(self, value: int):
        ...

    @property
    def location(self) -> Location:
        return Location(self.start_index, self.end_index)

    def get_covered_text(self, text: str):
        """Retrieves the slice of text from `start_index` to `end_index`.

        Parameters
        ----------
        text: str
            The text to retrieve covered text from.

        Returns
        -------
        str
            Substring slice of the text.

        Examples
        --------
        >>> label = labeler(0, 9)
        >>> label.get_covered_text("The quick brown fox jumped over the lazy dog.")
        "The quick"

        >>> label = labeler(0, 9)
        >>> "The quick brown fox jumped over the lazy dog."[label.start_index:label.end_index]
        "The quick"
        """
        return text[self.start_index:self.end_index]


L = TypeVar('L', bound=Label)


class GenericLabel(Label, Mapping[str, Any]):
    """Default implementation of the Label class which uses a dictionary to store attributes.

    Will be suitable for the majority of use cases for labels.

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
        for v in kwargs.values():
            _check_type(v)
        self.__dict__['fields'] = dict(kwargs)
        self.fields['start_index'] = start_index
        self.fields['end_index'] = end_index

    @property
    def start_index(self):
        return self.fields['start_index']

    @property
    def end_index(self):
        return self.fields['end_index']

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
        _check_type(value, [self])
        self.__dict__['fields'][key] = value

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
