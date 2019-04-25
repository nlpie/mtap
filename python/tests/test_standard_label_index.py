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

import pytest

from nlpnewt import GenericLabel
from nlpnewt._standard_label_index import _LabelIndex, _SortedLabels, create_standard_label_index

tested = _LabelIndex(_SortedLabels([
    GenericLabel(0, 5, i=0),
    GenericLabel(0, 7, i=1),
    GenericLabel(2, 6, i=2),
    GenericLabel(6, 7, i=3),
    GenericLabel(6, 8, i=4),
    GenericLabel(9, 10, i=5),
    GenericLabel(9, 13, i=6),
    GenericLabel(9, 13, i=7)
]))

empty = create_standard_label_index([])


def test_create_sort():
    sorted = create_standard_label_index([
        GenericLabel(9, 13, i=6),
        GenericLabel(0, 7, i=1),
        GenericLabel(6, 8, i=4),
        GenericLabel(6, 7, i=3),
        GenericLabel(9, 10, i=5),
        GenericLabel(9, 13, i=7),
        GenericLabel(0, 5, i=0),
        GenericLabel(2, 6, i=2),
    ])

    assert sorted == tested


def test_len():
    assert len(tested) == 8


def test_empty_len():
    assert len(empty) == 0


def test_covering():
    covering = tested.covering(2, 4)
    assert list(covering) == [GenericLabel(0, 5, i=0),
                              GenericLabel(0, 7, i=1),
                              GenericLabel(2, 6, i=2)]


def test_covering_empty():
    covering = tested.covering(4, 10)
    assert list(covering) == []


def test_empty_covering():
    covering = tested.covering(4, 10)
    assert list(covering) == []


def test_inside():
    inside = tested.inside(1, 8)
    assert list(inside) == [GenericLabel(2, 6, i=2),
                            GenericLabel(6, 7, i=3),
                            GenericLabel(6, 8, i=4)]


def test_inside_before():
    inside = tested.inside(0, 3)
    assert list(inside) == []


def test_inside_after():
    inside = tested.inside(15, 20)
    assert list(inside) == []


def test_empty_inside():
    inside = empty.inside(0, 5)
    assert list(inside) == []
    
    
def test_inside_many():
    tested = _LabelIndex(_SortedLabels([
        GenericLabel(0, 3),
        GenericLabel(0, 3),
        GenericLabel(0, 3),
        GenericLabel(0, 3),
        GenericLabel(0, 3),
        GenericLabel(0, 3),
        GenericLabel(0, 3),
        GenericLabel(2, 5),
        GenericLabel(2, 5),
        GenericLabel(2, 5),
        GenericLabel(2, 5),
        GenericLabel(2, 5),
        GenericLabel(2, 5),
        GenericLabel(2, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 6),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
        GenericLabel(6, 10),
    ]))
    inside = tested.inside(3, 6)
    assert list(inside) == [
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(3, 5),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
        GenericLabel(5, 6),
    ]


def test_begins_inside():
    inside = tested.beginning_inside(1, 9)
    assert list(inside) == [
        GenericLabel(2, 6, i=2),
        GenericLabel(6, 7, i=3),
        GenericLabel(6, 8, i=4),
    ]


def test_begins_inside_empty():
    inside = tested.beginning_inside(3, 5)
    assert inside == []


def test_empty_begins_inside():
    inside = empty.beginning_inside(3, 5)
    assert inside == []


def test_ascending():
    ascending = tested.ascending()
    assert tested is ascending


def test_empty_ascending():
    ascending = empty.ascending()
    assert ascending is empty


def test_descending():
    descending = tested.descending()
    assert descending == [
        GenericLabel(9, 13, i=7),
        GenericLabel(9, 13, i=6),
        GenericLabel(9, 10, i=5),
        GenericLabel(6, 8, i=4),
        GenericLabel(6, 7, i=3),
        GenericLabel(2, 6, i=2),
        GenericLabel(0, 7, i=1),
        GenericLabel(0, 5, i=0),
    ]


def test_empty_descending():
    descending = empty.descending()
    assert descending == []


def test_before():
    before = tested.before(8)
    assert before == [
        GenericLabel(0, 5, i=0),
        GenericLabel(0, 7, i=1),
        GenericLabel(2, 6, i=2),
        GenericLabel(6, 7, i=3),
        GenericLabel(6, 8, i=4),
    ]


def test_before_start():
    before = tested.before(3)
    assert before == []


def test_empty_before():
    before = empty.before(5)
    assert before == []


def test_after():
    after = tested.after(2)
    assert after == [
        GenericLabel(2, 6, i=2),
        GenericLabel(6, 7, i=3),
        GenericLabel(6, 8, i=4),
        GenericLabel(9, 10, i=5),
        GenericLabel(9, 13, i=6),
        GenericLabel(9, 13, i=7)
    ]
