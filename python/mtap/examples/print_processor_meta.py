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
"""Prints the processor metadata for the example processor."""
import sys
from os import environ
from subprocess import call
from tempfile import NamedTemporaryFile

from mtap.examples.example_processor import ExampleProcessor


def main(filename: str):
    java_jar = environ['MTAP_JAR']

    from yaml import dump, load
    try:
        from yaml import CDumper as Dumper, CLoader as Loader
    except ImportError:
        from yaml import Dumper as Dumper, Loader as Loader

    with NamedTemporaryFile('r') as f:
        # Here we call out to a java utility for printing processor metadata and then load that
        # metadata to merge it with the python metadata.
        # The classpath should include MTAP and class files for any processors for which you want
        # to print metadata.
        call(['java', '-cp', java_jar, 'edu.umn.nlpie.mtap.utilities.PrintProcessorMetadata',
              f.name,
              'edu.umn.nlpie.mtap.examples.WordOccurrencesExampleProcessor',
              ])
        java_meta = load(f, Loader=Loader)

    with open(filename, 'w') as f:
        dump([ExampleProcessor.metadata] + java_meta, f, Dumper=Dumper)


if __name__ == '__main__':
    main(sys.argv[1])
