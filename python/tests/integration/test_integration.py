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
import time
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

import pytest
import requests
from requests import RequestException

import mtap
from mtap import RemoteProcessor, EventsClient, Event
from mtap.utilities import subprocess_events_server


@pytest.fixture(name='python_events')
def fixture_python_events():
    config_path = Path(__file__).parent / 'integrationConfig.yaml'
    with subprocess_events_server(port=50500, cwd=Path(__file__).parents[2],
                                  config_path=config_path) as address:
        yield address


@pytest.fixture(name='python_processor')
def fixture_python_processor(python_events, processor_watcher):
    env = dict(os.environ)
    env['MTAP_CONFIG'] = str(Path(__file__).parent / 'integrationConfig.yaml')
    p = Popen(['python', '-m', 'mtap.examples.example_processor', '-p', '50501',
               '--events', python_events], stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env)
    yield from processor_watcher(address="127.0.0.1:50501", process=p)


@pytest.fixture(name="java_processor")
def fixture_java_processor(python_events, processor_watcher):
    mtap_jar = os.environ['MTAP_JAR']
    env = dict(os.environ)
    env['MTAP_CONFIG'] = str(Path(__file__).parent / 'integrationConfig.yaml')
    p = Popen(['java', '-cp', mtap_jar,
               'edu.umn.nlpie.mtap.examples.WordOccurrencesExampleProcessor',
               '-p', '50502', '-e', python_events], stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env)
    yield from processor_watcher(address="127.0.0.1:50502", process=p)


@pytest.fixture(name="api_gateway")
def fixture_api_gateway(python_events, python_processor, java_processor):
    env = dict(os.environ)
    env['MTAP_CONFIG'] = str(Path(__file__).parent / 'integrationConfig.yaml')
    p = Popen(['mtap-gateway', '-logtostderr', '-v=3'], stdin=PIPE, stdout=PIPE, stderr=STDOUT,
              env=env)
    try:
        if p.returncode is not None:
            raise ValueError("Failed to launch go gateway")
        for i in range(6):
            if i == 5:
                raise ValueError("Failed to connect to go gateway")
            try:
                time.sleep(3)
                resp = requests.get("http://localhost:50503/v1/processors")
                if resp.status_code == 200 and len(resp.json()['Processors']) == 2:
                    break
            except RequestException:
                pass
        yield
    finally:
        p.send_signal(signal.SIGINT)
        try:
            stdout, _ = p.communicate(timeout=1)
            print("api gateway exited with code: ", p.returncode)
            print(stdout.decode('utf-8'))
        except TimeoutExpired:
            print("timed out waiting for api gateway to terminate")


PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us, human history would 
be far less bloody. The Enterprise computer system is controlled by three primary main processor 
cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface modules. Our 
neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you do remember 
how to fire phasers?"""


@pytest.mark.integration
def test_pipeline(python_events, python_processor, java_processor):
    with EventsClient(address=python_events) as client, mtap.Pipeline(
            RemoteProcessor('mtap-example-processor-python', address='localhost:50501',
                            params={'do_work': True}),
            RemoteProcessor('mtap-example-processor-java', address='localhost:50502',
                            params={'do_work': True})
    ) as pipeline:
        with Event(event_id='1', client=client) as event:
            event.metadata['a'] = 'b'
            document = event.create_document('plaintext', PHASERS)
            pipeline.run(document)
            letter_counts = document.get_label_index('mtap.examples.letter_counts')
            a_counts = letter_counts[0]
            assert a_counts.count == 23
            b_counts = letter_counts[1]
            assert b_counts.count == 6
            pipeline.print_times()
            thes = document.get_label_index("mtap.examples.word_occurrences")
            assert thes[0].start_index == 121
            assert thes[0].end_index == 124


@pytest.mark.integration
def test_api_gateway(python_events, python_processor, java_processor, api_gateway):
    resp = requests.get("http://localhost:50503/v1/processors")
    assert resp.status_code == 200
    processors = resp.json()
    all_ids = []
    for processor in processors['Processors']:
        all_ids.append(processor['Identifier'])
    assert 'mtap-example-processor-python' in all_ids
    assert 'mtap-example-processor-java' in all_ids

    resp = requests.post("http://localhost:50503/v1/events/1")
    assert resp.status_code == 200
    create_event = resp.json()
    assert create_event['created'] is True

    body = {
        'value': 'bar'
    }
    resp = requests.post("http://localhost:50503/v1/events/1/metadata/foo", json=body)
    assert resp.status_code == 200

    resp = requests.get("http://localhost:50503/v1/events/1/metadata")
    assert resp.status_code == 200
    metadata = resp.json()['metadata']
    assert metadata['foo'] == 'bar'

    body = {
        'text': PHASERS
    }
    resp = requests.post("http://localhost:50503/v1/events/1/documents/plaintext", json=body)
    assert resp.status_code == 200

    resp = requests.get("http://localhost:50503/v1/events/1/documents")
    assert resp.status_code == 200
    documents = resp.json()["document_names"]
    assert documents == ['plaintext']

    resp = requests.get("http://localhost:50503/v1/events/1/documents/plaintext")
    assert resp.status_code == 200
    text = resp.json()['text']
    assert text == PHASERS

    body = {
        'generic_labels': {
            'is_distinct': True,
            'labels': [
                {
                    'identifier': 0,
                    'start_index': 4,
                    'end_index': 10,
                    'reference_ids': {},
                    'fields': {
                        'foo': 'bar'
                    }
                },
                {
                    'identifier': 1,
                    'start_index': 10,
                    'end_index': 20,
                    'reference_ids': {},
                    'fields': {
                        'foo': 'baz'
                    }
                }
            ]
        }
    }
    resp = requests.post(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels/test-labels", json=body)
    assert resp.status_code == 200

    resp = requests.get("http://localhost:50503/v1/events/1/documents/plaintext/labels/test-labels")
    assert resp.status_code == 200
    labels = resp.json()
    generic_labels = labels['generic_labels']
    assert generic_labels['is_distinct']
    assert generic_labels['labels'] == body['generic_labels']['labels']

    body = {
        'processor_id': 'mtap-example-processor-python',
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = requests.post(
        "http://localhost:50503/v1/processors/mtap-example-processor-python/process/1",
        json=body
    )
    assert resp.status_code == 200
    python_process = resp.json()
    assert python_process['result']['answer'] == 42

    resp = requests.get(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels/mtap.examples.letter_counts"
    )
    assert resp.status_code == 200
    labels = resp.json()
    generic_labels = labels['generic_labels']
    assert generic_labels['labels'] == [
        {
            'identifier': 0,
            'start_index': 0,
            'end_index': len(PHASERS),
            'reference_ids': None,
            'fields': {
                'letter': 'a',
                'count': 23
            }
        },
        {
            'identifier': 1,
            'start_index': 0,
            'end_index': len(PHASERS),
            'reference_ids': None,
            'fields': {
                'letter': 'b',
                'count': 6
            }
        }
    ]

    body = {
        'processor_id': 'mtap-example-processor-java',
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = requests.post(
        "http://localhost:50503/v1/processors/mtap-example-processor-java/process/1",
        json=body
    )
    assert resp.status_code == 200
    java_process = resp.json()
    assert java_process['result']['answer'] == 42

    resp = requests.get(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels/mtap.examples.word_occurrences"
    )
    assert resp.status_code == 200
    labels = resp.json()['generic_labels']['labels']
    assert labels == [
        {
            'identifier': 0,
            'start_index': 121,
            'end_index': 124,
            'fields': {},
            'reference_ids': {}
        }
    ]

    resp = requests.get(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels"
    )
    assert resp.status_code == 200
    indices = resp.json()['label_index_infos']
    assert {
               'index_name': 'mtap.examples.letter_counts',
               'type': 'GENERIC'
           } in indices
    assert {
               'index_name': 'mtap.examples.word_occurrences',
               'type': 'GENERIC'
           } in indices
