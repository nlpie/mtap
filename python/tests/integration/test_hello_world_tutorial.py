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
import os
import signal
import subprocess
import time
from pathlib import Path

import grpc
import pytest
import requests
from requests import RequestException

import nlpnewt
from nlpnewt import RemoteProcessor, EventsClient, Event
from nlpnewt.utils import find_free_port, subprocess_events_server


@pytest.fixture(name='python_events')
def fixture_python_events():
    config_path = Path(__file__).parent / 'integrationConfig.yaml'
    with subprocess_events_server(port=50500, cwd=Path(__file__).parents[2],
                                  config_path=config_path) as address:
        yield address


@pytest.fixture(name='hello_processor')
def fixture_hello_processor(python_events):
    cwd = Path(__file__).parents[2]
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    port = find_free_port()
    p = subprocess.Popen(['python', '-m', 'nlpnewt.examples.tutorial.hello',
                          '-p', str(port),
                          '--events', python_events],
                         start_new_session=True, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         cwd=cwd, env=env)
    try:
        address = "127.0.0.1:" + str(port)
        with grpc.insecure_channel(address) as channel:
            future = grpc.channel_ready_future(channel)
            future.result(timeout=10)
        yield address
    finally:
        p.send_signal(signal.SIGINT)
        try:
            stdout, _ = p.communicate(timeout=1)
            print("python processor exited with code: ", p.returncode)
            print(stdout.decode('utf-8'))
        except subprocess.TimeoutExpired:
            print("timed out waiting for python processor to terminate")


@pytest.mark.integration
def test_hello_world(python_events, hello_processor):
    p = subprocess.run(['python', '-m', 'nlpnewt.examples.tutorial.pipeline', python_events, hello_processor],
                       capture_output=True)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'
