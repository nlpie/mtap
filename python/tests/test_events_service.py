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
import grpc_testing
import pytest

from mtap._events_service import EventsServicer
from mtap.api.v1 import events_pb2

PHASERS = """Maybe if we felt any human loss as keenly as we feel one of those close to us, human 
history would be far less bloody. The Enterprise computer system is controlled by three primary 
main processor cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface 
modules. Our neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you 
do remember how to fire phasers?"""


@pytest.fixture(name='events_server')
def fixture_events_server():
    events_service = EventsServicer()
    yield grpc_testing.server_from_dictionary(
        {
            events_pb2.DESCRIPTOR.services_by_name['Events']: events_service
        },
        grpc_testing.strict_real_time()
    )


def test_OpenEvent(events_server: grpc_testing.Server):
    request = events_pb2.OpenEventRequest(event_id='1')
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    ).termination()
    assert response.created is True


def test_OpenEvent_without_id(events_server):
    request = events_pb2.OpenEventRequest(event_id=None)
    _, _, status_code, description = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    ).termination()

    assert status_code == grpc.StatusCode.INVALID_ARGUMENT
    assert description == 'event_id was not set.'


def test_OpenEvent_duplicate(events_server):
    request = events_pb2.OpenEventRequest(event_id='1')
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    ).termination()
    assert response.created is False


def test_OpenEvent_only_create(events_server):
    request = events_pb2.OpenEventRequest(event_id='1', only_create_new=True)
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    ).termination()
    assert response.created is True


def test_OpenEvent_only_create_duplicate(events_server):
    request = events_pb2.OpenEventRequest(event_id='1', only_create_new=True)
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    )
    _, _, status_code, description = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.ALREADY_EXISTS


def test_CloseEvent_delete(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['CloseEvent'],
        {},
        events_pb2.CloseEventRequest(event_id='1'),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    ).termination()
    assert response.created is True


def test_CloseEvent_no_delete(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['CloseEvent'],
        {},
        events_pb2.CloseEventRequest(event_id='1'),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    ).termination()
    assert response.created is False


def test_AddMetadataBadEvent(events_server):
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddMetadata'],
        {},
        events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'),
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_AddMetadata(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddMetadata'],
        {},
        events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'),
        None
    ).termination()
    assert status_code == grpc.StatusCode.OK


def test_AddMetadata_EmptyKey(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddMetadata'],
        {},
        events_pb2.AddMetadataRequest(event_id='1', key='', value='bar'),
        None
    ).termination()
    assert status_code == grpc.StatusCode.INVALID_ARGUMENT


def test_AddMetadata_NoneKey(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddMetadata'],
        {},
        events_pb2.AddMetadataRequest(event_id='1', key=None, value='bar'),
        None
    ).termination()
    assert status_code == grpc.StatusCode.INVALID_ARGUMENT


def test_GetAllMetadata(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddMetadata'],
        {},
        events_pb2.AddMetadataRequest(event_id='1', key='foo', value='bar'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddMetadata'],
        {},
        events_pb2.AddMetadataRequest(event_id='1', key='baz', value='buh'),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetAllMetadata'],
        {},
        events_pb2.GetAllMetadataRequest(event_id='1'),
        None
    ).termination()
    d = dict(response.metadata)
    assert d == {'foo': 'bar', 'baz': 'buh'}


def test_GetAllBinaryDataNames(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddBinaryData'],
        {},
        events_pb2.AddBinaryDataRequest(event_id='1',
                                        binary_data_name='a',
                                        binary_data=b'\xBF\xAF'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddBinaryData'],
        {},
        events_pb2.AddBinaryDataRequest(event_id='1',
                                        binary_data_name='b',
                                        binary_data=b'\xAF\xBF'),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetAllBinaryDataNames'],
        {},
        events_pb2.GetAllBinaryDataNamesRequest(event_id='1'),
        None
    ).termination()
    assert 'a' in response.binary_data_names
    assert 'b' in response.binary_data_names
    assert len(response.binary_data_names) == 2


def test_AddGetBinaryData(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddBinaryData'],
        {},
        events_pb2.AddBinaryDataRequest(event_id='1',
                                        binary_data_name='a',
                                        binary_data=b'\xBF\xAF'),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetBinaryData'],
        {},
        events_pb2.GetBinaryDataRequest(event_id='1', binary_data_name='a'),
        None
    ).termination()
    assert response.binary_data == b'\xBF\xAF'


def test_AddDocument_bad_event(events_server):
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_AddDocument(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    ).termination()
    assert status_code == grpc.StatusCode.OK


def test_AddDocument_empty_name(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='',
                                      text=PHASERS),
        None
    ).termination()
    assert status_code == grpc.StatusCode.INVALID_ARGUMENT


def test_AddDocument_empty_text(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=''),
        None
    ).termination()
    assert status_code == grpc.StatusCode.OK


