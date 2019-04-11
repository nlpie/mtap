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
import logging
import time
import typing as _typing

import grpc
import pytest

import nlpnewt
from nlpnewt import Document
from nlpnewt.api.v1 import health_pb2_grpc, health_pb2, processing_pb2_grpc, events_pb2, \
    processing_pb2


@nlpnewt.processor('nlpnewt-test-processor')
class TestProcessor(nlpnewt.DocumentProcessor):
    def process_document(self, document: Document, params: _typing.Dict[str, str]):
        text = document.text

        with document.get_labeler('blub') as labeler:
            labeler(0, 3, x='a')
            labeler(4, 5, x='b')
            labeler(6, 7, x='c')


@pytest.fixture
def processor_service(doc_service):
    logger = logging.getLogger()

    server = nlpnewt.processor_server('nlpnewt-test-processor', 'localhost', 50052, workers=5,
                                      events_address='localhost:50051')
    server.start(register=False)
    time.sleep(1)
    for i in range(10):
        try:
            with grpc.insecure_channel('localhost:50052') as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service='nlpnewt-test-processor')
                response = stub.Check(request)
                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    yield channel
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


def test_processor_service(doc_service, processor_service):
    doc_service.OpenEvent(events_pb2.OpenEventRequest(event_id='1'))
    doc_service.AddDocument(events_pb2.AddDocumentRequest(event_id='1', document_name='hey',
                                                          text=PHASERS))

    request = processing_pb2.ProcessRequest(processor_name='nlpnewt-test-processor', event_id='1')
    request.params['document_name'] = 'hey'
    processor_stub = processing_pb2_grpc.ProcessorStub(processor_service)
    processor_stub.Process(request)

    r = doc_service.GetLabels(events_pb2.GetLabelsRequest(event_id='1', document_name='hey',
                                                          index_name='blub'))
    assert r is not None


def test_pipeline_client(doc_service, processor_service):
    with nlpnewt.pipeline() as p, nlpnewt.events('localhost:50051') as events:
        p.add_processor('nlpnewt-test-processor', 'localhost:50052')
        event = events.open_event('1')
        doc = event.add_document('hey', PHASERS)

        r = p.run(doc)
        processor_timer_stats = p.processor_timer_stats()
        pipeline_timer_stats = p.pipeline_timer_stats()
        remote_call_time = r[0].timing_info['nlpnewt-test-processor-1:remote_call']
        process_method_time = r[0].timing_info[
            'nlpnewt-test-processor-1:nlpnewt-test-processor:process_method']
        assert remote_call_time > process_method_time
        first_component_stats = processor_timer_stats[0]
        assert first_component_stats.identifier == 'nlpnewt-test-processor-1'
        assert first_component_stats.timing_info['remote_call'].std == datetime.timedelta(seconds=0)
        assert first_component_stats.timing_info['remote_call'].mean == remote_call_time
        assert first_component_stats.timing_info['remote_call'].max == remote_call_time
        assert first_component_stats.timing_info['remote_call'].sum == remote_call_time
        assert first_component_stats.timing_info['remote_call'].min == remote_call_time
        assert pipeline_timer_stats.timing_info['total'].mean > remote_call_time

    doc_service.GetLabels(events_pb2.GetLabelsRequest(event_id='1', document_name='hey',
                                                      index_name='blub'))
