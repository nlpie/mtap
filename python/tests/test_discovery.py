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
import nlpnewt.base
import nlpnewt.constants
from nlpnewt.api.v1 import health_pb2_grpc, health_pb2


@pytest.fixture
def discovery_events():
    logger = logging.getLogger()
    logger.info('Starting document service')

    server = nlpnewt.events_server('127.0.0.1', 0, workers=5)
    server.start(register=True)

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
class TestProcessor(nlpnewt.base.DocumentProcessor):
    def process_document(self, document, params):
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

    server = nlpnewt.processor_server('nlpnewt-discovery-test-processor', '127.0.0.1', 0, workers=5)
    server.start(register=True)

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
    with nlpnewt.events() as events:
        with events.open_event('1') as e:
            e.add_document('plaintext', 'bluh')


@pytest.mark.consul
def test_discover_processor(discovery_processor_service):
    with nlpnewt.events() as events, nlpnewt.pipeline() as p:
        p.add_processor('nlpnewt-discovery-test-processor')
        with events.open_event(event_id='1') as event:
            doc = event.add_document(document_name='hey', text=TEXT)
            r = p.run(doc)

    assert r is not None
    print(r)
    assert r[0].results['success']
