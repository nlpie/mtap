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

from nlpnewt.api.v1 import events_pb2, events_pb2_grpc
from nlpnewt.events import EventsClient, LabelIndexType


@pytest.fixture(name='events_channel')
def fixture_events_channel():
    yield grpc_testing.channel(
        [
            events_pb2.DESCRIPTOR.services_by_name['Events']
        ],
        grpc_testing.strict_real_time()
    )


@pytest.fixture(name='events_client_executor')
def fixture_events_client_executor():
    executor = ThreadPoolExecutor(max_workers=1)
    yield executor
    executor.shutdown(wait=True)


def test_get_label_index_info(events_channel, events_client_executor):
    def call():
        client = EventsClient(stub=events_pb2_grpc.EventsStub(events_channel))
        result = client.get_label_index_info(event_id='1', document_name='plaintext')
        return result

    future = events_client_executor.submit(call)

    _, req, rpc = events_channel.take_unary_unary(
        events_pb2.DESCRIPTOR.services_by_name['Events'].methods_by_name['GetLabelIndicesInfo']
    )
    rpc.send_initial_metadata(())
    response = events_pb2.GetLabelIndicesInfoResponse()
    first = response.label_index_infos.add()
    first.index_name = 'foo'
    first.type = events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.JSON
    second = response.label_index_infos.add()
    second.index_name = 'bar'
    second.type = events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.OTHER
    third = response.label_index_infos.add()
    third.index_name = 'baz'

    rpc.terminate(response, None, StatusCode.OK, '')

    infos = future.result()
    assert infos is not None
    assert len(infos) == 3
    assert infos[0].index_name == 'foo'
    assert infos[0].type == LabelIndexType.JSON
    assert infos[1].index_name == 'bar'
    assert infos[1].type == LabelIndexType.OTHER
    assert infos[2].index_name == 'baz'
    assert infos[2].type == LabelIndexType.UNKNOWN

