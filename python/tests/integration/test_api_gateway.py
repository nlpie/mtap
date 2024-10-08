#  Copyright (c) Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import tempfile
import time
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

import pytest
import requests
import yaml
from requests import RequestException

from mtap.utilities import find_free_port

try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper


@pytest.fixture(name="api_gateway", scope='module')
def fixture_api_gateway(deployment, hosted_pipeline):
    python_events = deployment['events']
    python_processor = deployment['py_example']
    java_processor = deployment['java_example']
    port = find_free_port()
    config = {
        'grpc': {
            'enable_proxy': False
        },

        'max_send_message_length': 104857600,
        'max_receive_message_length': 104857600,
        'consul': {
            'host': 'localhost',
            'port': 8500,
            'scheme': 'http',
            # Python uses {python_naming_scheme}:address[:port][,address[:port],...] as grpc targets
            'python_naming_scheme': 'ipv4'
        },
        'gateway': {
            'port': port,
            'refresh_interval': 10,
            'events': python_events,
            'processors': [
                {
                    'Identifier': 'mtap-example-processor-python',
                    'Endpoint': python_processor
                },
                {
                    'Identifier': 'mtap-example-processor-java',
                    'Endpoint': java_processor
                }
            ],
            'pipelines': [
                {
                    'Identifier': 'test-pipeline',
                    'Endpoint': hosted_pipeline
                }
            ]
        }
    }

    with tempfile.NamedTemporaryFile('w', suffix='.yml') as conf_file:
        yaml.dump(config, conf_file, Dumper=Dumper)
        conf_file.flush()
        p = Popen(['mtap-gateway', '-logtostderr', '-v=3',
                   '-mtap-config=' + conf_file.name],
                  stdin=PIPE, stdout=PIPE, stderr=STDOUT)

        session = requests.Session()
        session.trust_env = False
        gateway = '127.0.0.1:{}'.format(port)
        try:
            if p.returncode is not None:
                raise ValueError("Failed to launch go gateway")
            for i in range(6):
                if i == 5:
                    raise ValueError("Failed to connect to go gateway")
                try:
                    time.sleep(3)
                    resp = session.get(
                        "http://{}/v1/processors".format(gateway), timeout=1)
                    if resp.status_code == 200 and len(
                            resp.json()['Processors']) == 2:
                        break
                except RequestException:
                    pass
            yield gateway
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
                stdout, _ = p.communicate(timeout=1)
                print("api gateway exited with code: ", p.returncode)
                print(stdout.decode('utf-8'))


PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us,
human history would be far less bloody. The Enterprise computer system is
controlled by three primary main processor cores, cross-linked with a redundant
melacortz ramistat, fourteen kiloquad interface modules. Our
neural pathways have become accustomed to your sensory input patterns. Mr.
Worf, you do remember how to fire phasers?"""


@pytest.mark.integration
@pytest.mark.gateway
def test_api_gateway(api_gateway):
    session = requests.Session()
    session.trust_env = False
    base_url = "http://" + api_gateway
    resp = session.get(base_url + "/v1/processors", timeout=10)
    assert resp.status_code == 200
    processors = resp.json()
    all_ids = []
    for processor in processors['Processors']:
        all_ids.append(processor['Identifier'])
    assert 'mtap-example-processor-python' in all_ids
    assert 'mtap-example-processor-java' in all_ids

    resp = session.get(base_url + "/v1/events/instance_id", timeout=1)
    assert resp.status_code == 200
    instance_id = resp.json()['instance_id']
    assert instance_id is not None

    resp = session.post(base_url + "/v1/events/1")
    assert resp.status_code == 200
    create_event = resp.json()
    assert create_event['created'] is True

    body = {
        'value': 'bar'
    }
    resp = session.post(base_url + "/v1/events/1/metadata/foo", json=body,
                        timeout=1)
    assert resp.status_code == 200

    resp = session.get(base_url + "/v1/events/1/metadata", timeout=1)
    assert resp.status_code == 200
    metadata = resp.json()['metadata']
    assert metadata['foo'] == 'bar'

    body = {
        'text': PHASERS
    }
    resp = session.post(base_url + "/v1/events/1/documents/plaintext",
                        json=body, timeout=1)
    assert resp.status_code == 200

    resp = session.get(base_url + "/v1/events/1/documents", timeout=1)
    assert resp.status_code == 200
    documents = resp.json()["document_names"]
    assert documents == ['plaintext']

    resp = session.get(base_url + "/v1/events/1/documents/plaintext",
                       timeout=1)
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
    resp = session.post(
        base_url + "/v1/events/1/documents/plaintext/labels/test-labels",
        json=body, timeout=1)
    assert resp.status_code == 200

    resp = session.get(
        base_url + "/v1/events/1/documents/plaintext/labels/test-labels",
        timeout=1)
    assert resp.status_code == 200
    labels = resp.json()
    generic_labels = labels['generic_labels']
    assert generic_labels['is_distinct']
    assert generic_labels['labels'] == body['generic_labels']['labels']

    body = {
        'processor_id': 'mtap-example-processor-python',
        'event_service_instance_id': instance_id,
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = session.post(
        base_url + "/v1/processors/mtap-example-processor-python/process/1",
        json=body,
        timeout=1
    )
    assert resp.status_code == 200
    python_process = resp.json()
    assert python_process['result']['answer'] == 42

    resp = session.get(
        base_url + "/v1/events/1/documents/plaintext/labels/mtap.examples.letter_counts",
        timeout=1
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
        'event_service_instance_id': instance_id,
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = session.post(
        base_url + "/v1/processors/mtap-example-processor-java/process/1",
        json=body,
        timeout=1
    )
    assert resp.status_code == 200
    java_process = resp.json()
    assert java_process['result']['answer'] == 42

    resp = session.get(
        base_url + "/v1/events/1/documents/plaintext/labels/mtap.examples.word_occurrences",
        timeout=1
    )
    assert resp.status_code == 200
    labels = resp.json()['generic_labels']['labels']
    assert labels == [
        {
            'identifier': 0,
            'start_index': 120,
            'end_index': 123,
            'fields': {},
            'reference_ids': {}
        }
    ]

    resp = session.get(
        base_url + "/v1/events/1/documents/plaintext/labels",
        timeout=1
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

    resp = session.delete(
        base_url + "/v1/events/1"
    )
    assert resp.status_code == 200

    resp = session.get(base_url + "/v1/events/1/metadata")
    assert resp.status_code == 404


@pytest.mark.integration
@pytest.mark.gateway
def test_api_gateway_pipeline(api_gateway):
    session = requests.Session()
    session.trust_env = False
    base_url = "http://" + api_gateway

    body = {
        'event': {
            'event_id': '1.txt',
            'documents': {
                'plaintext': {
                    'text': PHASERS
                }
            }
        },
        'params': {
            'document_name': 'plaintext',
            'do_work': True,
        }
    }
    resp = session.post(
        base_url + '/v1/pipeline/test-pipeline/process',
        json=body,
        timeout=10
    )
    resp_body = resp.json()
    label_indices = resp_body['event']['documents']['plaintext']['label_indices']
    a_counts = label_indices['mtap.examples.letter_counts']['labels'][0]
    assert a_counts['fields']['count'] == 23
    word_occ = label_indices['mtap.examples.word_occurrences']['labels'][0]
    assert word_occ is not None
