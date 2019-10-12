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
import json
from pathlib import Path
from tempfile import TemporaryFile

from mtap.io.serialization import JsonSerializer

import mtap
from mtap import GenericLabel
from mtap.events import Event, Document


def test_json_serializer():
    event = Event(event_id='1')
    event.metadata['foo'] = "bar"
    document = Document('plaintext', text='Some text.')
    event.add_document(document)
    document.add_labels('one', [mtap.GenericLabel(start_index=0, end_index=5, x=10),
                                mtap.GenericLabel(start_index=6, end_index=10, x=15)])
    document.add_labels('two', [mtap.GenericLabel(start_index=0, end_index=25, a='b'),
                                mtap.GenericLabel(start_index=26, end_index=42, a='c')])
    document.add_labels('three', [
        mtap.GenericLabel(start_index=0, end_index=10, foo=True),
        mtap.GenericLabel(start_index=11, end_index=15, foo=False)
    ], distinct=True)

    tf = TemporaryFile('w+')
    JsonSerializer.event_to_file(event, tf)
    tf.flush()
    tf.seek(0)

    o = json.load(tf)
    assert o['event_id'] == '1'
    assert o['metadata']['foo'] == 'bar'
    d = o['documents']['plaintext']
    assert d['text'] == 'Some text.'
    assert len(d['label_indices']) == 3
    assert d['label_indices']['one'] == {
        'json_labels': [
            {
                'start_index': 0,
                'end_index': 5,
                'x': 10
            },
            {
                'start_index': 6,
                'end_index': 10,
                'x': 15
            }
        ],
        'distinct': False
    }
    assert d['label_indices']['two'] == {
        'json_labels': [
            {
                'start_index': 0,
                'end_index': 25,
                'a': 'b'
            },
            {
                'start_index': 26,
                'end_index': 42,
                'a': 'c'
            }
        ],
        'distinct': False
    }
    assert d['label_indices']['three'] == {
        'json_labels': [
            {
                'start_index': 0,
                'end_index': 10,
                'foo': True
            },
            {
                'start_index': 11,
                'end_index': 15,
                'foo': False
            }
        ],
        'distinct': True
    }


def test_deserialization():
    f = Path(__file__).parent / 'event.json'
    event = JsonSerializer.file_to_event(f)
    assert event.event_id == '12345'
    assert event.metadata['foo'] == 'bar'
    d = event.documents['plaintext']
    assert d.text == "The quick brown fox jumps over the lazy dog."
    assert len(d.get_label_indices_info()) == 3
    assert d.get_label_index("one") == [
        GenericLabel(start_index=0, end_index=10, a="b"),
        GenericLabel(start_index=12, end_index=25, a="c"),
        GenericLabel(start_index=26, end_index=52, a="d"),
        GenericLabel(start_index=53, end_index=85, a="e"),
    ]
    assert d.get_label_index("two") == [
        GenericLabel(start_index=0, end_index=10, x=1),
        GenericLabel(start_index=3, end_index=9, x=3),
        GenericLabel(start_index=4, end_index=25, x=2),
        GenericLabel(start_index=5, end_index=25, x=4),
    ]
    assert d.get_label_index("three") == [
        GenericLabel(start_index=0, end_index=10, x=True),
        GenericLabel(start_index=3, end_index=9, x=True),
        GenericLabel(start_index=4, end_index=25, x=False),
        GenericLabel(start_index=5, end_index=25, x=False),
    ]
