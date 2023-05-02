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
import asyncio
import functools
import logging
import multiprocessing
import signal
from argparse import ArgumentParser, Namespace
from asyncio import Future
from concurrent.futures import ProcessPoolExecutor
from contextlib import AsyncExitStack, contextmanager
from dataclasses import dataclass
from typing import Optional, Sequence, Union
from uuid import uuid4

import grpc
from grpc_health.v1.health import HealthServicer
from grpc_health.v1.health_pb2_grpc import add_HealthServicer_to_server

from mtap import Config
from mtap.api.v1.processing_pb2_grpc import add_ProcessorServicer_to_server
from mtap.processing import EventProcessor
from mtap.processing._servicer import ProcessorServicer, init_local

logger = logging.getLogger('mtap.processing')


@dataclass
class ProcessorOptions:
    host: Optional[str] = None
    port: Optional[int] = None
    workers: Optional[int] = None
    register: Optional[bool] = None
    mtap_config: Optional[str] = None
    events_addresses: Optional[str] = None
    name: Optional[str] = None
    sid: Optional[str] = None
    log_level: Optional[str] = None
    mp: Optional[bool] = None
    mp_start_method: Optional[str] = None
    grpc_enable_http_proxy: Optional[bool] = None
    mp_context: Optional[multiprocessing.get_context] = None


def processor_parser() -> ArgumentParser:
    """An :class:`~argparse.ArgumentParser` that can be used to parse the
    settings for :func:`run_processor`.

    Returns:
        A parser containing server settings.

    Examples:
        Using this as a parent parser:

        >>> parser = ArgumentParser(parents=[processor_parser()])
        >>> parser.add_argument('--my-arg-1')
        >>> parser.add_argument('--my-arg-2')
        >>> args = parser.parse_args()
        >>> processor = MyProcessor(args.my_arg_1, args.my_arg_2)
        >>> run_processor(processor, args)

    """
    processors_parser = ArgumentParser(add_help=False)
    processors_parser.add_argument(
        '--host', '--address', '-a',
        metavar="HOST",
        help='Host address of the service. Defaults to 127.0.0.1 loopback.'
    )
    processors_parser.add_argument(
        '--port', '-p',
        type=int,
        metavar="PORT",
        help='Bind port of the service. Defaults to a random open port.'
    )
    processors_parser.add_argument(
        '--workers', '-w',
        type=int,
        help='Number of worker processes to handle requests. Defaults to 10.'
    )
    processors_parser.add_argument(
        '--register', '-r',
        action='store_true',
        help='Whether to register the service with the configured service '
             'discovery.'
    )
    processors_parser.add_argument(
        "--mtap-config",
        help="Optional path to a MTAP config file."
    )
    processors_parser.add_argument(
        '--events-addresses', '--events-address', '--events', '-e',
        help='Address of the events service to use, by default will use service discovery.'
    )
    processors_parser.add_argument(
        '--name', '-n',
        help="Optional override service name, defaults to the processor "
             "annotation."
    )
    processors_parser.add_argument(
        '--sid',
        help="A unique identifier for this instance of the processor service. "
             "By default will use a random uuid."
    )
    processors_parser.add_argument(
        '--log-level',
        type=str,
        help="Sets the python log level."
    )
    processors_parser.add_argument(
        '--grpc-enable-http-proxy',
        action='store_true',
        help="If set, will enable usage of http_proxy by grpc."
    )
    processors_parser.add_argument(
        '--mp',
        action='store_true',
        help="If set, will use a process pool executor to run the processor code."
    )
    processors_parser.add_argument(
        '--mp-start-method',
        choices=['spawn', 'fork', 'forkserver'],
        help="A multiprocessing.get_context method to use. Defaults to 'spawn'."
    )
    return processors_parser


