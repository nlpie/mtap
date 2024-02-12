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

from typing import Dict, Any

import grpc
import grpc_testing
import pytest

from mtap import processor, Document, DocumentProcessor
from mtap.api.v1 import processing_pb2
from mtap.processing import _runners
from mtap.descriptors import parameter, labels, label_property
from mtap.processing._service import _ProcessorServicer


@processor('mtap-test-processor',
           description='Processor desc.',
           parameters=[
               parameter('a_param', required=True, data_type='bool',
                         description="desc.")
           ],
           inputs=[
               labels('input_index',
                      properties=[label_property('bar', data_type='bool')])
           ],
           outputs=[
               labels('output_index',
                      description='desc.',
                      properties=[
                          label_property('foo', data_type='str', nullable=True,
                                         description='A label property.')])
           ])
class ExampleTestProcessor(DocumentProcessor):
    def process_document(self, document: Document, params: Dict[str, Any]):
        pass


@pytest.fixture(name='processor_servicer')
def fixture_processor_servicer():
    runner = _runners.LocalRunner(ExampleTestProcessor(), events_address=None)
    processor_service = _ProcessorServicer(runner=runner)
    yield grpc_testing.server_from_dictionary(
        {
            processing_pb2.DESCRIPTOR.services_by_name[
                'Processor']: processor_service
        },
        grpc_testing.strict_real_time()
    )


def test_GetInfo(processor_servicer):
    request = processing_pb2.GetInfoRequest(
        processor_id='mtap-example-processor-python')
    resp, _, status_code, _ = processor_servicer.invoke_unary_unary(
        processing_pb2.DESCRIPTOR.services_by_name[
            'Processor'].methods_by_name['GetInfo'],
        {},
        request,
        None
    ).termination()

    assert status_code == grpc.StatusCode.OK
    assert resp.metadata['name'] == 'mtap-test-processor'
    assert len(resp.metadata['parameters']) == 1
    assert resp.metadata['parameters'][0]['name'] == 'a_param'
    assert resp.metadata['parameters'][0]['required']
    assert resp.metadata['parameters'][0]['data_type'] == 'bool'
    assert resp.metadata['parameters'][0]['description'] == 'desc.'
    assert len(resp.metadata['inputs']) == 1
    assert resp.metadata['inputs'][0]['name'] == 'input_index'
    assert len(resp.metadata['inputs'][0]['properties']) == 1
    assert resp.metadata['inputs'][0]['properties'][0]['name'] == 'bar'
    assert resp.metadata['inputs'][0]['properties'][0]['data_type'] == 'bool'
    assert len(resp.metadata['outputs']) == 1
    assert resp.metadata['outputs'][0]['name'] == 'output_index'
    assert resp.metadata['outputs'][0]['description'] == 'desc.'
    assert len(resp.metadata['outputs'][0]['properties']) == 1
    assert resp.metadata['outputs'][0]['properties'][0]['name'] == 'foo'
    assert resp.metadata['outputs'][0]['properties'][0]['data_type'] == 'str'
    assert resp.metadata['outputs'][0]['properties'][0]['nullable']
    assert resp.metadata['outputs'][0]['properties'][0][
               'description'] == 'A label property.'
