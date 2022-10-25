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
import sys
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

import pytest

from mtap import EventsClient, RemoteProcessor, Pipeline, Event, GenericLabel
from mtap.utilities import subprocess_events_server, find_free_port


@pytest.fixture(name='python_events')
def fixture_python_events():
    with subprocess_events_server(cwd=Path(__file__).parents[2]) as address:
        yield address


@pytest.fixture(name='python_references_processor')
def fixture_python_references_processor(python_events, processor_watcher):
    env = dict(os.environ)
    port = str(find_free_port())
    p = Popen([sys.executable, '-m', 'mtap.examples.example_references_processor', '-p', port,
               '--events', python_events, '--log-level', 'DEBUG'], stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env)
    yield from processor_watcher(address="127.0.0.1:" + port, process=p)


@pytest.fixture(name="java_references_processor")
def fixture_java_references_processor(java_exe, python_events, processor_watcher):
    env = dict(os.environ)
    port = str(find_free_port())
    p = Popen(java_exe + ['edu.umn.nlpie.mtap.examples.ReferenceLabelsExampleProcessor',
                          '-p', port, '-e', python_events], stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env)
    yield from processor_watcher(address="127.0.0.1:" + port, process=p)


@pytest.mark.integration
def test_java_references(python_events, java_references_processor):
    with EventsClient(address=python_events) as client, Pipeline(
            RemoteProcessor('mtap-java-reference-labels-example-processor',
                            address=java_references_processor)
    ) as pipeline:
        with Event(event_id='1', client=client) as event:
            document = event.create_document('plaintext', 'abcd')
            pipeline.run(document)
            references = document.labels['references']
            assert references[0].a == GenericLabel(0, 1)
            assert references[0].b == GenericLabel(1, 2)
            assert references[1].a == GenericLabel(2, 3)
            assert references[1].b == GenericLabel(3, 4)

            map_references = document.labels['map_references']
            assert map_references[0].ref == {
                'a': GenericLabel(0, 1),
                'b': GenericLabel(1, 2),
                'c': GenericLabel(2, 3),
                'd': GenericLabel(3, 4)
            }

            list_references = document.labels['list_references']
            assert list_references[0].ref == [GenericLabel(0, 1), GenericLabel(1, 2)]
            assert list_references[1].ref == [GenericLabel(2, 3), GenericLabel(3, 4)]


@pytest.mark.integration
def test_python_references(python_events, python_references_processor):
    with EventsClient(address=python_events) as client, Pipeline(
            RemoteProcessor('mtap-python-references-example', address=python_references_processor)
    ) as pipeline:
        with Event(event_id='1', client=client) as event:
            document = event.create_document('plaintext', 'abcd')
            pipeline.run(document)
            references = document.labels['references']
            assert references[0].a == GenericLabel(0, 1)
            assert references[0].b == GenericLabel(1, 2)
            assert references[1].a == GenericLabel(2, 3)
            assert references[1].b == GenericLabel(3, 4)

            map_references = document.labels['map_references']
            assert map_references[0].ref == {
                'a': GenericLabel(0, 1),
                'b': GenericLabel(1, 2),
                'c': GenericLabel(2, 3),
                'd': GenericLabel(3, 4)
            }

            list_references = document.labels['list_references']
            assert list_references[0].ref == [GenericLabel(0, 1), GenericLabel(1, 2)]
            assert list_references[1].ref == [GenericLabel(2, 3), GenericLabel(3, 4)]
