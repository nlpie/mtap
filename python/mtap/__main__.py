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
import logging

from time import sleep

from mtap import processor_parser, run_processor
from mtap._config import Config
from mtap._events_service import EventsServer
from mtap.io.serialization import SerializationProcessor, JsonSerializer

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

_serializers = {'json': JsonSerializer}


def run_events_server(args):
    """Runs the documents service, blocking until keyboard interrupt.

    Parameters:
        args: Command line arguments.
    """
    with Config() as c:
        if args.mtap_config is not None:
            c.update_from_yaml(args.mtap_config)
        server = EventsServer(args.host, port=args.port, register=args.register,
                              workers=args.workers,
                              write_address=args.write_address)
        server.start()
        try:
            while True:
                sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(grace=5.0)


def run_serializer_processor(args):
    ser = _serializers[args.serializer]
    proc = SerializationProcessor(ser, args.output_dir)
    run_processor(proc, args=args)


def main(args=None):
    import argparse as argparse
    parser = argparse.ArgumentParser(description='Starts a MTAP gRPC server.',
                                     allow_abbrev=False)
    subparsers = parser.add_subparsers(title='sub-commands', description='valid sub-commands')

    # Documents service sub-command
    events_parser = subparsers.add_parser('events', help='starts a events service')
    events_parser.add_argument('--host', '--address', '-a', default="127.0.0.1", metavar="HOST",
                               help='the address to serve the service on')
    events_parser.add_argument('--port', '-p', type=int, default=0, metavar="PORT",
                               help='the port to serve the service on')
    events_parser.add_argument('--workers', '-w', type=int, default=10,
                               help='number of worker threads to handle requests')
    events_parser.add_argument('--register', '-r', action='store_true',
                               help='whether to register the service with the configured '
                                    'service discovery')
    events_parser.add_argument("--mtap-config", default=None,
                               help="path to MTAP config file")
    events_parser.add_argument("--write-address", action='store_true',
                               help="If set, will write the server's resolved address to a file "
                                    "in the MTAP home directory (~/.mtap/addresses)")
    events_parser.add_argument('--log-level', default='INFO', help='The global python log level.')

    events_parser.set_defaults(func=run_events_server)

    # Serializer processor sub-command
    serializer_parser = subparsers.add_parser('serializer', parents=[processor_parser()])
    serializer_parser.add_argument('serializer', choices=['json'],
                                   help="The name of the serializer to use.")
    serializer_parser.add_argument('--output-dir', '-o', default=".",
                                   help="Directory to write serialized files to.")
    serializer_parser.set_defaults(func=run_serializer_processor)

    # parse and execute
    args = parser.parse_args(args)
    logging.basicConfig(level=args.log_level)
    args.func(args)


if __name__ == "__main__":
    main()
