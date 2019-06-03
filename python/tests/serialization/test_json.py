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
from tempfile import TemporaryFile
from typing import List

import nlpnewt
from nlpnewt.events import LabelIndexInfo, LabelIndexType
from nlpnewt.label_indices import LabelIndex
from nlpnewt.serialization.serializers import get_serializer


class Event(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_id = "1"
        self.metadata = {}


class Document:
    def __init__(self):
        self.label_indices = {}

    def get_label_indices_info(self) -> List[LabelIndexInfo]:
        result = []
        for k, v in self.label_indices.items():
            result.append(LabelIndexInfo(index_name=k, type=LabelIndexType.JSON))
        return result

    def get_label_index(self, label_index_name: str, *, label_type_id: str = None) -> LabelIndex:
        return self.label_indices[label_index_name]


def test_json_serializer():
    event = Event()
    event.metadata['foo'] = "bar"
    document = Document()
    document.document_name = "plaintext"
    document.text = "Some text."
    label_index = nlpnewt.label_index([nlpnewt.GenericLabel(start_index=0, end_index=5, x=10),
                                       nlpnewt.GenericLabel(start_index=6, end_index=10, x=15)])
    document.label_indices['one'] = label_index
    label_index = nlpnewt.label_index([nlpnewt.GenericLabel(start_index=0, end_index=25, a='b'),
                                       nlpnewt.GenericLabel(start_index=26, end_index=42, a='c')])
    document.label_indices['two'] = label_index
    label_index = nlpnewt.label_index([
        nlpnewt.GenericLabel(start_index=0, end_index=10, foo=True),
        nlpnewt.GenericLabel(start_index=11, end_index=15, foo=False)
    ])
    document.label_indices['three'] = label_index
    event['plaintext'] = document

    serializer = get_serializer('json')()
    tf = TemporaryFile('w+')
    serializer.event_to_file(event, tf)
    tf.flush()
    tf.seek(0)

    o = json.load(tf)
    assert o['event_id'] == '1'
    assert o['metadata']['foo'] == 'bar'
    d = o['documents'][0]
    assert d['document_name'] == 'plaintext'
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
        ]
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
        ]
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
        ]
    }
