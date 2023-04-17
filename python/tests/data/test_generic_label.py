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

from mtap import GenericLabel, Document

document = Document('plaintext', text='foo bar')


def test_get_repr():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)

    rep = repr(label)
    assert rep.startswith("GenericLabel(0, 20, ")
    assert 'a="x"' in rep or "a='x'" in rep
    assert 'y=20' in rep
    assert 'z=20.0' in rep


def test_get_repr_ref():
    label = GenericLabel(0, 20, document=document, a=GenericLabel(0, 20, x="a"))

    rep = repr(label)
    assert rep == 'GenericLabel(0, 20, a=GenericLabel(0, 20, x=\'a\'))'


def test_get_repr_infinite_recursion():
    label = GenericLabel(0, 20, document=document)
    b = GenericLabel(0, 20, document=document, a=label)
    label.b = b

    rep = repr(label)
    assert rep == 'GenericLabel(0, 20, b=GenericLabel(0, 20, a=GenericLabel(...)))'


def test_get_attr():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)

    assert label.a == 'x'
    assert label.y == 20
    assert label.z == 20.0
    assert label.fields == {
        'a': 'x',
        'y': 20,
        'z': 20.0
    }


def test_loop_in_map():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)
    with pytest.raises(ValueError):
        label.bar = {
            'label': label
        }


def test_setattr():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)
    label.bar = 'baz'
    assert 'bar' in label.fields
    assert label.fields['bar'] == 'baz'


def test_eq_not_generic_label():
    assert GenericLabel(0, 20, document=document, a="x", y=20, z=20.0) != 0


def test_eq():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)
    label2 = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)

    assert label == label2


def test_not_eq():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)
    label2 = GenericLabel(0, 20, document=document, a="x", y=20, z=21.0)

    assert label != label2


def test_location():
    label = GenericLabel(0, 20, document=document, a="x", y=20, z=20.0)
    assert label.location == (0, 20)


def test_get_covered_text():
    label = GenericLabel(4, 7, document=document)
    assert label.text == 'bar'


def test_covers():
    label = GenericLabel(0, 6, document=document)
    inside = GenericLabel(4, 6, document=document)
    assert label.location.covers(inside)


def test_list_attr():
    label = GenericLabel(0, 6, document=document)
    label.bar = [0, 1, 2]
    assert label.bar == [0, 1, 2]


def test_dict_attr():
    label = GenericLabel(0, 10, document=document)
    label.bar = {
        'a': 1,
        'b': 2,
    }
    assert label.bar == {
        'a': 1,
        'b': 2,
    }


def test_list_ref_loop():
    label = GenericLabel(0, 4, document=document)
    with pytest.raises(ValueError):
        label.a = [label]


def test_obj_attr():
    label = GenericLabel(0, 4, document=document)
    with pytest.raises(TypeError):
        label.b = object()


def test_float_to_int():
    label = GenericLabel(0.0, 4.0, document=document)
    assert isinstance(label.start_index, int)
    assert isinstance(label.end_index, int)


def test_get_document():
    label = GenericLabel(0, 4, document=document)
    assert label.document == document


def test_set_document():
    label = GenericLabel(0, 4)
    label.document = document
    assert label.document == document


def test_try_assign_reserved():
    label = GenericLabel(0, 0)
    with pytest.raises(ValueError):
        label.location = 10
    with pytest.raises(ValueError):
        label.text = 'blah'


def test_construct_with_reserved():
    with pytest.raises(ValueError):
        GenericLabel(0, 0, location=1)
    with pytest.raises(ValueError):
        GenericLabel(0, 0, text='some text')


def test_infinite_recursion_equals():
    a = GenericLabel(0, 15)
    b = GenericLabel(0, 13)
    a.b = b
    b.a = a

    a2 = GenericLabel(0, 15)
    b2 = GenericLabel(0, 13)
    a2.b = b2
    b2.a = a2

    assert a == a2
