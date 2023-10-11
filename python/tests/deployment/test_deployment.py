#  Copyright 2022 Regents of the University of Minnesota.
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
from pathlib import Path

import pytest

from mtap import RemoteProcessor, Pipeline, events_client, Event
from mtap.deployment import Deployment, ProcessorDeployment
from mtap.utilities import find_free_port

text = """
Why, friends, you go to do you know not what:
Wherein hath Caesar thus deserved your loves?
Alas, you know not: I must tell you then:
You have forgot the will I told you of.
…
Here is the will, and under Caesar’s seal.
To every Roman citizen he gives,
To every several man, seventy-five drachmas.
…
Moreover, he hath left you all his walks,
His private arbours and new-planted orchards,
On this side Tiber; he hath left them you,
And to your heirs for ever, common pleasures,
To walk abroad, and recreate yourselves.
Here was a Caesar! when comes such another?
"""


@pytest.mark.integration
def test_deployment(java_exe):
    from importlib_resources import files, as_file
    deployment_config = files('mtap.examples').joinpath('exampleDeploymentConfiguration.yml')
    run_config = files('mtap.examples').joinpath('examplePipelineConfiguration.yml')
    with as_file(deployment_config) as deployment_f:
        deployment = Deployment.from_yaml_file(deployment_f)
    with as_file(run_config) as run_f:
        pipeline = Pipeline.from_yaml_file(run_f)
    deployment.global_settings.log_level = 'DEBUG'
    deployment.shared_processor_config.java_classpath = java_exe[-1]
    deployment.processors.append(ProcessorDeployment(
        implementation='python',
        entry_point='mtap.examples.tutorial.hello',
        port=10103
    ))
    with deployment.run_servers():
        pipeline.append(
            RemoteProcessor(
                name='hello',
                address='127.0.0.1:10103'
            )
        )
        with events_client(deployment.events_deployment.address) as c:
            with Event(client=c) as e:
                d = e.create_document('plaintext', text)

                def source():
                    yield d

                times = pipeline.run_multithread(source(), total=1, log_level='DEBUG')
                assert len(d.labels['mtap.examples.letter_counts']) > 0
                assert len(d.labels['mtap.examples.word_occurrences']) > 0
                assert len(times.component_ids) == 3


def test_minimal_deployment_configuration():
    deploy_file = Path(__file__).parent / 'minimalDeploymentConfiguration.yml'
    deployment = Deployment.from_yaml_file(deploy_file)
    deployment.processors[0].port = find_free_port()
    with deployment.run_servers() as (event_addresses, processor_addresses):
        assert len(event_addresses) == 0
        assert processor_addresses[0][0].endswith(f':{deployment.processors[0].port}')
