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
"""Internal utilities for interacting with protobuf structs."""
from typing import Sequence, Mapping

from google.protobuf import struct_pb2


def copy_dict_to_struct(d, struct, parents=None):
    if parents is None:
        parents = [d]
    for k, v in d.items():
        copy_item_to_struct(k, v, struct, parents)


def copy_item_to_struct(k, v, struct, parents):
    if isinstance(v, (str, float, bool, int)) or v is None:
        struct[k] = v
    elif isinstance(v, Sequence):
        _check_for_reference_cycle(v, parents)
        copy_list_to_list_value(v, struct.get_or_create_list(k), parents + [v])
    elif isinstance(v, Mapping):
        _check_for_reference_cycle(v, parents)
        copy_dict_to_struct(v, struct.get_or_create_struct(k), parents + [v])
    else:
        raise TypeError("Unrecognized type:", type(v))


def copy_list_to_list_value(lst, list_value, parents):
    for v in lst:
        if isinstance(v, (str, float, bool, int)) or v is None:
            list_value.append(v)
        elif isinstance(v, Sequence):
            _check_for_reference_cycle(v, parents)
            copy_list_to_list_value(v, list_value.add_list(), parents + [v])
        elif isinstance(v, Mapping):
            _check_for_reference_cycle(v, parents)
            copy_dict_to_struct(v, list_value.add_struct(), parents + [v])
        else:
            raise TypeError("Unrecognized type:", type(v))


def _check_for_reference_cycle(o, parents):
    for parent in parents:
        if o is parent:
            raise ValueError("Reference cycle while preparing for serialization.")


def copy_list_value_to_list(list_value, lst):
    for v in list_value:
        if isinstance(v, (str, float, bool, int)) or v is None:
            lst.append(v)
        elif isinstance(v, struct_pb2.ListValue):
            lst2 = []
            copy_list_value_to_list(v, lst2)
            lst.append(lst2)
        elif isinstance(v, struct_pb2.Struct):
            d = {}
            copy_struct_to_dict(v, d)
            lst.append(d)
        else:
            raise TypeError("Unrecognized type:", type(v))


def copy_struct_to_dict(struct, dictionary):
    for k, v in struct.items():
        if isinstance(v, (str, float, bool, int)) or v is None:
            dictionary[k] = v
        elif isinstance(v, struct_pb2.ListValue):
            lst = []
            copy_list_value_to_list(v, lst)
            dictionary[k] = lst
        elif isinstance(v, struct_pb2.Struct):
            d = {}
            copy_struct_to_dict(v, d)
            dictionary[k] = d
        else:
            raise TypeError("Unrecognized type:", type(v))


