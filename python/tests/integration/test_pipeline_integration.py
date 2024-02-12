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

import uuid

import grpc
import pytest
from importlib_resources import files, as_file

import mtap
from mtap import RemoteProcessor, events_client, Event, Pipeline
from mtap.api.v1 import pipeline_pb2_grpc, pipeline_pb2

PHASERS = """
Maybe if we felt any human loss as keenly as we feel one of those close to us,
human history would be far less bloody. The Enterprise computer system is
controlled by three primary main processor cores, cross-linked with a redundant
melacortz ramistat, fourteen kiloquad interface modules. Our
neural pathways have become accustomed to your sensory input patterns. Mr.
Worf, you do remember how to fire phasers?"""


def validate_pipeline(pipeline, python_events):
    with events_client(address=python_events) as client:
        with Event(event_id=str(uuid.uuid4()), client=client) as event:
            event.metadata['a'] = 'b'
            document = event.create_document('plaintext', PHASERS)
            result = pipeline.run_multithread([document])
            letter_counts = document.labels['mtap.examples.letter_counts']
            a_counts = letter_counts[0]
            assert a_counts.count == 23
            b_counts = letter_counts[1]
            assert b_counts.count == 6
            result.print()
            thes = document.labels["mtap.examples.word_occurrences"]
            assert thes[0].start_index == 120
            assert thes[0].end_index == 123


@pytest.mark.integration
def test_constructed_pipeline(deployment):
    python_events = deployment['events']
    python_processor = deployment['py_example']
    java_processor = deployment['java_example']

    pipeline = mtap.Pipeline(
        RemoteProcessor('mtap-example-processor-python',
                        address=python_processor,
                        params={'do_work': True}),
        RemoteProcessor('mtap-example-processor-java',
                        address=java_processor,
                        params={'do_work': True})
    )

    validate_pipeline(pipeline, python_events)


@pytest.mark.integration
def test_example_pipeline(deployment):
    python_events = deployment['events']
    python_processor = deployment['py_example']
    java_processor = deployment['java_example']

    pipeline_config = files('mtap.examples').joinpath('examplePipelineConfiguration.yml')
    with as_file(pipeline_config) as pipeline_f:
        pipeline = Pipeline.from_yaml_file(pipeline_f)

    pipeline.events_address = python_events
    pipeline[0].address = python_processor
    pipeline[1].address = java_processor

    validate_pipeline(pipeline, python_events)


@pytest.mark.integration
def test_hosted_pipeline(hosted_pipeline):
    with grpc.insecure_channel(hosted_pipeline) as ch:
        stub = pipeline_pb2_grpc.PipelineStub(ch)
        req = pipeline_pb2.ProcessEventInPipelineRequest()
        req.params['document_name'] = 'plaintext'
        req.params['do_work'] = True
        req.event['event_id'] = '1.txt'
        req_docs = req.event.get_or_create_struct('documents')
        req_doc = req_docs.get_or_create_struct('plaintext')
        req_doc['text'] = PHASERS
        resp = stub.Process(req)
        label_indices = resp.event['documents']['plaintext']['label_indices']
        assert label_indices['mtap.examples.letter_counts']['labels'][0]['fields']['count'] == 23
