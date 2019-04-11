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

import logging
import time

import grpc
import pytest

import nlpnewt
from nlpnewt.api.v1 import health_pb2_grpc, health_pb2


@pytest.fixture
def events_service():
    logger = logging.getLogger()
    logger.info('Starting document service')

    server = nlpnewt.events_server('localhost', 50051, workers=5)
    server.start(register=True)

    for i in range(10):
        try:
            with grpc.insecure_channel('localhost:50051') as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service=nlpnewt.events_service_name())
                response = stub.Check(request)
                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    nlpnewt.events()
                    yield channel
            event = server.stop()
            event.wait()
            return
        except Exception as e:
            print(e)
            logger.warning(f"Failed to connect try {i}/10. Retrying in 0.05 seconds.")
        time.sleep(0.05)

    raise ValueError('Unable to connect to documents service.')


@nlpnewt.processor('nlpnewt-test-processor')
class TestProcessor(nlpnewt.DocumentProcessor):
    def process_document(self, document, params):
        text = document.text

        with document.get_labeler('blub') as labeler:
            labeler(0, 3, x='a')
            labeler(4, 5, x='b')
            labeler(6, 7, x='c')


@pytest.fixture
def processor_service(events_service):
    logger = logging.getLogger()

    server = nlpnewt.processor_server('nlpnewt-test-processor', 'localhost', 50052, workers=5)
    server.start(register=True)

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
        except Exception as e:
            print(e)
            logger.warning(f"Failed to connect try {i}/10. Retrying in 0.05 seconds.")
        time.sleep(0.05)

    raise ValueError('Unable to connect to started processor service.')


TEXT = """
Maybe if we felt any human loss as keenly as we feel one of those close to us, human history would 
be far less bloody. The Enterprise computer system is controlled by three primary main processor 
cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface modules. Our 
neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you do remember 
how to fire phasers?"""


@pytest.mark.consul
def test_discover_events_service(events_service):
    with nlpnewt.events() as events:
        with events.open_event('1') as e:
            e.add_document('plaintext', 'bluh')


@pytest.mark.consul
def test_discover_processor(processor_service):
    with nlpnewt.events() as events, nlpnewt.pipeline(['nlpnewt-test-processor']) as p:
        with events.open_event(event_id='1') as event:
            doc = event.add_document(document_name='hey', text=TEXT)
            r = p.process_document(doc)

    assert r is not None