def test_AddDocument_exists(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    ).termination()
    assert status_code == grpc.StatusCode.ALREADY_EXISTS


def test_GetAllDocuments(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=''),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='other',
                                      text=''),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetAllDocumentNames'],
        {},
        events_pb2.GetAllDocumentNamesRequest(event_id='1'),
        None
    ).termination()
    assert 'plaintext' in response.document_names
    assert 'other' in response.document_names
    assert len(response.document_names) == 2


def test_GetDocumentText_bad_event(events_server):
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetDocumentText'],
        {},
        events_pb2.GetDocumentTextRequest(event_id='1',
                                          document_name='plaintext'),
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetDocumentText_bad_document(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetDocumentText'],
        {},
        events_pb2.GetDocumentTextRequest(event_id='1',
                                          document_name='plaintext'),
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetDocumentText(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    response, _, _, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetDocumentText'],
        {},
        events_pb2.GetDocumentTextRequest(event_id='1',
                                          document_name='plaintext'),
        None
    ).termination()
    assert response.text == PHASERS


def test_GetLabelIndicesInfo_bad_event(events_server):
    request = events_pb2.GetLabelIndicesInfoRequest(event_id='1', document_name='plaintext')

    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabelIndicesInfo'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetLabelIndicesInfo_bad_document(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    request = events_pb2.GetLabelIndicesInfoRequest(event_id='1', document_name='plaintext')

    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabelIndicesInfo'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetLabelIndicesInfo(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    )
    request = events_pb2.GetLabelIndicesInfoRequest(event_id='1', document_name='plaintext')
    res, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabelIndicesInfo'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.OK
    assert len(res.label_index_infos) == 1
    assert res.label_index_infos[0].index_name == 'labels'
    assert res.label_index_infos[0].type == events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.JSON


def test_AddLabels_bad_event(events_server):
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_AddLabels_bad_document(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_AddLabels_bad_index_name(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='')
    label = request.json_labels.labels.add()
    label['start_index'] = 15
    label['end_index'] = 20
    label['some_other_field'] = 'blah'

    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.INVALID_ARGUMENT


def test_AddLabels(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.OK


def test_AddLabels_no_labels(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    ).termination()
    assert status_code == grpc.StatusCode.OK


def test_GetLabels_bad_event(events_server):
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabels'],
        {},
        r,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetLabels_bad_document_name(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabels'],
        {},
        r,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetLabels_bad_index_name(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    r = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    _, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabels'],
        {},
        r,
        None
    ).termination()
    assert status_code == grpc.StatusCode.NOT_FOUND


def test_GetLabels_no_labels(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        events_pb2.AddLabelsRequest(event_id='1',
                                    document_name='plaintext',
                                    index_name='labels'),
        None
    )
    req = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    res, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabels'],
        {},
        req,
        None
    ).termination()
    assert len(res.json_labels.labels) == 0


def test_GetLabels(events_server):
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['OpenEvent'],
        {},
        events_pb2.OpenEventRequest(event_id='1'),
        None
    )
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddDocument'],
        {},
        events_pb2.AddDocumentRequest(event_id='1',
                                      document_name='plaintext',
                                      text=PHASERS),
        None
    )
    request = events_pb2.AddLabelsRequest(event_id='1',
                                          document_name='plaintext',
                                          index_name='labels')
    s = request.json_labels.labels.add()
    s['start_index'] = 15
    s['end_index'] = 20
    s['some_other_field'] = 'blah'
    events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['AddLabels'],
        {},
        request,
        None
    )

    req = events_pb2.GetLabelsRequest(event_id='1', document_name='plaintext', index_name='labels')
    res, _, status_code, _ = events_server.invoke_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabels'],
        {},
        req,
        None
    ).termination()
    assert len(res.json_labels.labels) == 1
    label = res.json_labels.labels[0]
    assert label['start_index'] == 15
    assert label['end_index'] == 20
    assert label['some_other_field'] == 'blah'
