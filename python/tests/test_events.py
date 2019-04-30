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
from typing import NamedTuple, List

import pytest

from nlpnewt import Events, GenericLabel, label_index
from nlpnewt._events_service import EventsServicer
from nlpnewt.api.v1 import events_pb2
from nlpnewt.events import Event, ProtoLabelAdapter, proto_label_adapter
from nlpnewt.labels import Label


@pytest.fixture
def events_servicer():
    return EventsServicer()


@pytest.fixture
def events(events_servicer) -> Events:
    with Events(stub=events_servicer) as events:
        yield events


@pytest.fixture
def event(events) -> Event:
    with events.open_event('id') as event:
        yield event


@pytest.fixture
def event2(events) -> Event:
    with events.open_event('id') as event:
        yield event


@pytest.fixture
def doc(event):
    return event.add_document('plaintext', 'blub')


@pytest.fixture
def doc2(event2):
    return event2['plaintext']


def test_open_event_new(events, events_servicer):
    with events.open_event('id') as event:
        assert event is not None
        assert events_servicer.events['id'] is not None

    with pytest.raises(KeyError):
        events_servicer.events['id']


def test_open_event_existing(events, events_servicer):
    with events.open_event('id'):
        with events.open_event('id'):
            pass
        assert events_servicer.events['id'] is not None

    with pytest.raises(KeyError):
        events_servicer.events['id']


def test_create_event_fails_existing(events: Events):
    with events.open_event('id'):
        with pytest.raises(ValueError):
            events.create_event('id')


def test_create_event(events: Events, events_servicer: EventsServicer):
    with events.create_event('id') as event:
        assert event is not None
        assert events_servicer.events['id'] is not None

    with pytest.raises(KeyError):
        events_servicer.events['id']


def test_event_event_id(events):
    with events.create_event('id') as event:
        assert event.event_id == 'id'