def run_processor(proc: EventProcessor,
                  *,
                  mp: bool = False,
                  options: Union[ProcessorOptions, Namespace, None] = None,
                  args: Optional[Sequence[str]] = None,
                  mp_context=None):
    """Runs the processor as a GRPC service, blocking until an interrupt signal
    is received.

    Args:
        proc: The processor to host.
        mp: If true, will create instances of ``proc`` on multiple
            forked processes to process events. This is useful if the processor
            is computationally intensive and would run into Python GIL issues
            on a single process.
        options: The parsed arguments
            from the parser returned by :func:`processor_parser`.
        args: Arguments to parse
            server settings from if ``namespace`` was not supplied.
        mp_context: A multiprocessing context that gets passed to the process
            pool executor in the case of mp = True.

    Examples:
        Will automatically parse arguments:

        >>> run_processor(MyProcessor())

        Manual arguments:

        >>> run_processor(MyProcessor(), args=['-p', '8080'])
    """
    if options is None:
        parser = ArgumentParser(parents=[processor_parser()])
        options = parser.parse_args(args, namespace=ProcessorOptions())

    if not isinstance(options, ProcessorOptions):
        new_options = ProcessorOptions()
        for k, v in vars(options).items():
            if hasattr(new_options, k):
                setattr(new_options, k, v)
        options = new_options

    if mp_context is not None:
        options.mp_context = mp_context

    asyncio.run(serve_forever(proc, options))


async def serve_forever(processor: EventProcessor, options: ProcessorOptions):
    if not isinstance(processor, EventProcessor):
        raise ValueError("Processor must be instance of EventProcessor class.")

    log_level = 'INFO' if options.log_level is None else options.log_level
    logging.basicConfig(level=log_level)

    host = '127.0.0.1' if options.host is None else options.host
    port = 0 if options.port is None else options.port
    workers = 10 if options.workers is None else options.workers
    processor_name = processor.metadata['name'] if options.name is None else options.name
    sid = str(uuid4()) if options.sid is None else options.sid
    mp_start_method = 'spawn' if options.mp_start_method is None else options.mp_start_method
    grpc_enable_http_proxy = (False if options.grpc_enable_http_proxy is None
                              else options.grpc_enable_http_proxy)
    mp_context = (multiprocessing.get_context(mp_start_method) if options.mp_context is None
                  else options.mp_context)

    events_addresses = ([] if options.events_addresses is None
                        else options.events_addresses.split(','))

    async with AsyncExitStack() as exit_stack:
        executor = exit_stack.enter_context(ProcessPoolExecutor(
            max_workers=workers,
            initializer=init_local,
            initargs=(processor, events_addresses, processor_name),
            mp_context=mp_context))

        proc_servicer = ProcessorServicer(processor_name, sid, processor.metadata, executor)
        health_servicer = HealthServicer()

        config = Config()
        grpc_options = config.get('grpc.processor_options', {})
        if options.grpc_enable_http_proxy:
            grpc_options['grpc.enable_http_proxy'] = grpc_enable_http_proxy
        # noinspection PyArgumentList
        server = grpc.aio.server(options=list(grpc_options.items()))
        add_ProcessorServicer_to_server(proc_servicer, server)
        add_HealthServicer_to_server(health_servicer, server)
        actual_port = server.add_insecure_port(f'{host}:{port}')
        if port != 0 and port != actual_port:
            raise ValueError(f"Unable to bind to specified port: {port}. Likely in use.")

        await server.start()
        logger.info(f'Started processor: "{processor_name}" on address: {host}:{actual_port}')

        exit_stack.push_async_callback(server.stop, None)
        exit_stack.enter_context(manage_health(health_servicer, processor_name, sid))

        if options.register:
            from mtap.discovery import DiscoveryMechanism
            disc_mech = DiscoveryMechanism()
            exit_stack.enter_context(disc_mech.register_processor_service(
                name=processor_name,
                sid=sid,
                address=host,
                port=actual_port,
                version='v1'))

        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        for signame in {'SIGINT', 'SIGTERM'}:
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(ask_exit, fut, processor_name, f'{host}:{actual_port}'))

        try:
            await fut
        except asyncio.CancelledError:
            pass


@contextmanager
def manage_health(health_servicer, name, sid):
    health_servicer.set('', 'SERVING')
    health_servicer.set(name, 'SERVING')
    health_servicer.set(sid, 'SERVING')
    try:
        yield
    finally:
        health_servicer.enter_graceful_shutdown()


def ask_exit(fut: Future, processor_name, address):
    print(
        f'Shutting down processor: "{processor_name}" on address: {address}')
    fut.cancel()
