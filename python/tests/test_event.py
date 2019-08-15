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

from nlpnewt.events import EventsClient, Event, Document


def test_add_document(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = Document('plaintext',
                        "“You're no help,” he told the lime. "
                        "This was unfair. It was only a lime; "
                        "there was nothing special about it at all. "
                        "It was doing the best it could.")
    event.add_document(document)
    assert event.documents['plaintext'] == document
    client.add_document.assert_called_once_with('1', 'plaintext',
                                                "“You're no help,” he told the lime. "
                                                "This was unfair. It was only a lime; "
                                                "there was nothing special about it at all. "
                                                "It was doing the best it could.")


def test_add_document_no_client():
    event = Event(event_id='1')
    document = Document('plaintext',
                        "“You're no help,” he told the lime. This was unfair. It was only a lime; "
                        "there was nothing special about it at all. "
                        "It was doing the best it could.")
    event.add_document(document)
    assert event.documents['plaintext'] == document


def test_create_document(mocker):
    client = mocker.Mock(EventsClient)
    event = Event(event_id='1', client=client)
    document = event.create_document('plaintext', "“You're no help,” he told the lime. "
                                                  "This was unfair. It was only a lime; "
                                                  "there was nothing special about it at all. "
                                                  "It was doing the best it could.")
    assert event.documents['plaintext'] == document
    client.add_document.assert_called_once_with('1', 'plaintext',
                                                "“You're no help,” he told the lime. "
                                                "This was unfair. It was only a lime; "
                                                "there was nothing special about it at all. "
                                                "It was doing the best it could.")


def test_create_document_no_client():
    event = Event(event_id='1')
    document = event.create_document('plaintext', "“You're no help,” he told the lime. "
                                                  "This was unfair. It was only a lime; "
                                                  "there was nothing special about it at all. "
                                                  "It was doing the best it could.")
    assert event.documents['plaintext'] == document


def test_get_document(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext']
    event = Event(event_id='1', client=client)
    document = event.documents['plaintext']
    assert document.document_name == 'plaintext'


def test_get_document_missing(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext']
    event = Event(event_id='1', client=client)
    with pytest.raises(KeyError):
        _ = event.documents['foo']


def test_get_document_missing_no_client(mocker):
    event = Event(event_id='1')
    with pytest.raises(KeyError):
        _ = event.documents['foo']


def test_iter_documents(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext', 'two', 'three']
    event = Event(event_id='1', client=client)
    documents = {document for document in event.documents}
    assert documents == {'plaintext', 'two', 'three'}


def test_contains_documents(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext', 'two', 'three']
    event = Event(event_id='1', client=client)
    assert 'plaintext' in event.documents
    assert 'two' in event.documents
    assert 'four' not in event.documents


def test_documents_len(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext', 'two', 'three']
    event = Event(event_id='1', client=client)
    assert len(event.documents) == 3
