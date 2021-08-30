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
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen, run

import pytest

from mtap.utilities import find_free_port, subprocess_events_server


@pytest.fixture(name='python_events')
def fixture_python_events():
    port = find_free_port()
    with subprocess_events_server(port=port) as address:
        yield address


@pytest.fixture(name='hello_processor')
def fixture_hello_processor(python_events, processor_watcher):
    port = find_free_port()
    p = Popen(['python', '-m', 'mtap.examples.tutorial.hello', '-p', str(port),
               '--events', python_events], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    address = "127.0.0.1:" + str(port)
    yield from processor_watcher(address=address, process=p)


@pytest.fixture(name='java_hello_processor')
def fixture_java_hello_processor(python_events, processor_watcher):
    mtap_jar = os.environ['MTAP_JAR']
    port = str(find_free_port())
    p = Popen(['java', '-cp', mtap_jar, 'edu.umn.nlpie.mtap.examples.HelloWorldExample',
               '-p', port, '--events', python_events],
              stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    address = "127.0.0.1:" + port
    yield from processor_watcher(address=address, process=p)


@pytest.mark.integration
def test_hello_world(python_events, hello_processor):
    p = run(['python', '-m', 'mtap.examples.tutorial.pipeline', python_events, hello_processor],
            stdout=PIPE)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'


@pytest.mark.integration
def test_java_hello_world(python_events, java_hello_processor):
    p = run(['python', '-m', 'mtap.examples.tutorial.pipeline', python_events,
             java_hello_processor], stdout=PIPE)
    p.check_returncode()
    assert p.stdout.decode('utf-8') == 'Hello YOUR NAME!\n'
