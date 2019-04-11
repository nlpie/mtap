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
from nlpnewt.api.v1 import health_pb2, health_pb2_grpc, events_pb2_grpc


def pytest_addoption(parser):
    parser.addoption(
        "--consul", action="store_true", default=False, help="runs tests that require consul"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--consul"):
        skip_consul = pytest.mark.skip(reason="need --consul option to run")
        for item in items:
            if "consul" in item.keywords:
                item.add_marker(skip_consul)


@pytest.fixture
def doc_service():
    logger = logging.getLogger()
    logger.info('Starting document service')

    server = nlpnewt.events_server('localhost', 50051, workers=5)
    server.start(register=False)

    for i in range(10):
        try:
            with grpc.insecure_channel('localhost:50051') as channel:
                stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service=nlpnewt.events_service_name())
                response = stub.Check(request)
                if response.status == health_pb2.HealthCheckResponse.SERVING:
                    yield events_pb2_grpc.EventsStub(channel)
            event = server.stop()
            event.wait()
            return
        except Exception as e:
            logger.warning(f"Failed to connect try {i}/10. Retrying in .05 seconds.")
            time.sleep(.05)

    raise ValueError('Unable to connect to documents service.')
