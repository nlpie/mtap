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

import nlpnewt

from nlpnewt import Event, EventsClient, Document, GenericLabel


def test_add_labels_not_distinct(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    l2 = document.add_labels('index', labels)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=mocker.ANY
    )
    assert l2 == labels
    assert not l2.distinct


def test_add_labels_distinct(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    l2 = document.add_labels('index', labels, distinct=True)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=mocker.ANY
    )
    assert l2 == labels
    assert l2.distinct


def test_add_labels_label_type_id(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    l2 = document.add_labels('index', labels, label_type_id=nlpnewt.constants.DISTINCT_GENERIC_LABEL_ID)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=mocker.ANY
    )
    assert l2 == labels
    assert l2.distinct


def test_add_labels_label_adapter(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    label_adapter = nlpnewt.events._get_label_adapter(nlpnewt.constants.DISTINCT_GENERIC_LABEL_ID)
    l2 = document.add_labels('index', labels, label_adapter=label_adapter)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=label_adapter
    )
    assert l2 == labels
    assert l2.distinct


def test_labeler_not_distinct_default(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    with document.get_labeler('index') as add_generic_label:
        add_generic_label(0, 10, x=1)
        add_generic_label(11, 15, x=2)
        add_generic_label(16, 20, x=3)
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    label_adapter = nlpnewt.events._get_label_adapter(nlpnewt.constants.GENERIC_LABEL_ID)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=label_adapter
    )
    assert document.get_label_index('index') == labels


def test_labeler_distinct(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    with document.get_labeler('index', distinct=True) as add_generic_label:
        add_generic_label(0, 10, x=1)
        add_generic_label(11, 15, x=2)
        add_generic_label(16, 20, x=3)
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    label_adapter = nlpnewt.events._get_label_adapter(nlpnewt.constants.DISTINCT_GENERIC_LABEL_ID)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=label_adapter
    )
    assert document.get_label_index('index') == labels


def test_labeler_label_type_id(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.')
    document.event = event
    with document.get_labeler('index', label_type_id=nlpnewt.constants.DISTINCT_GENERIC_LABEL_ID) as add_generic_label:
        add_generic_label(0, 10, x=1)
        add_generic_label(11, 15, x=2)
        add_generic_label(16, 20, x=3)
    labels = [
        GenericLabel(0, 10, x=1),
        GenericLabel(11, 15, x=2),
        GenericLabel(16, 20, x=3)
    ]
    label_adapter = nlpnewt.events._get_label_adapter(nlpnewt.constants.DISTINCT_GENERIC_LABEL_ID)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=label_adapter
    )
    assert document.get_label_index('index') == labels


def test_labeler_distinct_and_type_id_raises(mocker):
    with pytest.raises(ValueError):
        client = mocker.Mock(EventsClient)
        event = Event(event_id='1', client=client)
        document = Document(document_name='plaintext',
                            text='The quick brown fox jumped over the lazy dog.')
        document.event = event
        document.get_labeler('index', distinct=True, label_type_id=nlpnewt.constants.DISTINCT_GENERIC_LABEL_ID)
