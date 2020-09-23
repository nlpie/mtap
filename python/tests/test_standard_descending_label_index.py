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
#

import pytest

from mtap import GenericLabel, Location, Document
from mtap.data._label_indices import presorted_label_index


document = Document('plaintext', text='blah')


@pytest.fixture
def tested():
    return presorted_label_index([
        GenericLabel(0, 5, document=document, i=7),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(9, 13, document=document, i=1),
        GenericLabel(9, 13, document=document, i=0),
    ]).descending()


def test_getitem(tested):
    assert tested[3] == GenericLabel(6, 8, document=document, i=3)


def test_getitem_first(tested):
    assert tested[0] == GenericLabel(9, 13, document=document, i=0)


def test_getitem_last(tested):
    assert tested[7] == GenericLabel(0, 5, document=document, i=7)


def test_getitem_negative(tested):
    assert tested[-4] == GenericLabel(6, 7, document=document, i=4)


def test_getitem_last_negative(tested):
    assert tested[-1] == GenericLabel(0, 5, document=document, i=7)


def test_getitem_slice(tested):
    sliced = tested[2:4]
    assert sliced == [
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(6, 8, document=document, i=3),
    ]


def test_getitem_slice_end(tested):
    assert tested[4:8] == [
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(0, 5, document=document, i=7),
    ]


def test_getitem_slice_open_left(tested):
    assert tested[:4] == [
        GenericLabel(9, 13, document=document, i=0),
        GenericLabel(9, 13, document=document, i=1),
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(6, 8, document=document, i=3),
    ]


def test_getitem_slice_open_right(tested):
    assert tested[4:] == [
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(0, 5, document=document, i=7),
    ]


def test_getitem_slice_neg_right(tested):
    assert tested[4:-1] == [
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(0, 7, document=document, i=6),
    ]


def test_getitem_slice_neg_left(tested):
    assert tested[-4:-1] == [
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(0, 7, document=document, i=6),
    ]


def test_getitem_not_idx_slice(tested):
    with pytest.raises(TypeError):
        tested['foo']


def tested_getitem_slice_step_not_one(tested):
    slice = tested[1:4:2]
    assert slice == ([
        GenericLabel(9, 13, document=document, i=1),
        GenericLabel(6, 8, document=document, i=3),
    ])


def test_at(tested):
    assert tested.at(GenericLabel(2, 6, document=document))[0] == GenericLabel(2, 6, document=document, i=5)


def test_at_location(tested):
    assert tested.at(Location(2, 6))[0] == GenericLabel(2, 6, document=document, i=5)


def test_at_location_multiple(tested):
    assert tested.at(Location(9, 13)) == [
        GenericLabel(9, 13, document=document, i=0),
        GenericLabel(9, 13, document=document, i=1),
    ]


def test_at_location_not_found(tested):
    assert tested.at(Location(10, 10)) == []


def test_len(tested):
    assert len(tested) == 8


def test_covering(tested):
    covering = tested.covering(2, 4)
    assert list(covering) == [
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(0, 5, document=document, i=7),
    ]


def test_covering_empty(tested):
    assert tested.covering(4, 10) == []


def test_empty_covering(tested):
    covering = tested.covering(4, 10)
    assert list(covering) == []


def test_inside(tested):
    inside = tested.inside(1, 8)
    assert list(inside) == [
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
    ]


def test_inside_before(tested):
    inside = tested.inside(0, 3)
    assert list(inside) == []


def test_inside_after(tested):
    inside = tested.inside(15, 20)
    assert list(inside) == []


def test_inside_many(tested):
    tested = presorted_label_index([
        GenericLabel(0, 3, document=document),
        GenericLabel(0, 3, document=document),
        GenericLabel(0, 3, document=document),
        GenericLabel(0, 3, document=document),
        GenericLabel(0, 3, document=document),
        GenericLabel(0, 3, document=document),
        GenericLabel(0, 3, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(2, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 6, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
        GenericLabel(6, 10, document=document),
    ])
    inside = tested.inside(3, 6)
    assert inside == [
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(3, 5, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
    ]
    inside = inside.inside(5, 6)
    assert inside == [
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
        GenericLabel(5, 6, document=document),
    ]


def test_begins_inside(tested):
    inside = tested.beginning_inside(1, 9)
    assert list(inside) == [
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
    ]


def test_begins_inside_empty(tested):
    inside = tested.beginning_inside(3, 5)
    assert inside == []


def test_ascending(tested):
    ascending = tested.ascending()
    assert ascending == [
        GenericLabel(0, 5, document=document, i=7),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(9, 13, document=document, i=1),
        GenericLabel(9, 13, document=document, i=0),
    ]


def test_descending(tested):
    descending = tested.descending()
    assert descending == tested


def test_before(tested):
    before = tested.before(8)
    assert before == [
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(0, 5, document=document, i=7),
    ]


def test_before_start(tested):
    before = tested.before(3)
    assert before == []


def test_after(tested):
    after = tested.after(2)
    assert after == [
        GenericLabel(9, 13, document=document, i=0),
        GenericLabel(9, 13, document=document, i=1),
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(2, 6, document=document, i=5),
    ]


def test_contains_true(tested):
    assert GenericLabel(9, 13, document=document, i=0) in tested


def test_contains_false_location_in(tested):
    assert GenericLabel(9, 13, document=document) not in tested


def test_contains_false_location_not_in(tested):
    assert GenericLabel(0, 4, document=document) not in tested


def test_contains_false_not_label(tested):
    assert "blub" not in tested


def test_reversed(tested):
    l = list(reversed(tested))
    assert l == [
        GenericLabel(0, 5, document=document, i=7),
        GenericLabel(0, 7, document=document, i=6),
        GenericLabel(2, 6, document=document, i=5),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(6, 8, document=document, i=3),
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(9, 13, document=document, i=1),
        GenericLabel(9, 13, document=document, i=0),
    ]


def test_count_in(tested):
    assert tested.count(GenericLabel(2, 6, document=document, i=5)) == 1


def test_count_multiple(tested):
    index = presorted_label_index([
        GenericLabel(2, 6, document=document, i=2),
        GenericLabel(6, 7, document=document, i=3),
        GenericLabel(6, 8, document=document, i=4),
        GenericLabel(9, 10, document=document, i=5),
        GenericLabel(9, 13, document=document, i=6),
        GenericLabel(9, 13, document=document, i=7),
        GenericLabel(9, 13, document=document, i=6)
    ]).descending()
    assert index.count(GenericLabel(9, 13, document=document, i=6)) == 2


def test_count_different_label(tested):
    assert tested.count(GenericLabel(9, 13, document=document, x=2)) == 0


def test_count_not_label(tested):
    assert tested.count("blub") == 0


def test_count_location_not_in(tested):
    assert tested.count(GenericLabel(4, 5, document=document)) == 0


def test_filter(tested):
    assert tested.filter(lambda x: x.i % 2 == 0) == [
        GenericLabel(9, 13, document=document, i=0),
        GenericLabel(9, 10, document=document, i=2),
        GenericLabel(6, 7, document=document, i=4),
        GenericLabel(0, 7, document=document, i=6),
    ]
