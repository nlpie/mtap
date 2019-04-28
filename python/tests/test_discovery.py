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
from typing import Dict, Any, Optional

import grpc
import pytest
from grpc_health.v1 import health_pb2_grpc, health_pb2

import nlpnewt
import nlpnewt.constants
from nlpnewt.events import Document
from nlpnewt.processing import DocumentProcessor


@pytest.fixture
def discovery_events():
    logger = logging.getLogger()
    logger.info('Starting document service')

    server = nlpnewt.EventsServer('127.0.0.1', 0, register=True, workers=5)
    server.start()

    for i in range(10):
        try:
            with grpc.insecure_channel(f'127.0.0.1:{server.port}') as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service=nlpnewt.constants.EVENTS_SERVICE_NAME)
                response = stub.Check(request)
                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    yield
            event = server.stop()
            event.wait()
            return
        except Exception as e:
            print(e)
            logger.warning(f"Failed to connect try {i}/10. Retrying in 0.05 seconds.")
        time.sleep(0.05)

    raise ValueError('Unable to connect to documents service.')


@nlpnewt.processor('nlpnewt-discovery-test-processor')
class TestProcessor(DocumentProcessor):
    def process(self, document: Document, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        text = document.text

        with document.get_labeler('blub') as labeler:
            labeler(0, 3, x='a')
            labeler(4, 5, x='b')
            labeler(6, 7, x='c')

        return {
            'success': text == TEXT
        }


@pytest.fixture
def discovery_processor_service(discovery_events):
    logger = logging.getLogger()

    server = nlpnewt.ProcessorServer('nlpnewt-discovery-test-processor', '127.0.0.1', 0,
                                     register=True, workers=5)
    server.start()

    for i in range(10):
        try:
            with grpc.insecure_channel(f'127.0.0.1:{server.port}') as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service='nlpnewt-discovery-test-processor')
                response = stub.Check(request)
                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    yield channel
                else:
                    continue
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
def test_discover_events_service(discovery_events):
    with nlpnewt.Events() as events:
        with events.open_event('1') as e:
            e.add_document('plaintext', 'bluh')


@pytest.mark.consul
def test_discover_processor(discovery_processor_service):
    with nlpnewt.Events() as events, nlpnewt.Pipeline() as p:
        p.add_processor('nlpnewt-discovery-test-processor')
        with events.open_event(event_id='1') as event:
            doc = event.add_document(document_name='hey', text=TEXT)
            r = p.run(doc)

    assert r is not None
    print(r)
    assert r[0].results['success']
