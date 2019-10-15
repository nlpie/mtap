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

from mtap.examples.example_processor import ExampleProcessor


def main(filename: str):
    from yaml import dump
    try:
        from yaml import CDumper as Dumper
    except ImportError:
        from yaml import Dumper as Dumper

    with open(filename, 'w') as f:
        dump(ExampleProcessor.metadata, f, Dumper=Dumper)


if __name__ == '__main__':
    main(sys.argv[1])
