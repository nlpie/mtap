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
import signal
import threading

from nlpnewt._config import Config
from nlpnewt._events_service import EventsServer
from nlpnewt.processing import ProcessorServer

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def run_events_server(args):
    """Runs the documents service, blocking until keyboard interrupt

    Parameters
    ----------
    args
        Command line arguments.
    """
    with Config() as c:
        if args.config is not None:
            c.update_from_yaml(args.config)
        server = EventsServer(args.address, args.port, register=args.register, workers=args.workers)
        server.start()
        e = threading.Event()

        def handler(sig, frame):
            print("Shutting down", flush=True)
            server.stop()
            e.set()
        signal.signal(signal.SIGINT, handler)
        e.wait()


def run_processor_service(args):
    """Runs a processor, blocking until keyboard interrupt

    Parameters
    ----------
    args
        Command line arguments.
    """
    import importlib
    if args.module is not None:
        importlib.import_module(args.module)

    with Config() as c:
        if args.config is not None:
            c.update_from_yaml(args.config)
        processor_name = args.name
        server = ProcessorServer(processor_name,
                                 address=args.address,
                                 port=args.port,
                                 register=args.register,
                                 workers=args.workers,
                                 processor_id=args.identifier,
                                 events_address=args.events_address,
                                 args=args.args)
        server.start()
        e = threading.Event()

        def handler(sig, frame):
            print("Shutting down", flush=True)
            server.stop()
            e.set()
        signal.signal(signal.SIGINT, handler)
        e.wait()


def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    import argparse as argparse
    parser = argparse.ArgumentParser(description='Starts a nlpnewt grpc server.',
                                     allow_abbrev=False)
    subparsers = parser.add_subparsers(title='sub-commands', description='valid sub-commands')

    # Arguments shared by service sub-commands
    service_parser = argparse.ArgumentParser(add_help=False)
    service_parser.add_argument('--address', '-a', default="127.0.0.1", metavar="HOST",
                                help='the address to serve the service on')
    service_parser.add_argument('--port', '-p', type=int, default=0, metavar="PORT",
                                help='the port to serve the service on')
    service_parser.add_argument('--workers', '-w', type=int, default=10,
                                help='number of worker threads to handle requests')
    service_parser.add_argument('--register', '-r', action='store_true',
                                help='whether to register the service with the configured service '
                                     'discovery')
    service_parser.add_argument("--config", '-c', default=None,
                                help="path to config file")

    # Documents service sub-command
    documents_parser = subparsers.add_parser('events', parents=[service_parser],
                                             help='starts a events service')
    documents_parser.set_defaults(func=run_events_server)

    # Processing services sub-command
    processors_parser = subparsers.add_parser('processor', parents=[service_parser],
                                              help='starts a processor service')
    processors_parser.add_argument('--events-address', '--events', '-e', default=None,
                                   help='address of the events service to use, '
                                        'omit to use discovery')
    processors_parser.add_argument('--name', '-n', required=True,
                                   help='The name the processor is registered under using the '
                                        'processor decorator.')
    processors_parser.add_argument('--identifier', '-i',
                                   help="Optional argument if you want the processor to register "
                                        "under a different identifier than its name.")
    processors_parser.add_argument('--module', '-m', default=None,
                                   help='A python module to load to trigger the processor '
                                        'decorator')
    processors_parser.add_argument('args', nargs='*', default=None,
                                   help='args that will be passed to the processor')
    processors_parser.set_defaults(func=run_processor_service)

    # parse and execute
    args = parser.parse_args(args)
    args.func(args)


if __name__ == "__main__":
    main()
