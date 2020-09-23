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
"""Internal implementation of a standard non-distinct label index."""
from abc import ABCMeta, abstractmethod
from bisect import bisect_left, bisect_right
from operator import attrgetter
from typing import Union, Optional, Any, Iterator, List, TypeVar, Sequence, Generic, Callable, \
    TYPE_CHECKING

from mtap.data import _labels

if TYPE_CHECKING:
    from mtap import data

L = TypeVar('L', bound='data.Label')


class LabelIndex(Sequence[L], Generic[L]):
    """An immutable :obj:`~typing.Sequence` of labels ordered by their location in text. By default
    sorts by ascending `start_index` and then by ascending `end_index`.
    """

    @property
    @abstractmethod
    def distinct(self) -> bool:
        """bool: Whether this label index is distinct, i.e. all of the labels in it are
            non-overlapping.
        """
        ...

    @property
    @abstractmethod
    def adapter(self) -> Optional['data.ProtoLabelAdapter']:
        ...

    @abstractmethod
    def filter(self, fn: Callable[['data.Label'], bool]) -> 'data.LabelIndex[L]':
        """Filters the label index according to a filter function.

        This function is less efficient for filtering based on indices than
        :func:`~LabelIndex.inside`, :func:`~LabelIndex.covering`, etc., which use a binary search
        method on the sorted index.

        Args:
            fn (~typing.Callable[[Label], bool]): A filter function, returns ``true`` if the label
                should be included, ``false`` if it should not be included

        Returns:
            LabelIndex: A view of this label index.
        """
        ...

    @abstractmethod
    def at(self,
           x: Union['data.Label', 'data.Location', float],
           end: Optional[float] = None) -> 'data.LabelIndex[L]':
        """Returns the labels at the specified location in text.

        Args:
            x (~typing.Union[Label, Location, float]): A label or location, or start index if `end`
                is specified.
            end (~typing.Optional[float]): The exclusive end index of the location in text if it has
                not been specified by a label.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 10, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(6, 20, x=3)])
            >>> index.at(0, 10)
            label_index([GenericLabel(0, 10, x=1), GenericLabel(0, 10, x=2)], distinct=False)
        """
        ...

    @abstractmethod
    def covering(self,
                 x: Union['data.Label', 'data.Location', float],
                 end: Optional[float] = None) -> 'data.LabelIndex[L]':
        """A label index containing all labels that cover / contain the specified location in text.

        Args:
            x (~typing.Union[~'data.Label', ~'data.Location', float]): A label or location, or start
                index if `end` is specified.
            end (~typing.Optional[float]): The exclusive end index of the location in text if it has
                not been specified by a label.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.covering(5, 10)
            label_index([GenericLabel(0, 10, x=2), GenericLabel(5, 10, x=3), GenericLabel(5, 15, x=5)], distinct=False)

        """
        ...

    @abstractmethod
    def inside(self,
               x: Union['data.Label', 'data.Location', float],
               end: Optional[float] = None) -> 'data.LabelIndex[L]':
        """A label index containing all labels that are inside the specified location in text.

        Args:
            x (~typing.Union[~'data.Label', ~'data.Location', float]): A label or location, or start
                index if `end` is specified.
            end (~typing.Optional[float]): The exclusive end index of the location in text if it has
                not been specified by a label.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.inside(5, 10)
            label_index([GenericLabel(5, 10, x=3), GenericLabel(7, 10, x=4)], distinct=False)
        """
        ...

    @abstractmethod
    def beginning_inside(self,
                         x: Union['data.Label', 'data.Location', float],
                         end: Optional[float] = None) -> 'data.LabelIndex[L]':
        """A label index containing all labels whose begin index is inside the specified location
        in text.

        Args:
            x (~typing.Union[~'data.Label', ~'data.Location', float]): A label or location, or start
                index if `end` is specified.
            end (~typing.Optional[float]): The exclusive end index of the location in text if it has
                not been specified by a label.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.beginning_inside(6, 11)
            label_index([GenericLabel(7, 10, x=4), GenericLabel(10, 15, x=6)], distinct=False)
        """
        ...

    @abstractmethod
    def overlapping(self,
                    x: Union['data.Label', 'data.Location', float],
                    end: Optional[float] = None) -> 'data.LabelIndex[L]':
        """Returns all labels that overlap the specified location in text.

        Args:
            x (~typing.Union[~'data.Label', ~'data.Location', float]): A label or location, or start
                index if `end` is specified.
            end (~typing.Optional[float]): The exclusive end index of the location in text if it has
                not been specified by a label.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.overlapping(6, 10)
            label_index([GenericLabel(0, 10, x=2), GenericLabel(5, 10, x=3), GenericLabel(5, 15, x=5), GenericLabel(7, 10, x=4)], distinct=False)


        """
        ...

    def before(self, x: Union['data.Label', 'data.Location', float]) -> 'data.LabelIndex[L]':
        """A label index containing all labels that are before a label's location in text or
        an index in text.

        Args:
            x (~typing.Union[~'data.Label', ~'data.Location', float]): A label or location whose
                `start_index` will be used, or a float index in text.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.before(6)
            label_index([GenericLabel(0, 5, x=1)], distinct=False)
        """
        try:
            index = x.start_index
        except AttributeError:
            index = x
        return self.inside(0, index)

    def after(self, x: Union['data.Label', 'data.Location', float]) -> 'data.LabelIndex[L]':
        """A label index containing all labels that are after a label's location in text
        or an index in text.

        Args:
            x (~typing.Union[Label, Location, float]): A label or location whose `end_index` will
                be used, or a float index in text.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.after(6)
            label_index([GenericLabel(7, 10, x=4), GenericLabel(10, 15, x=6)], distinct=False)

        """
        try:
            index = x.end_index
        except AttributeError:
            index = x
        return self.inside(index, float('inf'))

    @abstractmethod
    def ascending(self) -> 'data.LabelIndex[L]':
        """This label index sorted according to ascending start and end index.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index == index.ascending()
            True
        """
        ...

    @abstractmethod
    def descending(self) -> 'data.LabelIndex[L]':
        """This label index sorted according to descending start index and ascending end index.

        Returns:
            LabelIndex: A view of this label index.

        Examples:
            >>> from mtap import label_index, label
            >>> index = label_index([label(0, 5, x=1),
            ...                      label(0, 10, x=2),
            ...                      label(5, 10, x=3),
            ...                      label(7, 10, x=4),
            ...                      label(5, 15, x=5),
            ...                      label(10, 15, x=6)])
            >>> index.descending()
            label_index([GenericLabel(10, 15, x=6), GenericLabel(7, 10, x=4), GenericLabel(5, 15, x=5), GenericLabel(5, 10, x=3), GenericLabel(0, 10, x=2), GenericLabel(0, 5, x=1)], distinct=False)
        """
        ...


