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
from nlpnewt.utils import service_parser

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


def main(args=None):
    logging.basicConfig(level=logging.DEBUG)
    import argparse as argparse
    parser = argparse.ArgumentParser(description='Starts a nlpnewt grpc server.',
                                     allow_abbrev=False)
    subparsers = parser.add_subparsers(title='sub-commands', description='valid sub-commands')

    # Documents service sub-command
    documents_parser = subparsers.add_parser('events', parents=[service_parser()],
                                             help='starts a events service')
    documents_parser.set_defaults(func=run_events_server)

    # parse and execute
    args = parser.parse_args(args)
    args.func(args)


if __name__ == "__main__":
    main()
