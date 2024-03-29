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
from tempfile import TemporaryFile

import mtap
from mtap import Event, Document
from mtap.serialization import JsonSerializer, Serializer


def test_json_serializer():
    event = Event(event_id='1')
    event.metadata['foo'] = "bar"
    document = Document('plaintext', text='Some text.')
    event.add_document(document)
    one = mtap.GenericLabel(start_index=0, end_index=5, x=10)
    two = mtap.GenericLabel(start_index=6, end_index=10, x=15)
    document.add_labels('one', [one,
                                two])
    document.add_labels('two', [mtap.GenericLabel(start_index=0, end_index=25, a='b', b=one),
                                mtap.GenericLabel(start_index=26, end_index=42, a='c', b=two)])
    document.add_labels('three', [
        mtap.GenericLabel(start_index=0, end_index=10, foo=True),
        mtap.GenericLabel(start_index=11, end_index=15, foo=False)
    ], distinct=True)

    with TemporaryFile('w+') as tf:
        JsonSerializer.event_to_file(event, tf)
        tf.flush()
        tf.seek(0)
        e = JsonSerializer.file_to_event(tf)

    assert e.event_id == event.event_id
    assert e.metadata['foo'] == 'bar'
    d = e.documents['plaintext']
    assert d.text == document.text
    index_one = d.labels['one']
    assert index_one == [one, two]
    index_two = d.labels['two']
    assert index_two == [mtap.GenericLabel(start_index=0, end_index=25, a='b', b=one),
                         mtap.GenericLabel(start_index=26, end_index=42, a='c', b=two)]
    index_three = d.labels['three']
    assert index_three == [mtap.GenericLabel(start_index=0, end_index=10, foo=True),
                           mtap.GenericLabel(start_index=11, end_index=15, foo=False)]


def test_registered():
    assert Serializer.get('json') is JsonSerializer
