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
import subprocess
import time
from pathlib import Path

import grpc
import pytest
import requests
from requests import RequestException

import nlpnewt


@pytest.fixture(name='python_events')
def fixture_python_events():
    cwd = Path(__file__).parents[2]
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    p = subprocess.Popen(['python', 'nlpnewt', 'events', '-p', '50500'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=cwd, env=env)
    try:
        with grpc.insecure_channel("127.0.0.1:50500") as channel:
            future = grpc.channel_ready_future(channel)
            future.result(timeout=10)
        yield
    finally:
        p.terminate()
        p.wait(5)
        stdout, stderr = p.communicate()
        print(stdout.decode('utf-8'))
        print(stderr.decode('utf-8'))


@pytest.fixture(name='python_processor')
def fixture_python_processor(python_events):
    cwd = Path(__file__).parents[2]
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    p = subprocess.Popen(['python', 'nlpnewt', 'processor', '-p', '50501',
                          '--events', '127.0.0.1:50500',
                          '--name', 'nlpnewt-example-processor-python',
                          '-m', 'nlpnewt.examples.example_processor'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=cwd, env=env)
    try:
        with grpc.insecure_channel("127.0.0.1:50501") as channel:
            future = grpc.channel_ready_future(channel)
            future.result(timeout=10)
        yield
    finally:
        p.terminate()
        p.wait(5)
        stdout, stderr = p.communicate()
        print(stdout.decode('utf-8'))
        print(stderr.decode('utf-8'))


@pytest.fixture(name="java_processor")
def fixture_java_processor(python_events):
    cwd = Path(__file__).parents[3] / 'java'
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    p = subprocess.Popen(['./gradlew', 'newt',
                          '--args',
                          "processor -p 50502 -e 127.0.0.1:50500 "
                          "edu.umn.nlpnewt.examples.TheOccurrencesExampleProcessor"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=cwd, env=env)
    try:
        if p.returncode is not None:
            raise ValueError("Failed to launch java processor")
        with grpc.insecure_channel("127.0.0.1:50502") as channel:
            future = grpc.channel_ready_future(channel)
            future.result(timeout=10)
        yield
    finally:
        p.terminate()
        p.wait(5)
        stdout, stderr = p.communicate()
        print(stdout.decode('utf-8'))
        print(stderr.decode('utf-8'))


@pytest.fixture(name="api_gateway")
def fixture_api_gateway(python_events, python_processor, java_processor):
    cwd = Path(__file__).parents[3] / 'go'
    env = dict(os.environ)
    env['NEWT_CONFIG'] = Path(__file__).parent / 'integrationConfig.yaml'
    subprocess.call(['make', 'proto'], cwd=cwd)
    subprocess.call(['go', 'install', 'nlpnewt-gateway/nlpnewt-gateway.go'], cwd=cwd)
    p = subprocess.Popen(['nlpnewt-gateway', '-logtostderr', '-v=2'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=cwd, env=env)
    try:
        if p.returncode is not None:
            raise ValueError("Failed to launch go gateway")
        for i in range(6):
            if i == 5:
                raise ValueError("Failed to connect to go gateway")
            try:
                resp = requests.get("http://localhost:50503/v1/processors")
                if resp.status_code == 200:
                    break
            except RequestException:
                pass
            time.sleep(0.5)
        yield
    finally:
        p.terminate()
        p.wait(5)
        stdout, stderr = p.communicate()
        print(stdout.decode('utf-8'))
        print(stderr.decode('utf-8'))


PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us, human history would 
be far less bloody. The Enterprise computer system is controlled by three primary main processor 
cores, cross-linked with a redundant melacortz ramistat, fourteen kiloquad interface modules. Our 
neural pathways have become accustomed to your sensory input patterns. Mr. Worf, you do remember 
how to fire phasers?"""


def test_pipeline(python_events, python_processor, java_processor):
    with nlpnewt.Events('127.0.0.1:50500') as events, nlpnewt.Pipeline() as pipeline:
        pipeline.add_processor('nlpnewt-example-processor-python', address='localhost:50501',
                               params={'do_work': True})
        pipeline.add_processor('nlpnewt-example-processor-java', address='localhost:50502',
                               params={'do_work': True})

        with events.open_event('1') as event:
            event.metadata['a'] = 'b'
            document = event.add_document('plaintext', PHASERS)
            results = pipeline.run(document)
            letter_counts = document.get_label_index('nlpnewt.examples.letter_counts')
            a_counts = letter_counts[0]
            assert a_counts.count == 23
            b_counts = letter_counts[1]
            assert b_counts.count == 6
            pipeline.print_times()
            thes = document.get_label_index("nlpnewt.examples.thes")
            assert thes[0].start_index == 121
            assert thes[0].end_index == 124


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
        "http://localhost:50503/v1/events/1/documents/plaintext/labels/nlpnewt.examples.thes"
    )
    assert resp.status_code == 200
    labels = resp.json()['json_labels']['labels']
    assert labels == [
        {
            'start_index': 121,
            'end_index': 124
        }
    ]