def test_metadata_not_open(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        event.metadata


def test_event_metadata_contains_true(events):
    with events.create_event('id') as e1, events.open_event('id') as e2:
        e1.metadata['bar'] = 'baz'
        assert 'bar' in e2.metadata


def test_event_metadata_contains_true_cached(events):
    with events.create_event('id') as e1:
        e1.metadata['bar'] = 'baz'
        assert 'bar' in e1.metadata


def test_event_metadata_contains_false(events):
    with events.create_event('id') as e1:
        assert 'bar' not in e1.metadata


def test_event_metadata_contains_not_open(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        'bar' in event.metadata


def test_double_set_metadata(events):
    with events.create_event('id') as e1, events.open_event('id') as e2:
        e1.metadata['bar'] = 'baz'
        with pytest.raises(KeyError):
            e2.metadata['bar'] = 'baz'


def test_get_metadata(events):
    with events.create_event('id') as e1, events.open_event('id') as e2:
        e1.metadata['bar'] = 'baz'
        assert e2.metadata['bar'] == 'baz'


def test_get_metadata_missing(events):
    with events.create_event('id') as e1:
        with pytest.raises(KeyError):
            e1.metadata['bar']


def test_get_metadata_not_open(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        event.metadata['bar']


def test_del_metadata(events):
    with events.create_event('id') as e1:
        with pytest.raises(NotImplementedError):
            del e1.metadata['bar']


def test_iter_metadata(events):
    with events.create_event('id') as e1, events.open_event('id') as e2:
        e1.metadata['bar'] = 'baz'
        e1.metadata['baz'] = 'foo'
        e1.metadata['foo'] = 'bar'
        l = list(iter(e2.metadata))
        assert 'bar' in l
        assert 'baz' in l
        assert 'foo' in l


def test_iter_metadata_empty(events):
    with events.create_event('id') as e1:
        assert list(iter(e1.metadata)) == []


def test_iter_metadata_not_open(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        iter(event.metadata)


def test_len_metadata(events):
    with events.create_event('id') as e1, events.open_event('id') as e2:
        e1.metadata['bar'] = 'baz'
        e1.metadata['baz'] = 'foo'
        e1.metadata['foo'] = 'bar'
        assert len(e2.metadata) == 3


def test_len_empty_metadata(events):
    with events.create_event('id') as e1:
        assert len(e1.metadata) == 0


def test_len_metadata_not_open(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        len(event.metadata)


def test_add_document(event, events_servicer):
    event.add_document('plaintext', 'foo bar')
    assert events_servicer.events['id'].documents['plaintext'].text == 'foo bar'


def test_add_document_existing(event, event2):
    event.add_document('plaintext', 'foo')
    with pytest.raises(Exception):
        event2.add_document('plaintext', 'foo')


def test_add_document_name_not_string(event):
    with pytest.raises(TypeError):
        event.add_document(1, 'text')


def test_add_document_none_text(event):
    with pytest.raises(Exception):
        event.add_document('plaintext', None)


def test_add_document_closed(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        event.add_document('plaintext', 'foo')


def test_event_contains_document(event, event2):
    event.add_document('plaintext', 'blub')
    assert 'plaintext' in event2


def test_event_contains_not_string(event):
    assert 1 not in event


def test_event_contains_local(event):
    event.add_document('plaintext', 'blub')
    assert 'plaintext' in event


def test_event_contains_closed(events):
    event = events.open_event('1')
    event.add_document('plaintext', 'foo')
    event.close()
    with pytest.raises(ValueError):
        'plaintext' in event


def test_event_get_document(event, event2):
    d1 = event.add_document('plaintext', 'foo')
    d2 = event2['plaintext']
    assert d2.document_name == d1.document_name
    assert d2.text == d1.text


def test_event_get_document_missing(event):
    with pytest.raises(KeyError):
        event['plaintext']


def test_event_get_document_none(event):
    with pytest.raises(KeyError):
        event[None]


def test_event_get_document_closed(events):
    event = events.open_event('1')
    event.add_document('plaintext', 'foo')
    event.close()
    with pytest.raises(ValueError):
        event['plaintext']


def test_event_len(event, event2):
    event.add_document('a', '1')
    event.add_document('b', '2')
    event.add_document('c', '3')
    assert len(event2) == 3


def test_empty_event_len(event):
    assert len(event) == 0


def test_len_closed_event(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        len(event)


def test_iter_event(event, event2):
    event.add_document('a', '1')
    event.add_document('b', '2')
    event.add_document('c', '3')
    l = list(iter(event2))
    assert len(l) == 3
    assert 'a' in l
    assert 'b' in l
    assert 'c' in l


def test_iter_empty_event(event):
    assert list(iter(event)) == []


def test_iter_closed_event(events):
    event = events.open_event('1')
    event.close()
    with pytest.raises(ValueError):
        iter(event)


def test_document_event(doc):
    assert doc.event.event_id == 'id'


def test_document_get_label_index(doc, doc2):
    with doc.get_labeler('labels') as label:
        label(0, 1, x='a')
        label(0, 2, x='b')

    index = doc2.get_label_index('labels')
    assert index == [
        GenericLabel(0, 1, x='a'),
        GenericLabel(0, 2, x='b')
    ]


def test_document_get_label_index_cached(doc):
    with doc.get_labeler('labels') as label:
        label(0, 1, x='a')
        label(0, 2, x='b')

    doc.get_label_index('labels')
    index = doc.get_label_index('labels')
    assert index == [
        GenericLabel(0, 1, x='a'),
        GenericLabel(0, 2, x='b')
    ]


def test_document_get_label_index_closed(events):
    event = events.open_event('1')
    doc = event.add_document('plaintext', 'foo')
    with doc.get_labeler('labels') as label:
        label(0, 1, x='a')
        label(0, 2, x='b')
    event.close()
    with pytest.raises(ValueError):
        doc.get_label_index('plaintext')


def test_document_create_labeler_in_use(doc):
    with doc.get_labeler('labels') as label:
        label(0, 1, x='a')
        label(0, 2, x='b')

    with pytest.raises(KeyError):
        with doc.get_labeler('labels'):
            pass


def test_labeler_closed(events):
    event = events.open_event('1')
    doc = event.add_document('plaintext', 'foo')
    event.close()
    with pytest.raises(ValueError):
        with doc.get_labeler('labels') as l:
            pass


class _CustomLabel(NamedTuple):
    start_index: int
    end_index: int
    x: str


CustomLabel = type('CustomLabel', (_CustomLabel, Label), {})


@proto_label_adapter('test')
class CustomLabelAdapter(ProtoLabelAdapter[CustomLabel]):
    def create_label(self, start_index, end_index, x=None):
        return CustomLabel(start_index, end_index, x)

    def create_index_from_response(self, response: events_pb2.GetLabelsResponse):
        return label_index([CustomLabel(x['start_index'], x['end_index'], x['x'])
                            for x in response.json_labels.labels])

    def add_to_message(self, labels: List[CustomLabel], request: events_pb2.AddLabelsRequest):
        for l in labels:
            struct = request.json_labels.labels.add()
            struct['start_index'] = l.start_index
            struct['end_index'] = l.end_index
            struct['x'] = l.x


def test_document_custom_labeler(doc, doc2):
    with doc.get_labeler('labels', label_type_id='test') as label:
        label(0, 1, x='a')
        label(0, 2, x='b')

    index = doc2.get_label_index('labels', label_type_id='test')
    assert index == [
        CustomLabel(0, 1, x='a'),
        CustomLabel(0, 2, x='b')
    ]


def test_get_created_indices(doc):
    with doc.get_labeler('labels', label_type_id='test') as label:
        label(0, 1, x='a')
        label(0, 2, x='b')

    assert 'labels' in doc.created_indices
    assert 'labels' in doc.event.created_indices['plaintext']


def test_add_created_indices(doc):
    doc.event.add_created_indices({'plaintext': ['x', 'y', 'z']})

    assert 'x' in doc.created_indices
    assert 'y' in doc.created_indices
    assert 'z' in doc.created_indices
