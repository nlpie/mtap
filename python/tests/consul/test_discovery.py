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

import sys
import time
from pathlib import Path
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT

import pytest
import requests
from requests import RequestException

import mtap
from mtap import events_client, Event, RemoteProcessor, utilities
from mtap.utilities import subprocess_events_server


@pytest.fixture(name='disc_python_events', scope='module')
def fixture_disc_python_events():
    with subprocess_events_server(cwd=Path(__file__).parents[2],
                                  register=True) as address:
        yield address


@pytest.fixture(name='disc_python_processor', scope='module')
def fixture_disc_python_processor(disc_python_events, processor_watcher):
    p = Popen([sys.executable, '-m', 'mtap.examples.example_processor',
               '-p', '50501', '--register'],
              start_new_session=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    yield from processor_watcher(address="127.0.0.1:50501", process=p)


@pytest.fixture(name="disc_java_processor", scope='module')
def fixture_disc_java_processor(java_exe, disc_python_events,
                                processor_watcher):
    p = Popen(java_exe + [
        'edu.umn.nlpie.mtap.examples.WordOccurrencesExampleProcessor', '-p',
        '50502', '--register'],
              stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    yield from processor_watcher(address="127.0.0.1:50502", process=p)


@pytest.fixture(name="disc_api_gateway", scope='module')
def fixture_disc_api_gateway(disc_python_events, disc_python_processor,
                             disc_java_processor):
    port = utilities.find_free_port()
    address = f"127.0.0.1:{port}"
    p = Popen(['mtap-gateway', '-mtap-config',
               str(Path(__file__).parent / 'integrationConfig.yaml'),
               '-port', str(port),
               '-logtostderr', '-v=3'], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    session = requests.Session()
    session.trust_env = False
    try:
        if p.returncode is not None:
            raise ValueError("Failed to launch go gateway")
        for i in range(6):
            if i == 5:
                raise ValueError("Failed to connect to go gateway")
            try:
                time.sleep(3)
                resp = session.get(f"http://{address}/v1/processors",
                                   timeout=10)
                if resp.status_code == 200 and len(
                        resp.json()['Processors']) == 2:
                    break
            except RequestException:
                pass
        yield address
    finally:
        session.close()
        p.terminate()
        try:
            stdout, _ = p.communicate(timeout=1)
            print("api gateway exited with code: ", p.returncode)
            print(stdout.decode('utf-8'))
        except TimeoutExpired:
            print("timed out waiting for api gateway to terminate")
            p.kill()
            stdout, _ = p.communicate()
            print("api gateway exited with code: ", p.returncode)
            print(stdout.decode('utf-8'))


PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us, human history would 
be far less bloody. The Enterprise computer system is controlled by three primary main processor 
cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface modules. Our 
neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you do remember 
how to fire phasers?"""


@pytest.mark.consul
def test_disc_pipeline(disc_python_events, disc_python_processor,
                       disc_java_processor):
    pipeline = mtap.Pipeline(
        RemoteProcessor('mtap-example-processor-python',
                        address='localhost:50501',
                        params={'do_work': True}),
        RemoteProcessor('mtap-example-processor-java',
                        address='localhost:50502',
                        params={'do_work': True})
    )
    with events_client() as client:
        with Event(event_id='1', client=client) as event:
            event.metadata['a'] = 'b'
            document = event.create_document('plaintext', PHASERS)
            result = pipeline.run_multithread([document])
            letter_counts = document.labels['mtap.examples.letter_counts']
            a_counts = letter_counts[0]
            assert a_counts.count == 23
            b_counts = letter_counts[1]
            assert b_counts.count == 6
            result.print_times()
            thes = document.labels["mtap.examples.word_occurrences"]
            assert thes[0].start_index == 121
            assert thes[0].end_index == 124


@pytest.mark.consul
def test_disc_api_gateway(disc_api_gateway):
    session = requests.Session()
    session.trust_env = False
    resp = session.get(f"http://{disc_api_gateway}/v1/processors", timeout=10)
    assert resp.status_code == 200
    processors = resp.json()
    all_ids = []
    for processor in processors['Processors']:
        all_ids.append(processor['Identifier'])
    assert 'mtap-example-processor-python' in all_ids
    assert 'mtap-example-processor-java' in all_ids
