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
from google.protobuf import struct_pb2

from mtap._structs import copy_dict_to_struct, copy_struct_to_dict


def test_recursive_looping():
    a = {}
    a['a'] = {'a': a}
    with pytest.raises(ValueError):
        copy_dict_to_struct(a, struct_pb2.Struct())


def test_recursive_looping_in_list():
    a = {}
    a['bar'] = [a]
    with pytest.raises(ValueError):
        copy_dict_to_struct(a, struct_pb2.Struct())


def test_empty():
    d = {}
    copy_dict_to_struct(d, struct_pb2.Struct())


def test_dict_in_dict():
    a = {
        'b': {
            'bar': 'baz'
        }
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(a, struct)
    assert isinstance(struct['b'], struct_pb2.Struct)
    assert struct['b']['bar'] == 'baz'


def test_copies_object():
    class TestClass:
        def __init__(self):
            self.bar = 'baz'
    b = TestClass()
    a = {
        'b': b
    }
    with pytest.raises(TypeError):
        copy_dict_to_struct(a, struct_pb2.Struct())


def test_empty_list():
    d = {
        'bar': []
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert list(struct['bar']) == []


def test_string_list():
    d = {
        'bar': ['a', 'b', 'c', 'd']
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert isinstance(struct['bar'], struct_pb2.ListValue)
    assert list(struct['bar']) == ['a', 'b', 'c', 'd']


def test_int_list():
    d = {
        'bar': [0, 1, 2, 3]
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert isinstance(struct['bar'], struct_pb2.ListValue)
    assert list(struct['bar']) == [0, 1, 2, 3]


def test_float_list():
    d = {
        'bar': [0.1, 1.2, 2.2, 3.3]
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert isinstance(struct['bar'], struct_pb2.ListValue)
    assert list(struct['bar']) == [0.1, 1.2, 2.2, 3.3]


def test_bool_list():
    d = {
        'bar': [True, False, False, True]
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert isinstance(struct['bar'], struct_pb2.ListValue)
    assert list(struct['bar']) == [True, False, False, True]


def test_list_of_lists():
    d = {
        'bar': [[0, 1, 2, 3], [4, 5, 6]]
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert isinstance(struct['bar'], struct_pb2.ListValue)
    assert list(struct['bar'][0]) == [0, 1, 2, 3]
    assert list(struct['bar'][1]) == [4, 5, 6]


def test_list_of_dicts():
    d = {
        'a': [
            {
                'bar': 'baz'
            },
            {
                'foo': 'bar'
            }
        ]
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert isinstance(struct['a'], struct_pb2.ListValue)
    assert isinstance(struct['a'][0], struct_pb2.Struct)
    assert struct['a'][0]['bar'] == 'baz'
    assert isinstance(struct['a'][1], struct_pb2.Struct)
    assert struct['a'][1]['foo'] == 'bar'


def test_list_of_objects():
    class TestClass:
        def __init__(self, val):
            self.bar = val
    d = {
        'bar': [
            TestClass('a'),
            TestClass(1),
            TestClass(False)
        ]
    }
    with pytest.raises(TypeError):
        copy_dict_to_struct(d, struct_pb2.Struct())


def test_str_field():
    d = {
        'bar': 'baz'
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert struct['bar'] == 'baz'


def test_float_field():
    d = {
        'bar': 0.1
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert struct['bar'] == 0.1


def test_bool_field():
    d = {
        'bar': True
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert struct['bar'] is True


def test_int_field():
    d = {
        'bar': 42
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert struct['bar'] == 42


def test_null_field():
    d = {
        'bar': None
    }
    struct = struct_pb2.Struct()
    copy_dict_to_struct(d, struct)
    assert struct['bar'] is None


def test_empty_struct():
    struct = struct_pb2.Struct()
    d = {}
    copy_struct_to_dict(struct, d)
    assert d == {}


def test_null_field_reverse():
    struct = struct_pb2.Struct()
    struct['bar'] = None
    d = {}
    copy_struct_to_dict(struct, d)
    assert d == {'bar': None}


def test_str_field_reverse():
    struct = struct_pb2.Struct()
    struct['bar'] = 'baz'
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == 'baz'


def test_float_field_reverse():
    struct = struct_pb2.Struct()
    struct['bar'] = 1.2
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == 1.2


def test_bool_field_reverse():
    struct = struct_pb2.Struct()
    struct['bar'] = True
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] is True


def test_int_field_reverse():
    struct = struct_pb2.Struct()
    struct['bar'] = 1
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == 1


def test_empty_list_field_reverse():
    struct = struct_pb2.Struct()
    struct.get_or_create_list('bar')
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == []


def test_none_list_field_reverse():
    struct = struct_pb2.Struct()
    bar = struct.get_or_create_list('bar')
    bar.append(None)
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == [None]


def test_str_list_field_reverse():
    struct = struct_pb2.Struct()
    struct.get_or_create_list('bar').extend(['a', 'b', 'c'])
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == ['a', 'b', 'c']


def test_float_list_field_reverse():
    struct = struct_pb2.Struct()
    struct.get_or_create_list('bar').extend([1.2, 2.2, 3.2])
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == [1.2, 2.2, 3.2]


def test_bool_list_field_reverse():
    struct = struct_pb2.Struct()
    struct.get_or_create_list('bar').extend([True, False, True])
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == [True, False, True]


def test_int_list_field_reverse():
    struct = struct_pb2.Struct()
    struct.get_or_create_list('bar').extend([1, 2, 3])
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == [1, 2, 3]


def test_list_list_field_reverse():
    struct = struct_pb2.Struct()
    bar = struct.get_or_create_list('bar')
    bar.add_list().extend([1, 2, 3])
    bar.add_list().extend([4, 5, 6])
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == [[1, 2, 3], [4, 5, 6]]


def test_struct_list_field_reverse():
    struct = struct_pb2.Struct()
    bar = struct.get_or_create_list('bar')
    bar.add_struct()['bar'] = 'baz'
    bar.add_struct()['foo'] = 'bar'
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == [{'bar': 'baz'}, {'foo': 'bar'}]


def test_struct_field_reverse():
    struct = struct_pb2.Struct()
    struct.get_or_create_struct('bar')['bar'] = 'baz'
    d = {}
    copy_struct_to_dict(struct, d)
    assert d['bar'] == {'bar': 'baz'}
