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
from concurrent.futures.thread import ThreadPoolExecutor

import grpc_testing
import pytest
from grpc import StatusCode

from mtap._events_client_grpc import GrpcEventsClient
from mtap._label_indices import LabelIndexType
from mtap.api.v1 import events_pb2

EVENTS_SERVICE_DESC = events_pb2.DESCRIPTOR.services_by_name['Events']


@pytest.fixture(name='events_channel')
def fixture_events_channel():
    yield grpc_testing.channel(
        [
            EVENTS_SERVICE_DESC
        ],
        grpc_testing.strict_real_time()
    )


@pytest.fixture(name='events_client_executor')
def fixture_events_client_executor():
    with ThreadPoolExecutor(max_workers=1) as executor:
        yield executor


def test_get_label_index_info(events_channel, events_client_executor):
    def call():
        client = GrpcEventsClient(address='a', channel=events_channel)
        result = client.get_label_index_info(instance_id='0', event_id='1',
                                             document_name='plaintext')
        return result

    future = events_client_executor.submit(call)

    get_events_instance_id_method = EVENTS_SERVICE_DESC.methods_by_name['GetEventsInstanceId']
    _, req, rpc = events_channel.take_unary_unary(get_events_instance_id_method)
    rpc.send_initial_metadata(())
    response = events_pb2.GetEventsInstanceIdResponse()
    response.instance_id = '0'
    rpc.terminate(response, None, StatusCode.OK, '')

    get_label_indices_info_method = EVENTS_SERVICE_DESC.methods_by_name['GetLabelIndicesInfo']
    _, req, rpc = events_channel.take_unary_unary(get_label_indices_info_method)
    rpc.send_initial_metadata(())
    response = events_pb2.GetLabelIndicesInfoResponse()
    first = response.label_index_infos.add()
    first.index_name = 'foo'
    first.type = events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.GENERIC
    second = response.label_index_infos.add()
    second.index_name = 'bar'
    second.type = events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.CUSTOM
    third = response.label_index_infos.add()
    third.index_name = 'baz'

    rpc.terminate(response, None, StatusCode.OK, '')

    infos = future.result(timeout=1)
    assert infos is not None
    assert len(infos) == 3
    assert infos[0].index_name == 'foo'
    assert infos[0].type == LabelIndexType.GENERIC
    assert infos[1].index_name == 'bar'
    assert infos[1].type == LabelIndexType.CUSTOM
    assert infos[2].index_name == 'baz'
    assert infos[2].type == LabelIndexType.UNKNOWN


def test_get_binary_data_names(events_channel, events_client_executor):
    def call():
        client = GrpcEventsClient(address='a', channel=events_channel)
        result = client.get_all_binary_data_names(instance_id='0',
                                                  event_id='1')
        return result

    future = events_client_executor.submit(call)

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name[
            'GetEventsInstanceId']
    )
    rpc.send_initial_metadata(())
    response = events_pb2.GetEventsInstanceIdResponse()
    response.instance_id = '0'
    rpc.terminate(response, None, StatusCode.OK, '')

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name[
            'GetAllBinaryDataNames']
    )
    rpc.send_initial_metadata(())
    response = events_pb2.GetAllBinaryDataNamesResponse(
        binary_data_names=['a', 'b', 'c'])
    rpc.terminate(response, None, StatusCode.OK, '')

    assert future.result(5) == ['a', 'b', 'c']


def test_add_binary_data(events_channel, events_client_executor):
    def call():
        client = GrpcEventsClient(address='a', channel=events_channel)
        result = client.add_binary_data(instance_id='0', event_id='1',
                                        binary_data_name='foo',
                                        binary_data=b'\xFF')
        return result

    events_client_executor.submit(call)

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name[
            'GetEventsInstanceId']
    )
    rpc.send_initial_metadata(())
    response = events_pb2.GetEventsInstanceIdResponse()
    response.instance_id = '0'
    rpc.terminate(response, None, StatusCode.OK, '')

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name[
            'AddBinaryData']
    )
    rpc.send_initial_metadata(())
    response = events_pb2.AddBinaryDataResponse()
    rpc.terminate(response, None, StatusCode.OK, '')
    assert req.binary_data == b'\xFF'


def test_get_binary_data(events_channel, events_client_executor):
    def call():
        client = GrpcEventsClient(address='a', channel=events_channel)
        result = client.get_binary_data('0', event_id='1', binary_data_name='foo')
        return result

    future = events_client_executor.submit(call)

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name[
            'GetEventsInstanceId']
    )
    rpc.send_initial_metadata(())
    response = events_pb2.GetEventsInstanceIdResponse()
    response.instance_id = '0'
    rpc.terminate(response, None, StatusCode.OK, '')

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name[
            'GetBinaryData']
    )
    assert req.event_id == '1'
    assert req.binary_data_name == 'foo'
    rpc.send_initial_metadata(())
    response = events_pb2.GetBinaryDataResponse(binary_data=b'\xFF')
    rpc.terminate(response, None, StatusCode.OK, '')

    result = future.result(5)
    assert result == b'\xFF'
