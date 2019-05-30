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


def test_get_repr():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)

    assert repr(label) == "GenericLabel(0, 20, a='x', y=20, z=20.0)"


def test_get_attr():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)

    assert label.a == 'x'
    assert label.y == 20
    assert label.z == 20.0
    assert label.fields == {
        'start_index': 0,
        'end_index': 20,
        'a': 'x',
        'y': 20,
        'z': 20.0
    }


def test_loop_in_map():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    with pytest.raises(ValueError):
        label.bar = {
            'label': label
        }


def test_setattr():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    label.bar = 'baz'
    assert 'bar' in label.fields
    assert label.fields['bar'] == 'baz'


def test_eq_not_generic_label():
    assert GenericLabel(0, 20, a="x", y=20, z=20.0) != 0


def test_eq():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    label2 = GenericLabel(0, 20, a="x", y=20, z=20.0)

    assert label == label2


def test_not_eq():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    label2 = GenericLabel(0, 20, a="x", y=20, z=21.0)

    assert label != label2


def test_len():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    assert len(label) == 5


def test_location():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    assert label.location == (0, 20)


def test_get_item():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    assert label['a'] == 'x'


def test_iter():
    label = GenericLabel(0, 20, a="x", y=20, z=20.0)
    i = list(iter(label))
    assert len(i) == 5
    assert 'start_index' in i
    assert 'end_index' in i
    assert 'a' in i
    assert 'y' in i
    assert 'z' in i


def test_get_covered_text():
    label = GenericLabel(4, 7)
    assert label.get_covered_text('foo bar') == 'bar'


def test_covers():
    label = GenericLabel(0, 6)
    inside = GenericLabel(4, 6)
    assert label.location.covers(inside)


def test_list_attr():
    label = GenericLabel(0, 6)
    label.bar = [0, 1, 2]
    assert label.bar == [0, 1, 2]


def test_dict_attr():
    label = GenericLabel(0, 10)
    label.bar = {
        'a': 1,
        'b': 2,
    }
    assert label.bar == {
        'a': 1,
        'b': 2,
    }


def test_list_ref_loop():
    label = GenericLabel(0, 4)
    with pytest.raises(ValueError):
        label.a = [label]


def test_obj_attr():
    label = GenericLabel(0, 4)
    with pytest.raises(TypeError):
        label.b = object()


def test_float_to_int():
    label = GenericLabel(0.0, 4.0)
    assert isinstance(label.start_index, int)
    assert isinstance(label.end_index, int)
