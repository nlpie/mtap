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

from mtap import Event, EventsClient, Document, GenericLabel
from mtap.data import DISTINCT_GENERIC_ADAPTER, GENERIC_ADAPTER


def test_add_labels_not_distinct(mocker):
    client = mocker.Mock(EventsClient)
    client.get_label_index_info.return_value = []
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.', event=event)
    labels = [
        GenericLabel(0, 10, document=document, x=1),
        GenericLabel(11, 15, document=document, x=2),
        GenericLabel(16, 20, document=document, x=3)
    ]
    document.add_labels('index', labels)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=mocker.ANY
    )
    l2 = document.labels['index']
    assert l2 == labels
    assert not l2.distinct


def test_add_labels_distinct(mocker):
    client = mocker.Mock(EventsClient)
    client.get_label_index_info.return_value = []
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.', event=event)
    labels = [
        GenericLabel(0, 10, document=document, x=1),
        GenericLabel(11, 15, document=document, x=2),
        GenericLabel(16, 20, document=document, x=3)
    ]
    document.add_labels('index', labels, distinct=True)
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=mocker.ANY
    )
    l2 = document.labels['index']
    assert l2 == labels
    assert l2.distinct


def test_labeler_not_distinct_default(mocker):
    client = mocker.Mock(EventsClient)
    client.get_label_index_info.return_value = []
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.', event=event)
    with document.get_labeler('index') as add_generic_label:
        add_generic_label(0, 10, x=1)
        add_generic_label(11, 15, x=2)
        add_generic_label(16, 20, x=3)
    labels = [
        GenericLabel(0, 10, document=document, x=1),
        GenericLabel(11, 15, document=document, x=2),
        GenericLabel(16, 20, document=document, x=3)
    ]
    label_adapter = GENERIC_ADAPTER
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=label_adapter
    )
    assert document.labels['index'] == labels


def test_labeler_distinct(mocker):
    client = mocker.Mock(EventsClient)
    client.get_label_index_info.return_value = []
    event = Event(event_id='1', client=client)
    document = Document(document_name='plaintext',
                        text='The quick brown fox jumped over the lazy dog.', event=event)
    with document.get_labeler('index', distinct=True) as add_generic_label:
        add_generic_label(0, 10, x=1)
        add_generic_label(11, 15, x=2)
        add_generic_label(16, 20, x=3)
    labels = [
        GenericLabel(0, 10, document=document, x=1),
        GenericLabel(11, 15, document=document, x=2),
        GenericLabel(16, 20, document=document, x=3)
    ]
    label_adapter = DISTINCT_GENERIC_ADAPTER
    client.add_labels.assert_called_with(
        event_id='1',
        document_name='plaintext',
        index_name='index',
        labels=labels,
        adapter=label_adapter
    )
    assert document.labels['index'] == labels
