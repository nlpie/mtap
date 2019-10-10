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
from abc import ABCMeta, abstractmethod
from bisect import bisect_left, bisect_right
from operator import attrgetter
from typing import Union, Optional, Any, Iterator, List, TypeVar, Sequence, Generic

from mtap.labels import Label, Location

L = TypeVar('L', bound=Label)

__all__ = [
    'LabelIndex',
    'label_index',
    'presorted_label_index'
]


class LabelIndex(Sequence[L], Generic[L]):
    """An immutable sequence of labels ordered by their location in text. By default sorts by
    ascending :func:`Label.start_index` and then by ascending :func:`Label.end_index`.

    See Also
    ========
    Document.get_label_index : Method for getting existing label indices.
    Document.get_labeler : Method for adding new label indexes to documents.
    Labeler : Object for adding new label indices to documents.
    """

    @abstractmethod
    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        """Returns the label at the specified index/slice.

        Parameters
        ----------
        idx : int or slice
            The index of the label to return or a slice of indices to return as a new label index,
            or a label to indicate to indicate a location.

        Returns
        -------
        L or LabelIndex
            Label if a single index, LabelIndex if a slice of indices.

        Examples
        --------
        At index:

        >>> sentences = distinct_label_index(label(0, 10),
        >>>                                  label(11, 40),
        >>>                                  label(41, 60),
        >>>                                  label(61, 90))
        >>> sentence = sentences[0]
        >>> print(sentence)
        GenericLabel{start_index = 0, end_index = 10}



        Slice:

        >>> sentences = distinct_label_index(label(0, 10),
        >>>                                  label(11, 40),
        >>>                                  label(41, 60),
        >>>                                  label(61, 90))
        >>> sentences[:2]
        LabelIndex[GenericLabel{0, 10}, GenericLabel{11, 40}]
        >>> last_two_sentences = [-2:]
        LabelIndex[GenericLabel{41, 60}, GenericLabel{61, 90}]

        """
        ...

    @property
    @abstractmethod
    def distinct(self) -> bool:
        """Whether this label index is distinct, i.e. all of the labels in it are non-overlapping,
        or not distinct.

        Returns
        -------
        bool
            True if distinct, False if not.

        """
        ...

    @abstractmethod
    def at(self, label: Union[Label, Location]) -> 'LabelIndex[L]':
        """Returns the labels at the specified label or location.

        Returns
        -------
        LabelIndex
            A view of this label index.

        Examples
        --------
        >>> concepts = standard_label_index(label(0, 10, x=1),
        >>>                                 label(0, 10, x=2),
        >>>                                 label(6, 20, x=3))
        >>>
        >>> term = label(0, 10)
        >>> concepts.at(term)
        standard_label_index([GenericLabel(0, 10, x=1), GenericLabel(0, 10, x=2)])

        """
        ...

    @abstractmethod
    def __len__(self) -> int:
        """The number of labels in this label index.

        Returns
        -------
        int
            Count of labels in this index.

        Examples
        --------
        >>> len(sentences_index)
        25

        """
        ...

    @abstractmethod
    def __contains__(self, item: Any) -> bool:
        """Checks if the item is a label in this label index.

        Parameters
        ----------
        item: Any

        Returns
        -------
        bool
            True if the item is a label and it is in this label index. False if it is not.

        """
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[L]:
        """An iterator of the label objects in this index.

        Returns
        -------
        typing.Iterator[Label]


        Examples
        --------
        >>> for sentence in sentences_index:
        >>>     # use sentence

        >>> it = iter(sentences_index)
        >>> try:
        >>>     next_sentence = next(it)
        >>> except StopIteration:
        >>>     pass
        """
        ...

    @abstractmethod
    def __reversed__(self) -> 'Iterator[L]':
        """The labels in this label index in reverse order.

        Returns
        -------
        Iterator[L]
            An iterator of the elements in reverse order.
        """
        ...

    @abstractmethod
    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        """The index of the first occurrence of `x` in the label index at or after `start`
        and before `end`.

        Parameters
        ----------
        x: Any
        start: int, optional
            Inclusive start index.
        end: int, optional
            Exclusive end index.

        Returns
        -------
        index: int

        Raises
        ------
        ValueError
            If x is not found in this label index.

        """
        ...

    @abstractmethod
    def count(self, x: Any) -> int:
        """The number of times `x` occurs in the label index.

        Parameters
        ----------
        x: Any

        Returns
        -------
        count: int
            The total number of times that the parameter occurs, or 0 if it doesn't occur.

        """
        ...

    @abstractmethod
    def covering(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        """A label index containing all labels that cover / contain the specified span of text.

        Parameters
        ----------
        x: Label or int
            Either a label whose location specifies the entire span of text, or the start index of
            the span of text.
        end: int, optional
            The exclusive end index of the span of text if it has not been specified by a label.

        Returns
        -------
        LabelIndex[L]
            A view of this label index.

        """
        ...

    @abstractmethod
    def inside(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        """A label index containing all labels that are inside the specified span of text.

        Parameters
        ----------
        x: Label or int
            Either a label whose location specifies the entire span of text, or the start index of
            the span of text.
        end: int, optional
            The exclusive end index of the span of text if it has not been specified by a label.

        Returns
        -------
        LabelIndex[L]
            A view of this label index.
        """
        ...

    @abstractmethod
    def beginning_inside(self,
                         x: Union[Label, float],
                         end: Optional[float] = None) -> 'LabelIndex[L]':
        """A label index containing all labels whose begin index is inside the specified span of
        text.

        Parameters
        ----------
        x: Label or int
            Either a label whose location specifies the entire span of text, or the start index of
            the span of text.
        end: int, optional
            The exclusive end index of the span of text if it has not been specified by a label.

        Returns
        -------
        LabelIndex[L]
            A view of this label index.
        """
        ...

    @abstractmethod
    def overlapping(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        ...

    def before(self, x: Union[Label, float]) -> 'LabelIndex[L]':
        """A label index containing all labels that are before a label's location in text or
        an index in text.

        Parameters
        ----------
        x: Label or int
            Either a label whose begin indicates a text index to use, or the text index itself.

        Returns
        -------
        LabelIndex[L]
            A view of this label index.
        """
        try:
            index = x.start_index
        except AttributeError:
            index = x
        return self.inside(0, index)

    def after(self, x: Union[Label, float]) -> 'LabelIndex[L]':
        """A label index containing all labels that are after a label's location in text
        or an index in text.

        Parameters
        ----------
        x: Label or int
            Either a label whose end indicates a text index to use, or the text index itself.


        Returns
        -------
        LabelIndex[L]
            A view of this label index.
        """
        try:
            index = x.end_index
        except AttributeError:
            index = x
        return self.inside(index, float('inf'))

    @abstractmethod
    def ascending(self) -> 'LabelIndex[L]':
        """This label index sorted according to ascending start and end index.

        Returns
        -------
        LabelIndex[L]
            A view of this label index.
        """
        ...

    @abstractmethod
    def descending(self) -> 'LabelIndex[L]':
        """This label index sorted according to descending start index and ascending end index.

        Returns
        -------
        LabelIndex[L]
            A view of this label index.
        """
        ...


def label_index(labels: List[L], distinct: bool = False) -> LabelIndex[L]:
    """Creates a label index from the labels.

    Parameters
    ----------
    labels: List[L]
        Zero or more labels to create a label index from.
    distinct:

    Returns
    -------
    nlpnewt.base.LabelIndex

    """
    labels = sorted(labels, key=attrgetter('location'))
    return presorted_label_index(labels, distinct)


def presorted_label_index(labels: List[L], distinct: bool = False) -> LabelIndex[L]:
    if len(labels) == 0:
        return EMPTY[distinct]
    return _LabelIndex(distinct, _Ascending(labels))


class _View(metaclass=ABCMeta):
    def __init__(self, labels, indices: Sequence[int] = ...):
        self._labels = labels
        self._indices = range(len(labels)) if indices is ... else indices

    @property
    def locations(self):
        try:
            locations = self._locations
        except AttributeError:
            locations = [self._labels[i].location for i in self._indices]
            self._locations = locations
        return locations

    def __len__(self):
        return len(self._indices)

    def bound(self,
              min_start: float = 0,
              max_start: float = float('inf'),
              min_end: float = 0,
              max_end: float = float('inf')) -> '_View':
        filtered_indices = list(self._filter(min_start, max_start, min_end, max_end))
        if len(filtered_indices) == 0:
            raise ValueError
        return self.__class__(self._labels, filtered_indices)

    def _filter(self,
                min_start: float = 0,
                max_start: float = float('inf'),
                min_end: float = 0,
                max_end: float = float('inf')) -> Iterator[int]:
        try:
            left = self._index_lt(Location(min_start, min_end)) + 1
        except ValueError:
            left = 0

        for i in range(left, len(self._indices)):
            location = self.locations[i]
            if location.start_index > max_start:
                break
            if min_end <= location.end_index <= max_end:
                yield self._indices[i]

    def _first_index_location(self,
                              location: Location,
                              from_index: int = 0,
                              to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self.locations)
        i = bisect_left(self.locations, location, from_index, to_index)

        if i != to_index and self.locations[i] == location:
            return i
        raise ValueError

    def _last_index_location(self,
                             location: Location,
                             from_index: int = 0,
                             to_index: int = ...):
        if to_index is ...:
            to_index = len(self.locations)
        i = bisect_right(self.locations, location, from_index, to_index)

        if i > from_index and self.locations[i - 1] == location:
            return i - 1
        raise ValueError

    def _index_lt(self,
                  location: Location,
                  from_index: int = 0,
                  to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_left(self.locations, location, from_index, to_index)
        if i > from_index:
            return i - 1
        raise ValueError

    @abstractmethod
    def __getitem__(self, idx) -> Union[Label, '_View']:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Label]:
        ...

    @abstractmethod
    def reversed(self):
        ...

    @abstractmethod
    def index_location(self,
                       location: Location,
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        ...


class _Ascending(_View):
    def __getitem__(self, idx) -> Union[Label, '_View']:
        if isinstance(idx, int):
            return self._labels[self._indices[idx]]
        elif isinstance(idx, slice):
            return _Ascending(self._labels, self._indices[idx])

    def __iter__(self) -> Iterator[Label]:
        for idx in self._indices:
            yield self._labels[idx]

    def reversed(self):
        return _Descending(self._labels, self._indices)

    def index_location(self,
                       location: Location,
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        return self._first_index_location(location, from_index, to_index)


class _Descending(_View):
    def _reverse_index(self, i: int = None):
        return -(i + 1)

    def __getitem__(self, idx) -> Union[Label, '_View']:
        if isinstance(idx, int):
            return self._labels[self._indices[self._reverse_index(idx)]]
        elif isinstance(idx, slice):
            start = idx.stop
            if start is not None:
                start = self._reverse_index(idx.stop - 1)
            stop = idx.start
            if stop is not None:
                stop = self._reverse_index(idx.start - 1)
            idx = slice(start, stop, idx.step)
            return _Descending(self._labels, self._indices[idx])

    def __iter__(self) -> Iterator[Label]:
        for i in range(len(self._indices)):
            yield self._labels[self._indices[self._reverse_index(i)]]

    def reversed(self):
        return _Ascending(self._labels, self._indices)

    def index_location(self,
                       location: Location,
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        index_location = self._last_index_location(location, from_index, to_index)
        return self._reverse_index(index_location)


def _start_and_end(x: Union[Label, float], end: Optional[float] = None) -> Location:
    if end is None:
        x = _location(x)
        start = x.start_index
        end = x.end_index
    else:
        if not isinstance(x, int) and not isinstance(x, float):
            raise TypeError
        if not isinstance(end, int) and not isinstance(end, float):
            raise TypeError
        start = x
        if end is None:
            end = float('inf')
    return Location(start, end)


def _location(x):
    if isinstance(x, Label):
        x = x.location
    if not isinstance(x, Location):
        raise TypeError
    return x


class _LabelIndex(LabelIndex[L]):
    def __init__(self, distinct: bool,
                 view: _View,
                 ascending: bool = True,
                 reversed_index: '_LabelIndex[L]' = None):
        self._distinct = distinct
        self._view = view
        self._ascending = ascending
        if reversed_index is not None:
            self.__reversed = reversed_index

    @property
    def distinct(self) -> bool:
        return self._distinct

    @property
    def _reversed(self) -> '_LabelIndex[L]':
        try:
            reversed_label_index = self.__reversed
        except AttributeError:
            reversed_label_index = _LabelIndex(distinct=self.distinct,
                                               view=self._view.reversed(),
                                               ascending=False,
                                               reversed_index=self)
            self.__reversed = reversed_label_index
        return reversed_label_index

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        if isinstance(idx, int):
            return self._view[idx]
        elif isinstance(idx, slice):
            return _LabelIndex(self.distinct, self._view[idx])
        else:
            raise TypeError("Index must be int or slice.")

    def at(self, label: Union[Label, Location]) -> 'LabelIndex[L]':
        location = _location(label)
        return self._bounded_or_empty(min_start=location.start_index,
                                      max_start=location.start_index,
                                      min_end=location.end_index,
                                      max_end=location.end_index)

    def __contains__(self, item: Any) -> bool:
        try:
            self.index(item)
            return True
        except ValueError:
            return False

    def __len__(self) -> int:
        return len(self._view)

    def __iter__(self) -> Iterator[L]:
        return iter(self._view)

    def __reversed__(self) -> 'Iterator[L]':
        return iter(self._reversed)

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        if not isinstance(x, Label):
            raise ValueError
        for i in range(self._view.index_location(x.location), len(self._view)):
            if self._view[i] == x:
                return i
        raise ValueError

    def count(self, x: Any) -> int:
        if not isinstance(x, Label):
            return False
        try:
            i = self._view.index_location(x.location)
        except ValueError:
            return 0
        count = 0
        for label in self._view[i:]:
            if not label.location == x.location:
                break
            if label == x:
                count += 1
        return count

    def covering(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(max_start=start, min_end=end)

    def overlapping(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(max_start=end - 1, min_end=start + 1)

    def inside(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(start, end - 1, start, end)

    def beginning_inside(self, x: Union[Label, float],
                         end: Optional[float] = None) -> 'LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(min_start=start, max_start=end - 1)

    def ascending(self) -> 'LabelIndex[L]':
        if self._ascending:
            return self
        else:
            return self._reversed

    def descending(self) -> 'LabelIndex[L]':
        if not self._ascending:
            return self
        else:
            return self._reversed

    def __repr__(self):
        return ("label_index(["
                + ", ".join(repr(l) for l in self)
                + "], distinct={})".format(self.distinct))

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for s, o in zip(self, other):
            if s != o:
                return False
        return True

    def _bounded_or_empty(self,
                          min_start: float = 0,
                          max_start: float = float('inf'),
                          min_end: float = 0,
                          max_end: float = float('inf')):
        try:
            bounded_view = self._view.bound(min_start=min_start, max_start=max_start,
                                            min_end=min_end, max_end=max_end)
        except ValueError:
            return EMPTY[self.distinct]
        return _LabelIndex(self.distinct, bounded_view)


class _Empty(LabelIndex):
    def __init__(self, distinct):
        self._distinct = distinct

    @property
    def distinct(self) -> bool:
        return self._distinct

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'LabelIndex[L]']:
        raise IndexError

    def at(self, label: Union[Label, Location]) -> Union[L, 'LabelIndex[L]']:
        return self

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

    def covering(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        return self

    def inside(self,
               x: Union[Label, float],
               end: Optional[float] = None) -> 'LabelIndex[L]':
        return self

    def overlapping(self, x: Union[Label, float], end: Optional[float] = None) -> 'LabelIndex[L]':
        return self

    def beginning_inside(self,
                         x: Union[Label, float],
                         end: Optional[float] = None) -> 'LabelIndex[L]':
        return self

    def ascending(self) -> 'LabelIndex[L]':
        return self

    def descending(self) -> 'LabelIndex[L]':
        return self

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for s, o in zip(self, other):
            if s != o:
                return False
        return True

    def __repr__(self):
        return "label_index([], distinct={})".format(self.distinct)


EMPTY = {
    True: _Empty(True),
    False: _Empty(False)
}
