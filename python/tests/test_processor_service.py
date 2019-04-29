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

import datetime
import time
from typing import Dict

import grpc
import pytest
from grpc_health.v1 import health_pb2_grpc, health_pb2

import nlpnewt
from nlpnewt.api.v1 import processing_pb2_grpc, events_pb2, processing_pb2
from nlpnewt.events import Document
from nlpnewt.processing import DocumentProcessor, ProcessorContext


@nlpnewt.processor('nlpnewt-test-processor')
class ProcessorWithContext(DocumentProcessor):
    def __init__(self, context: ProcessorContext):
        self.context = context

    def process(self, document: Document, params: Dict[str, str]):
        with self.context.stopwatch('fetch_document'):
            text = document.text
        with document.get_labeler('blub') as labeler:
            labeler(0, 3, x='a')
            labeler(4, 5, x='b')
            labeler(6, 7, x='c')


@pytest.fixture
def processor_service(events):
    server = nlpnewt.ProcessorServer('nlpnewt-test-processor', '127.0.0.1', 0,
                                     processor_id='nlpnewt-test-processor-id',
                                     workers=5,
                                     events_address=events[0])
    server.start()
    for i in range(10):
        try:
            address = f'127.0.0.1:{server.port}'
            with grpc.insecure_channel(address) as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service='nlpnewt-test-processor-id')
                response = stub.Check(request)
                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    yield address, channel
            event = server.stop()
            event.wait()
            return
        except:
            print(f"Failed to connect try {i}/10. Retrying in 0.05 seconds.")
        time.sleep(0.05)

    raise ValueError('Unable to connect to started processor service.')


PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us, human history would 
be far less bloody. The Enterprise computer system is controlled by three primary main processor 
cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface modules. Our 
neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you do remember 
how to fire phasers?"""


def test_processor_service(events, processor_service):
    events_host, events_service = events
    events_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    events_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1', document_name='hey',
                                                             text=PHASERS))

    request = processing_pb2.ProcessRequest(processor_id='nlpnewt-test-processor-id', event_id='1')
    request.params['document_name'] = 'hey'
    processor_stub = processing_pb2_grpc.ProcessorStub(processor_service[1])
    processor_stub.Process(request)

    r = events_service.GetLabels(events_pb2.GetLabelsRequest(event_id='1', document_name='hey',
                                                             index_name='blub'))
    assert r is not None


def test_get_info(processor_service):
    processor_stub = processing_pb2_grpc.ProcessorStub(processor_service[1])
    info = processor_stub.GetInfo(processing_pb2.GetInfoRequest(processor_id='nlpnewt-test-processor-id'))
    assert info.name == 'nlpnewt-test-processor'
    assert info.identifier == 'nlpnewt-test-processor-id'


def test_pipeline_client(events, processor_service):
    events_host, events_service = events
    with nlpnewt.Pipeline() as p, nlpnewt.Events(events_host) as events:
        p.add_processor('nlpnewt-test-processor-id', processor_service[0])
        event = events.open_event('1')
        doc = event.add_document('hey', PHASERS)

        r = p.run(doc)
        processor_timer_stats = p.processor_timer_stats()
        pipeline_timer_stats = p.pipeline_timer_stats()
        remote_call_time = r[0].timing_info['nlpnewt-test-processor-id-1:remote_call']
        process_method_time = r[0].timing_info[
            'nlpnewt-test-processor-id-1:nlpnewt-test-processor-id:process_method']
        assert remote_call_time > process_method_time
        first_component_stats = processor_timer_stats[0]
        assert first_component_stats.identifier == 'nlpnewt-test-processor-id-1'
        assert first_component_stats.timing_info['remote_call'].std == datetime.timedelta(seconds=0)
        assert first_component_stats.timing_info['remote_call'].mean == remote_call_time
        assert first_component_stats.timing_info['remote_call'].max == remote_call_time
        assert first_component_stats.timing_info['remote_call'].sum == remote_call_time
        assert first_component_stats.timing_info['remote_call'].min == remote_call_time
        assert pipeline_timer_stats.timing_info['total'].mean > remote_call_time

    events_service.GetLabels(events_pb2.GetLabelsRequest(event_id='1', document_name='hey',
                                                         index_name='blub'))
