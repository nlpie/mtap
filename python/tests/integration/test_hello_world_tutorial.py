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
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired, run

import grpc
import pytest

from nlpnewt.utils import find_free_port, subprocess_events_server


@pytest.fixture(name='python_events')
def fixture_python_events():
    port = find_free_port()
    with subprocess_events_server(port=port) as address:
        yield address


@pytest.fixture(name='hello_processor')
def fixture_hello_processor(python_events):
    port = find_free_port()
    p = Popen(['python', '-m', 'nlpnewt.examples.tutorial.hello', '-p', str(port),
               '--events', python_events],
              start_new_session=True, stdin=PIPE,
              stdout=PIPE, stderr=STDOUT)
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
        except TimeoutExpired:
            print("timed out waiting for python processor to terminate")


@pytest.fixture(name='java_hello_processor')
def fixture_java_hello_processor(python_events):
    newt_jar = Path(os.environ['NEWT_JAR'])
    port = str(find_free_port())
    p = Popen(['java', '-cp', newt_jar, 'edu.umn.nlpnewt.examples.HelloWorldExample',
               '-p', port, '--events', python_events], start_new_session=True, stdin=PIPE,
              stdout=PIPE, stderr=STDOUT)
    try:
        address = "127.0.0.1:" + port
        with grpc.insecure_channel(address) as channel:
            future = grpc.channel_ready_future(channel)
            future.result(timeout=10)
        yield address
    finally:
        p.send_signal(signal.SIGINT)
        try:
            stdout, _ = p.communicate(timeout=1)
            print("java processor exited with code: ", p.returncode)
            print(stdout.decode('utf-8'))
        except TimeoutExpired:
            print("timed out waiting for java processor to terminate")


@pytest.mark.integration
def test_hello_world(python_events, hello_processor):
    p = run(['python', '-m', 'nlpnewt.examples.tutorial.pipeline', python_events, hello_processor],
            capture_output=True)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'


@pytest.mark.integration
def test_java_hello_world(python_events, java_hello_processor):
    p = run(['python', '-m', 'nlpnewt.examples.tutorial.pipeline', python_events,
             java_hello_processor], capture_output=True)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'
