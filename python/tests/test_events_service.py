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

import grpc
import pytest

from nlpnewt.api.v1 import events_pb2

PHASERS = """Maybe if we felt any human loss as keenly as we feel one of those close to us, human 
history would be far less bloody. The Enterprise computer system is controlled by three primary 
main processor cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface 
modules. Our neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you 
do remember how to fire phasers?"""


def test_OpenEvent(events):
    request = events_pb2.OpenEventRequest(event_id='1')
    response = events[1].OpenEvent(request)
    assert response.created is True


def test_OpenEvent_without_id(events):
    request = events_pb2.OpenEventRequest(event_id=None)
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].OpenEvent(request)
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_OpenEvent_duplicate(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    response = events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    assert response.created is False


def test_OpenEvent_only_create(events):
    response = events[1].OpenEvent(
        events_pb2.OpenEventRequest(event_id='1', only_create_new=True))
    assert response.created is True


def test_OpenEvent_only_create_duplicate(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1', only_create_new=True))
        assert excinfo.value.code() == grpc.StatusCode.ALREADY_EXISTS


def test_CloseEvent_delete(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].CloseEvent(events_pb2.CloseEventRequest(event_id='1'))
    response = events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    assert response.created is True


def test_CloseEvent_no_delete(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].CloseEvent(events_pb2.CloseEventRequest(event_id='1'))
    response = events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    assert response.created is False


def test_AddMetadataBadEvent(events):
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddMetadata(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'))


def test_AddMetadata_EmptyKey(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='', value='bar'))
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_AddMetadata_NoneKey(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key=None, value='bar'))
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_GetAllMetadata(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'))
    events[1].AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='baz', value='buh'))
    response = events[1].GetAllMetadata(events_pb2.GetAllMetadataRequest(event_id='1'))
    d = dict(response.metadata)
    assert d == {'foo': 'bar', 'baz': 'buh'}


def test_AddDocument_bad_event(events):
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                         document_name='plaintext',
                                                         text=PHASERS))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddDocument(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))


def test_AddDocument_empty_name(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                         document_name='',
                                                         text=PHASERS))
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_AddDocument_empty_text(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=''))


def test_AddDocument_exists(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                         document_name='plaintext',
                                                         text=PHASERS))
        assert excinfo.value.code() == grpc.StatusCode.ALREADY_EXISTS


def test_GetAllDocuments(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=''))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='other',
                                                     text=''))
    request = events_pb2.GetAllDocumentNamesRequest(event_id='1')
    response = events[1].GetAllDocumentNames(request)
    document_names = list(response.document_names)
    assert document_names == ['plaintext', 'other']


def test_GetDocumentText_bad_event(events):
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].GetDocumentText(events_pb2.GetDocumentTextRequest(event_id='1',
                                                                 document_name='plaintext'))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetDocumentText_bad_document(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].GetDocumentText(events_pb2.GetDocumentTextRequest(event_id='1',
                                                                 document_name='plaintext'))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetDocumentText(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    response = events[1].GetDocumentText(events_pb2.GetDocumentTextRequest(event_id='1',
                                                                        document_name='plaintext'))
    assert response.text == PHASERS


def test_AddLabels_bad_event(events):
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddLabels(request)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddLabels_bad_document(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddLabels(request)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddLabels_bad_index_name(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].AddLabels(request)
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_AddLabels(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    events[1].AddLabels(request)


def test_AddLabels_no_labels(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    events[1].AddLabels(request)


def test_GetLabels_bad_event(events):
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].GetLabels(r)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetLabels_bad_document_name(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].GetLabels(r)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetLabels_bad_index_name(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    with pytest.raises(grpc.RpcError) as excinfo:
        events[1].GetLabels(r)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetLabels_no_labels(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    events[1].AddLabels(events_pb2.AddLabelsRequest(event_id='1',
                                                 document_name='plaintext',
                                                 index_name='labels'))
    req = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    res = events[1].GetLabels(req)
    assert len(res.json_labels.labels) == 0


def test_GetLabels(events):
    events[1].OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events[1].AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                     document_name='plaintext',
                                                     text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    events[1].AddLabels(request)

    req = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    res = events[1].GetLabels(req)
    assert len(res.json_labels.labels) == 1
    label = res.json_labels.labels[0]
    assert label['start_index'] == 15
    assert label['end_index'] == 20
    assert label['some_other_field'] == 'blah'
