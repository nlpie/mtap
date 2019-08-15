from typing import Dict, Any

import grpc
import grpc_testing
import pytest

from nlpnewt import processor, Document
from nlpnewt.api.v1 import processing_pb2
from nlpnewt.processing import DocumentProcessor
from nlpnewt.processing.descriptions import parameter, label_index, label_property
from nlpnewt.processing.service import _ProcessorServicer


@processor('nlpnewt-test-processor',
           description='Processor desc.',
           parameters=[
               parameter('a_param', required=True, data_type='bool',
                         description="desc.")
           ],
           inputs=[
               label_index('input_index', properties=[label_property('bar', data_type='bool')])
           ],
           outputs=[
               label_index('output_index',
                           description='desc.',
                           properties=[label_property('foo', data_type='str', nullable=True,
                                                      description='A label property.')])
           ])
class ExampleTestProcessor(DocumentProcessor):
    def process_document(self, document: Document, params: Dict[str, Any]):
        pass


@pytest.fixture(name='processor_servicer')
def fixture_processor_servicer():
    processor_service = _ProcessorServicer(config={}, pr=ExampleTestProcessor(), address='',
                                           health_servicer=None)
    yield grpc_testing.server_from_dictionary(
        {
            processing_pb2.DESCRIPTOR.services_by_name['Processor']: processor_service
        },
        grpc_testing.strict_real_time()
    )


def test_GetInfo(processor_servicer):
    request = processing_pb2.GetInfoRequest(processor_id='nlpnewt-example-processor-python')
    resp, _, status_code, _ = processor_servicer.invoke_unary_unary(
        processing_pb2.DESCRIPTOR.services_by_name['Processor'].methods_by_name['GetInfo'],
        {},
        request,
        None
    ).termination()

    assert status_code == grpc.StatusCode.OK
    assert resp.name == 'nlpnewt-test-processor'
    assert len(resp.parameters) == 1
    assert resp.parameters[0].name == 'a_param'
    assert resp.parameters[0].required
    assert resp.parameters[0].data_type == 'bool'
    assert resp.parameters[0].description == 'desc.'
    assert len(resp.inputs) == 1
    assert resp.inputs[0].name == 'input_index'
    assert len(resp.inputs[0].properties) == 1
    assert resp.inputs[0].properties[0].name == 'bar'
    assert resp.inputs[0].properties[0].data_type == 'bool'
    assert len(resp.outputs) == 1
    assert resp.outputs[0].name == 'output_index'
    assert resp.outputs[0].description == 'desc.'
    assert len(resp.outputs[0].properties) == 1
    assert resp.outputs[0].properties[0].name == 'foo'
    assert resp.outputs[0].properties[0].data_type == 'str'
    assert resp.outputs[0].properties[0].nullable
    assert resp.outputs[0].properties[0].description == 'A label property.'
