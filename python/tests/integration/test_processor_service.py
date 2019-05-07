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

import subprocess
import time
from pathlib import Path

import grpc
import pytest
from grpc_health.v1 import health_pb2_grpc, health_pb2

import nlpnewt


@pytest.fixture(name='python_events')
def fixture_python_events():
    cwd = Path(__file__).parent.parent.parent
    p = subprocess.Popen(['python', 'nlpnewt', 'events', '-p', '50500'],
                         cwd=cwd)
    try:
        for i in range(10):
            try:
                with grpc.insecure_channel('127.0.0.1:50500') as channel:
                    stub = health_pb2_grpc.HealthStub(channel)
                    request = health_pb2.HealthCheckRequest(
                        service=nlpnewt.constants.EVENTS_SERVICE_NAME)
                    response = stub.Check(request)
                    if response.status == health_pb2.HealthCheckResponse.SERVING:
                        yield
                        return
            except grpc.RpcError:
                pass
            time.sleep(.05)
    finally:
        p.kill()


@pytest.fixture(name='python_processor')
def fixture_python_processor(python_events):
    cwd = Path(__file__).parent.parent.parent
    p = subprocess.Popen(['python', 'nlpnewt', 'processor', '-p', '50501',
                          '--events', '127.0.0.1:50500',
                          '--name', 'nlpnewt-example-processor-python',
                          '-m', 'nlpnewt.examples.example_processor'],
                         cwd=cwd)
    try:
        for i in range(10):
            try:
                with grpc.insecure_channel('127.0.0.1:50501') as channel:
                    stub = health_pb2_grpc.HealthStub(channel)
                    request = health_pb2.HealthCheckRequest(service='nlpnewt-example-processor-python')
                    response = stub.Check(request)
                    if response.status == health_pb2.HealthCheckResponse.SERVING:
                        yield
                        return
            except grpc.RpcError:
                pass
            time.sleep(.05)
    finally:
        p.kill()


PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us, human history would 
be far less bloody. The Enterprise computer system is controlled by three primary main processor 
cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface modules. Our 
neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you do remember 
how to fire phasers?"""


def test_pipeline(python_events, python_processor):
    with nlpnewt.Events('127.0.0.1:50500') as events, nlpnewt.Pipeline() as pipeline:
        pipeline.add_processor('nlpnewt-example-processor-python', address='localhost:50501',
                               params={'do_work': True})

        with events.open_event('1') as event:
            event.metadata['a'] = 'b'
            document = event.add_document('plaintext', PHASERS)
            results = pipeline.run(document)
            letter_counts = document.get_label_index('nlpnewt.examples.letter_counts')
            a_counts = letter_counts[0]
            pipeline.print_times()