def label_index(labels: List[L],
                distinct: bool = False,
                adapter: Optional['data.ProtoLabelAdapter'] = None) -> LabelIndex[L]:
    """Creates a label index from labels.

    Args:
        labels (~typing.List[L]): Zero or more labels to create a label index from.
        distinct (bool): Whether the label index is distinct or not.
        adapter (~data.ProtoLabelAdapter): The label adapter for these labels.

    Returns:
        ~data.LabelIndex: The newly created label index.

    Examples:
        >>> from mtap import label_index, label
        >>> index = label_index([label(0, 5, x=1),
        ...                      label(0, 10, x=2),
        ...                      label(5, 10, x=3),
        ...                      label(7, 10, x=4),
        ...                      label(5, 15, x=5),
        ...                      label(10, 15, x=6)])
        >>> index
        label_index([GenericLabel(0, 5, x=1), GenericLabel(0, 10, x=2), GenericLabel(5, 10, x=3), GenericLabel(5, 15, x=5), GenericLabel(7, 10, x=4), GenericLabel(10, 15, x=6)], distinct=False)

    """
    labels = sorted(labels, key=attrgetter('location'))
    return presorted_label_index(labels, distinct, adapter=adapter)


def presorted_label_index(labels: List[L],
                          distinct: bool = False,
                          adapter: Optional['data.ProtoLabelAdapter'] = None) -> LabelIndex[L]:
    if len(labels) == 0:
        return _Empty(distinct, adapter)
    return _LabelIndex(distinct, _Ascending(labels), adapter=adapter)


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

    def filter(self, fn: Callable[['data.Label'], bool]) -> '_View':
        filtered_indices = list(self._filter_fn(fn))
        if len(filtered_indices) == 0:
            raise ValueError
        return self.__class__(self._labels, filtered_indices)

    def _filter(self,
                min_start: float = 0,
                max_start: float = float('inf'),
                min_end: float = 0,
                max_end: float = float('inf')) -> Iterator[int]:
        try:
            left = self._index_lt(_labels.Location(min_start, min_end)) + 1
        except ValueError:
            left = 0

        for i in range(left, len(self._indices)):
            location = self.locations[i]
            if location.start_index > max_start:
                break
            if min_end <= location.end_index <= max_end:
                yield self._indices[i]

    def _filter_fn(self, fn: Callable[['data.Label'], bool]) -> Iterator[int]:
        for index in self._indices:
            label = self._labels[index]
            if fn(label):
                yield index

    def _first_index_location(self,
                              location: 'data.Location',
                              from_index: int = 0,
                              to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self.locations)
        i = bisect_left(self.locations, location, from_index, to_index)

        if i != to_index and self.locations[i] == location:
            return i
        raise ValueError

    def _last_index_location(self,
                             location: 'data.Location',
                             from_index: int = 0,
                             to_index: int = ...):
        if to_index is ...:
            to_index = len(self.locations)
        i = bisect_right(self.locations, location, from_index, to_index)

        if i > from_index and self.locations[i - 1] == location:
            return i - 1
        raise ValueError

    def _index_lt(self,
                  location: 'data.Location',
                  from_index: int = 0,
                  to_index: int = ...) -> int:
        if to_index is ...:
            to_index = len(self.locations)

        i = bisect_left(self.locations, location, from_index, to_index)
        if i > from_index:
            return i - 1
        raise ValueError

    @abstractmethod
    def __getitem__(self, idx) -> Union['data.Label', '_View']:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator['data.Label']:
        ...

    @abstractmethod
    def reversed(self):
        ...

    @abstractmethod
    def index_location(self,
                       location: 'data.Location',
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        ...


class _Ascending(_View):
    def __getitem__(self, idx) -> Union['data.Label', '_View']:
        if isinstance(idx, int):
            return self._labels[self._indices[idx]]
        elif isinstance(idx, slice):
            return _Ascending(self._labels, self._indices[idx])

    def __iter__(self) -> Iterator['data.Label']:
        for idx in self._indices:
            yield self._labels[idx]

    def reversed(self):
        return _Descending(self._labels, self._indices)

    def index_location(self,
                       location: 'data.Location',
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        return self._first_index_location(location, from_index, to_index)


class _Descending(_View):
    def _reverse_index(self, i: int = None):
        return -(i + 1)

    def __getitem__(self, idx) -> Union['data.Label', '_View']:
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

    def __iter__(self) -> Iterator['data.Label']:
        for i in range(len(self._indices)):
            yield self._labels[self._indices[self._reverse_index(i)]]

    def reversed(self):
        return _Ascending(self._labels, self._indices)

    def index_location(self,
                       location: 'data.Location',
                       from_index: int = 0,
                       to_index: int = ...) -> int:
        index_location = self._last_index_location(location, from_index, to_index)
        return self._reverse_index(index_location)


def _start_and_end(x: Union['data.Label', float], end: Optional[float] = None) -> 'data.Location':
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
    return _labels.Location(start, end)


def _location(x):
    if isinstance(x, _labels.Label):
        x = x.location
    if not isinstance(x, _labels.Location):
        raise TypeError
    return x


class _LabelIndex(LabelIndex[L]):
    def __init__(self, distinct: bool,
                 view: _View,
                 ascending: bool = True,
                 reversed_index: '_LabelIndex[L]' = None,
                 adapter: Optional['data.ProtoLabelAdapter'] = None):
        self._distinct = distinct
        self._view = view
        self._ascending = ascending
        self._adapter = adapter
        if reversed_index is not None:
            self.__reversed = reversed_index

    @property
    def distinct(self) -> bool:
        return self._distinct

    @property
    def adapter(self) -> 'data.ProtoLabelAdapter[L]':
        return self._adapter

    @adapter.setter
    def adapter(self, value: 'data.ProtoLabelAdapter[L]'):
        self._adapter = value

    def filter(self, fn: Callable[['data.Label'], bool]) -> 'data.LabelIndex[L]':
        return self._filtered_or_empty(fn)

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

    def __getitem__(self, idx: Union[int, slice]) -> Union[L, 'data.LabelIndex[L]']:
        if isinstance(idx, int):
            return self._view[idx]
        elif isinstance(idx, slice):
            return _LabelIndex(self.distinct, self._view[idx], adapter=self.adapter)
        else:
            raise TypeError("Index must be int or slice.")

    def at(self, x, end=None):
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(min_start=start, max_start=start, min_end=end, max_end=end)

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

    def __reversed__(self) -> Iterator[L]:
        return iter(self._reversed)

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        if not isinstance(x, _labels.Label):
            raise ValueError
        for i in range(self._view.index_location(x.location), len(self._view)):
            if self._view[i] == x:
                return i
        raise ValueError

    def count(self, x: Any) -> int:
        if not isinstance(x, _labels.Label):
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

    def covering(self,
                 x: Union['data.Label', float],
                 end: Optional[float] = None) -> 'data.LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(max_start=start, min_end=end)

    def overlapping(self,
                    x: Union['data.Label', float],
                    end: Optional[float] = None) -> 'data.LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(max_start=end - 1, min_end=start + 1)

    def inside(self,
               x: Union['data.Label', float],
               end: Optional[float] = None) -> 'data.LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(start, end - 1, start, end)

    def beginning_inside(self,
                         x: Union['data.Label', float],
                         end: Optional[float] = None) -> 'data.LabelIndex[L]':
        start, end = _start_and_end(x, end)
        return self._bounded_or_empty(min_start=start, max_start=end - 1)

    def ascending(self) -> 'data.LabelIndex[L]':
        if self._ascending:
            return self
        else:
            return self._reversed

    def descending(self) -> 'data.LabelIndex[L]':
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
            return _Empty(self.distinct, self.adapter)
        return _LabelIndex(self.distinct, bounded_view, adapter=self.adapter)

    def _filtered_or_empty(self, fn: Callable[['data.Label'], bool]):
        try:
            filtered_view = self._view.filter(fn)
        except ValueError:
            return _Empty(self.distinct, self.adapter)
        return _LabelIndex(self.distinct, filtered_view, adapter=self.adapter)


class _Empty(LabelIndex):
    @property
    def adapter(self) -> Optional['data.ProtoLabelAdapter']:
        return self._adapter

    def __init__(self, distinct, adapter=None):
        self._distinct = distinct
        self._adapter = adapter

    @property
    def distinct(self) -> bool:
        return self._distinct

    def __getitem__(self, idx):
        raise IndexError

    def filter(self, fn: Callable[['data.Label'], bool]) -> 'data.LabelIndex[L]':
        return self

    def at(self,
           x: Union['data.Label', 'data.Location', float],
           end: Optional[float] = None) -> 'data.LabelIndex[L]':
        return self

    def __len__(self) -> int:
        return 0

    def __contains__(self, item: Any) -> bool:
        return False

    def __iter__(self) -> Iterator[L]:
        return iter([])

    def __reversed__(self) -> 'data.LabelIndex[L]':
        return self

    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        raise ValueError

    def count(self, x: Any) -> int:
        return 0

    def covering(self,
                 x: Union['data.Label', float],
                 end: Optional[float] = None) -> 'data.LabelIndex[L]':
        return self

    def inside(self,
               x: Union['data.Label', float],
               end: Optional[float] = None) -> 'data.LabelIndex[L]':
        return self

    def overlapping(self,
                    x: Union['data.Label', float],
                    end: Optional[float] = None) -> 'data.LabelIndex[L]':
        return self

    def beginning_inside(self,
                         x: Union['data.Label', float],
                         end: Optional[float] = None) -> 'data.LabelIndex[L]':
        return self

    def ascending(self) -> 'data.LabelIndex[L]':
        return self

    def descending(self) -> 'data.LabelIndex[L]':
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
