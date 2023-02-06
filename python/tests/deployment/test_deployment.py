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

import mtap
from mtap import RemoteProcessor
from mtap.deployment import Deployment, ProcessorDeployment

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


def test_deployment(java_exe):
    from importlib_resources import files, as_file
    deployment_config = files('mtap.examples').joinpath('exampleDeploymentConfiguration.yml')
    run_config = files('mtap.examples').joinpath('examplePipelineConfiguration.yml')
    with as_file(deployment_config) as deployment_f, as_file(run_config) as run_f:
        deployment = Deployment.from_yaml_file(deployment_f)
        deployment.global_settings.log_level = 'DEBUG'
        deployment.shared_processor_config.java_classpath = java_exe[-1]
        deployment.shared_processor_config.jvm_args = ["-Dorg.slf4j.simpleLogger.log.edu.umn.nlpie.mtap=debug"]
        deployment.processors.append(ProcessorDeployment(
            implementation='python',
            entry_point='mtap.examples.tutorial.hello',
            port=10103
        ))
        with deployment.run_servers():
            pipeline = mtap.Pipeline.from_yaml_file(run_f)
            pipeline.append(
                RemoteProcessor(
                    processor_name='hello',
                    address='127.0.0.1:10103'
                )
            )
            with mtap.Event(client=pipeline.events_client) as e:
                d = e.create_document('plaintext', text)
                results = pipeline.run(d)
                assert results is not None
            with mtap.Event(client=pipeline.events_client) as e:
                d = e.create_document('plaintext', text)

                def source():
                    yield d

                pipeline.run_multithread(source(), total=1, log_level='DEBUG')
                assert len(d.labels['mtap.examples.letter_counts']) > 0
                assert len(d.labels['mtap.examples.word_occurrences']) > 0
