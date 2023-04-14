#  Copyright 2021 Regents of the University of Minnesota.
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
#
import shutil
from argparse import ArgumentParser
from pathlib import Path

import mtap
from mtap.serialization import SerializationProcessor, JsonSerializer
from mtap.processing import (
    FilesInDirectoryProcessingSource,
    Pipeline,
    LocalProcessor,
)


def print_example(_):
    print('Writing "examplePipelineConfiguration.yml" to ' + str(Path.cwd()))
    shutil.copy2(
        str(Path(__file__).parent / 'examplePipelineConfiguration.yml'),
        'examplePipelineConfiguration.yml')


def run_pipeline(conf):
    pipeline_conf = (
            conf.pipeline_config
            or Path(__file__).parent / 'examplePipelineConfiguration.yml'
    )
    pipeline = Pipeline.from_yaml_file(pipeline_conf)

    with mtap.EventsClient(address=conf.events_address) as client:
        pipeline.events_client = client
        pipeline.append(
            LocalProcessor(
                processor=SerializationProcessor(
                    serializer=JsonSerializer,
                    output_dir=conf.output_directory
                ),
                component_id='serialization_processor'
            )
        )
        source = FilesInDirectoryProcessingSource(directory=conf.directory,
                                                  client=client)
        pipeline.run_multithread(source=source, workers=conf.threads,
                                 max_failures=conf.max_failures,
                                 read_ahead=conf.read_ahead)


def main(args=None):
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    print_example_subparser = subparsers.add_parser('write_example')
    print_example_subparser.set_defaults(f=print_example)

    run_subparser = subparsers.add_parser('run')

    run_subparser.add_argument(
        'input_directory',
        metavar='IN_DIR',
        help='Directory of files to process.'
    )

    run_subparser.add_argument(
        'output_directory',
        metavar='OUT_DIR',
        help='Where to write output files.'
    )

    run_subparser.add_argument(
        'events_address',
        metavar='ADDRESS',
        help='Address of the events service.'
    )

    run_subparser.add_argument(
        '--pipeline-config',
        metavar='PATH',
        default=None,
        help='Path to a pipeline configuration.'
    )

    run_subparser.add_argument(
        '--threads',
        metavar='N',
        default=4,
        help='Number of threads to use for processing'
    )

    run_subparser.add_argument(
        '--max-failures',
        metavar='N',
        default=0,
        help='The maximum number of failures to accept before stopping.'
    )

    run_subparser.add_argument(
        '--read-ahead',
        metavar='N',
        default=1,
        help='The number of documents to read ahead of what is currently '
             'being processed'
    )

    run_subparser.set_defaults(f=run_pipeline)

    conf = parser.parse_args(args)
    f = conf.f
    f(conf)


if __name__ == '__main__':
    main()
