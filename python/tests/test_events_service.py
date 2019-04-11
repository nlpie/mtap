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


def test_OpenEvent(doc_service):
    request = events_pb2.OpenEventRequest(event_id='1')
    response = doc_service.OpenEvent(request)
    assert response.created is True


def test_OpenEvent_without_id(doc_service):
    request = events_pb2.OpenEventRequest(event_id=None)
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.OpenEvent(request)
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_OpenEvent_duplicate(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    response = doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    assert response.created is False


def test_OpenEvent_only_create(doc_service):
    response = doc_service.OpenEvent(
        events_pb2.OpenEventRequest(event_id='1', only_create_new=True))
    assert response.created is True


def test_OpenEvent_only_create_duplicate(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1', only_create_new=True))
        assert excinfo.value.code() == grpc.StatusCode.ALREADY_EXISTS


def test_CloseEvent_delete(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.CloseEvent(events_pb2.CloseEventRequest(event_id='1'))
    response = doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    assert response.created is True


def test_CloseEvent_no_delete(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.CloseEvent(events_pb2.CloseEventRequest(event_id='1'))
    response = doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    assert response.created is False


def test_AddMetadataBadEvent(doc_service):
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddMetadata(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'))


def test_AddMetadata_EmptyKey(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='', value='bar'))
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_AddMetadata_NoneKey(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key=None, value='bar'))
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_GetAllMetadata(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'))
    doc_service.AddMetadata(events_pb2.AddMetadataRequest(event_id='1', key='baz', value='buh'))
    response = doc_service.GetAllMetadata(events_pb2.GetAllMetadataRequest(event_id='1'))
    d = dict(response.metadata)
    assert d == {'foo': 'bar', 'baz': 'buh'}


def test_AddDocument_bad_event(doc_service):
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                              document_name='plaintext',
                                                              text=PHASERS))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddDocument(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))


def test_AddDocument_empty_name(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                              document_name='',
                                                              text=PHASERS))
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_AddDocument_empty_text(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=''))


def test_AddDocument_exists(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                              document_name='plaintext',
                                                              text=PHASERS))
        assert excinfo.value.code() == grpc.StatusCode.ALREADY_EXISTS


def test_GetAllDocuments(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=''))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='other',
                                                          text=''))
    request = events_pb2.GetAllDocumentNamesRequest(event_id='1')
    response = doc_service.GetAllDocumentNames(request)
    document_names = list(response.document_names)
    assert document_names == ['plaintext', 'other']


def test_GetDocumentText_bad_event(doc_service):
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.GetDocumentText(events_pb2.GetDocumentTextRequest(event_id='1',
                                                                      document_name='plaintext'))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetDocumentText_bad_document(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.GetDocumentText(events_pb2.GetDocumentTextRequest(event_id='1',
                                                                      document_name='plaintext'))
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetDocumentText(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    response = doc_service.GetDocumentText(events_pb2.GetDocumentTextRequest(event_id='1',
                                                                             document_name='plaintext'))
    assert response.text == PHASERS


def test_AddLabels_bad_event(doc_service):
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddLabels(request)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddLabels_bad_document(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.AddLabels(request)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_AddLabels_bad_index_name(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
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
        doc_service.AddLabels(request)
        assert excinfo.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_AddLabels(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    doc_service.AddLabels(request)


def test_AddLabels_no_labels(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    doc_service.AddLabels(request)


def test_GetLabels_bad_event(doc_service):
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.GetLabels(r)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetLabels_bad_document_name(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.GetLabels(r)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetLabels_bad_index_name(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    with pytest.raises(grpc.RpcError) as excinfo:
        doc_service.GetLabels(r)
        assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND


def test_GetLabels_no_labels(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    doc_service.AddLabels(events_pb2.AddLabelsRequest(event_id='1',
                                                      document_name='plaintext',
                                                      index_name='labels'))
    req = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    res = doc_service.GetLabels(req)
    assert len(res.json_labels.labels) == 0


def test_GetLabels(doc_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1',
                                                          document_name='plaintext',
                                                          text=PHASERS))
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    doc_service.AddLabels(request)

    req = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    res = doc_service.GetLabels(req)
    assert len(res.json_labels.labels) == 1
    label = res.json_labels.labels[0]
    assert label['start_index'] == 15
    assert label['end_index'] == 20
    assert label['some_other_field'] == 'blah'
