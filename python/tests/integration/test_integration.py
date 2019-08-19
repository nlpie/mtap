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
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired, call

import grpc
import pytest
import requests
from requests import RequestException

import nlpnewt
from nlpnewt import RemoteProcessor, EventsClient, Event
from nlpnewt.utils import subprocess_events_server


@pytest.fixture(name='python_events')
def fixture_python_events():
    config_path = Path(__file__).parent / 'integrationConfig.yaml'
    with subprocess_events_server(port=50500, cwd=Path(__file__).parents[2],
                                  config_path=config_path) as address:
        yield address


@pytest.fixture(name='python_processor')
def fixture_python_processor(python_events, processor_watcher):
    cwd = Path(__file__).parents[2]
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    p = Popen(['python', '-m', 'nlpnewt.examples.example_processor', '-p', '50501',
               '--events', python_events],
              start_new_session=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=cwd, env=env)
    yield from processor_watcher(address="127.0.0.1:50501", process=p)


@pytest.fixture(name="java_processor")
def fixture_java_processor(python_events, processor_watcher):
    newt_jar = os.environ['NEWT_JAR']
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    p = Popen(['java', '-cp', newt_jar, 'edu.umn.nlpnewt.examples.WordOccurrencesExampleProcessor',
               '-p', '50502', '-e', python_events],
              start_new_session=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, env=env)
    yield from processor_watcher(address="127.0.0.1:50502", process=p)


@pytest.fixture(name="api_gateway")
def fixture_api_gateway(python_events, python_processor, java_processor):
    cwd = Path(__file__).parents[3] / 'go'
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    call(['make', 'proto'], cwd=cwd)
    call(['go', 'install', 'nlpnewt-gateway/nlpnewt-gateway.go'], cwd=cwd)
    p = Popen(['nlpnewt-gateway', '-logtostderr', '-v=3'],
              start_new_session=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=cwd, env=env)
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
    with EventsClient(address=python_events) as client, nlpnewt.Pipeline(
            RemoteProcessor('nlpnewt-example-processor-python', address='localhost:50501',
                            params={'do_work': True}),
            RemoteProcessor('nlpnewt-example-processor-java', address='localhost:50502',
                            params={'do_work': True})
    ) as pipeline:
        with Event(event_id='1', client=client) as event:
            event.metadata['a'] = 'b'
            document = event.create_document('plaintext', PHASERS)
            results = pipeline.run(document)
            letter_counts = document.get_label_index('nlpnewt.examples.letter_counts')
            a_counts = letter_counts[0]
            assert a_counts.count == 23
            b_counts = letter_counts[1]
            assert b_counts.count == 6
            pipeline.print_times()
            thes = document.get_label_index("nlpnewt.examples.word_occurrences")
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
    assert 'nlpnewt-example-processor-python' in all_ids
    assert 'nlpnewt-example-processor-java' in all_ids

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
        'json_labels': {
            'is_distinct': True,
            'labels': [
                {
                    'start_index': 4,
                    'end_index': 10,
                    'foo': 'bar'
                },
                {
                    'start_index': 10,
                    'end_index': 20,
                    'foo': 'baz'
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
    json_labels = labels['json_labels']
    assert json_labels['is_distinct']
    assert json_labels['labels'] == body['json_labels']['labels']

    body = {
        'processor_id': 'nlpnewt-example-processor-python',
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = requests.post(
        "http://localhost:50503/v1/processors/nlpnewt-example-processor-python/process/1",
        json=body
    )
    assert resp.status_code == 200
    python_process = resp.json()
    assert python_process['result']['answer'] == 42

    resp = requests.get(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels/nlpnewt.examples.letter_counts"
    )
    assert resp.status_code == 200
    labels = resp.json()
    json_labels = labels['json_labels']
    assert json_labels['labels'] == [
        {
            'start_index': 0,
            'end_index': len(PHASERS),
            'letter': 'a',
            'count': 23
        },
        {
            'start_index': 0,
            'end_index': len(PHASERS),
            'letter': 'b',
            'count': 6
        }
    ]

    body = {
        'processor_id': 'nlpnewt-example-processor-java',
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = requests.post(
        "http://localhost:50503/v1/processors/nlpnewt-example-processor-java/process/1",
        json=body
    )
    assert resp.status_code == 200
    java_process = resp.json()
    assert java_process['result']['answer'] == 42

    resp = requests.get(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels/nlpnewt.examples.word_occurrences"
    )
    assert resp.status_code == 200
    labels = resp.json()['json_labels']['labels']
    assert labels == [
        {
            'start_index': 121,
            'end_index': 124
        }
    ]

    resp = requests.get(
        "http://localhost:50503/v1/events/1/documents/plaintext/labels"
    )
    assert resp.status_code == 200
    indices = resp.json()['label_index_infos']
    assert {
               'index_name': 'nlpnewt.examples.letter_counts',
               'type': 'JSON'
           } in indices
    assert {
               'index_name': 'nlpnewt.examples.word_occurrences',
               'type': 'JSON'
           } in indices
