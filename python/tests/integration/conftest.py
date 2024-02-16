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

import multiprocessing
from contextlib import suppress

import grpc
import pytest
from importlib_resources import files, as_file

from mtap import Pipeline, RemoteProcessor
from mtap.deployment import Deployment, ProcessorDeployment
from mtap.pipeline import run_pipeline_server
from mtap.utilities import find_free_port


def make_addr(p):
    return f'localhost:{p}'


@pytest.fixture(name="deployment", scope="package")
def fixture_deployment(java_exe, processor_timeout):
    deployment_config = files('mtap.examples').joinpath('exampleDeploymentConfiguration.yml')
    with as_file(deployment_config) as deployment_f:
        deployment = Deployment.from_yaml_file(deployment_f)

    events_port = find_free_port()
    deployment.events_deployment.address = f'127.0.0.1:{events_port}'
    events_address = make_addr(events_port)

    py_example_proc_port = find_free_port()
    py_example_proc_addr = make_addr(py_example_proc_port)
    deployment.processors[0].port = py_example_proc_port

    java_example_proc_port = find_free_port()
    java_example_proc_addr = make_addr(java_example_proc_port)
    deployment.processors[1].port = java_example_proc_port

    py_hello_port = find_free_port()
    py_hello_addr = make_addr(py_hello_port)

    java_hello_port = find_free_port()
    java_hello_addr = make_addr(java_hello_port)

    py_references_port = find_free_port()
    py_references_addr = make_addr(py_references_port)

    java_references_port = find_free_port()
    java_references_addr = make_addr(java_references_port)

    deployment.global_settings.log_level = 'DEBUG'
    deployment.shared_processor_config.startup_timeout = processor_timeout
    deployment.shared_processor_config.java_classpath = java_exe[-1]
    deployment.processors.append(ProcessorDeployment(
        implementation='python',
        entry_point='mtap.examples.tutorial.hello',
        port=py_hello_port
    ))
    deployment.processors.append(ProcessorDeployment(
        implementation='java',
        entry_point='edu.umn.nlpie.mtap.examples.HelloWorldExample',
        port=java_hello_port
    ))
    deployment.processors.append(ProcessorDeployment(
        implementation='python',
        entry_point='mtap.examples.example_references_processor',
        port=py_references_port
    ))
    deployment.processors.append(ProcessorDeployment(
        implementation='java',
        entry_point='edu.umn.nlpie.mtap.examples.ReferenceLabelsExampleProcessor',
        port=java_references_port
    ))

    with deployment.run_servers():
        for addr in (events_address, py_example_proc_addr, java_example_proc_addr, py_hello_addr, java_hello_addr):
            with grpc.insecure_channel(addr) as ch:
                fut = grpc.channel_ready_future(ch)
                fut.result(timeout=10.0)

        yield {
            'events': events_address,
            'py_example': py_example_proc_addr,
            'java_example': java_example_proc_addr,
            'py_hello': py_hello_addr,
            'java_hello': java_hello_addr,
            'py_references': py_references_addr,
            'java_references': java_references_addr
        }


@pytest.fixture(name='hosted_pipeline', scope='package')
def fixture_hosted_pipeline(deployment):
    mp = multiprocessing.get_context('spawn')
    pipeline_port = str(find_free_port())
    pipeline = Pipeline(RemoteProcessor(name='mtap-example-processor-python',
                                        address=deployment['py_example']),
                        RemoteProcessor(name='mtap-example-processor-java',
                                        address=deployment['java_example']),
                        name='test-pipeline',
                        events_address=deployment['events'])
    p: multiprocessing.Process = mp.Process(target=run_pipeline_server,
                                            args=(pipeline, None, ['--port', str(pipeline_port)], None))
    p.start()
    try:
        addr = make_addr(pipeline_port)
        with grpc.insecure_channel(addr) as ch:
            fut = grpc.channel_ready_future(ch)
            fut.result(timeout=10.0)
        yield addr
    finally:
        try:
            p.terminate()
            p.join(timeout=1)
        except multiprocessing.TimeoutError:
            p.kill()
            with suppress(multiprocessing.TimeoutError):
                p.join(timeout=1)
