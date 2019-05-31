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
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Any

from nlpnewt import processor
from nlpnewt.events import Event
from nlpnewt.processing import EventProcessor, run_processor, processor_parser
from nlpnewt.serialization.serializers import Serializer, get_serializer


@processor('nlpnewt-serializer')
class SerializationProcessor(EventProcessor):
    def __init__(self, serializer: Serializer, output_dir: str):
        self.serializer = serializer
        self.output_dir = output_dir

    def process(self, event: Event, params: Dict[str, Any]):
        name = params.get('filename', event.event_id + self.serializer.extension)
        path = Path(self.output_dir, name)
        self.serializer.event_to_file(event, path)


def main(args=None):
    parser = ArgumentParser(parents=[processor_parser()])
    parser.add_argument('serializer', help="The name of the serializer to use.")
    parser.add_argument('--output-dir', '-o', default=".",
                        help="Directory to write serialized files to.")
    ns = parser.parse_args(args)
    Serializer = get_serializer(ns.serializer)
    processor = SerializationProcessor(Serializer(), ns.output_dir)
    run_processor(processor, ns)


if __name__ == '__main__':
    main()
