#  Copyright (c) Regents of the University of Minnesota.
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
"""Host a pipeline as a service."""

import argparse
import logging
import threading
import uuid
from argparse import ArgumentParser
from concurrent.futures import thread
from typing import Optional, Sequence

import grpc
from grpc_health.v1 import health, health_pb2_grpc
from grpc_status import rpc_status

from mtap import _config, utilities
from mtap._common import run_server_forever
from mtap._events_client import events_client, EventsClient, EventsAddressLike
from mtap._structs import copy_struct_to_dict, copy_dict_to_struct
from mtap.api.v1 import pipeline_pb2_grpc, pipeline_pb2
from mtap.pipeline._mp_pipeline import MpPipelinePool
from mtap.pipeline._pipeline import Pipeline
from mtap.processing import ProcessingException
from mtap.serialization import dict_to_event, event_to_dict

logger = logging.getLogger('mtap.processing')


def run_pipeline_server(pipeline: Pipeline,
                        options: Optional[argparse.Namespace] = None,
                        args: Optional[Sequence[str]] = None,
                        mp_context=None):
    """Hosts an end-to-end pipeline as a grpc Pipeline service and blocks forever.

    Args:
        pipeline: The pipeline to host.
        options: A namespace parsed from arguments.
        args: A sequence of string arguments.
        mp_context: A multiprocessing.get_context to use.

    """
    if not isinstance(pipeline, Pipeline):
        raise ValueError("pipeline must be instance of the Pipeline class")

    if options is None:
        parser = ArgumentParser(parents=[pipeline_parser()], add_help=True)
        options = parser.parse_args(args)

    if options.log_level:
        logging.basicConfig(level=getattr(logging, options.log_level))

    if options.events_addresses is not None:
        pipeline.events_address = list(options.events_addresses.split(','))

    with _config.Config() as c:
        if options.mtap_config is not None:
            c.update_from_yaml(options.mtap_config)

        if options.name is not None:
            pipeline.name = options.name

        enable_http_proxy = options.grpc_enable_http_proxy
        if enable_http_proxy is not None:
            c['grpc.events_channel_options.grpc.enable_http_proxy'] \
                = enable_http_proxy

        if mp_context is not None:
            pipeline.mp_config.mp_context = mp_context

        with MpPipelinePool(pipeline) as pool:
            server = PipelineServer(
                pool=pool,
                events_address=pipeline.events_address,
                host=options.host,
                port=options.port,
                sid=options.sid,
                workers=options.workers,
                write_address=options.write_address
            )
            run_server_forever(server)


def pipeline_parser() -> ArgumentParser:
    """Creates an argument parser for the pipeline hosting options.

    Returns: An argument parser.

    """
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        '--host', '--address', '-a',
        default="127.0.0.1",
        metavar="HOST",
        help="The IP to serve the service on."
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=0,
        metavar="PORT",
        help="The port to server the service on."
    )
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=10,
        help="The number of workers threads to handle requests."
    )
    parser.add_argument(
        "--mtap-config",
        default=None,
        help="Path to the MTAP configuration file."
    )
    parser.add_argument(
        '--events-addresses', '--events-address', '--events', '-e',
        default=None,
        help="Optional override events address."
    )
    parser.add_argument(
        '--name', '-n',
        help="Optional override service name, defaults to the pipeline name."
    )
    parser.add_argument(
        '--sid',
        help="A unique identifier for this instance of a pipeline service."
    )
    parser.add_argument(
        '--write-address', action='store_true',
        help="If set, will write the server address to a designated location."
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        help="Sets the python log level."
    )
    parser.add_argument(
        '--grpc-enable-http-proxy',
        action='store_true',
        help="If set, will enable usage of http_proxy by grpc."
    )
    return parser


class PipelineServicer(pipeline_pb2_grpc.PipelineServicer):
    def __init__(self, pool: MpPipelinePool, events: EventsClient):
        self.pool = pool
        self.events = events

    def Process(self, request, context):
        event_dict = {}
        copy_struct_to_dict(request.event, event_dict)
        with dict_to_event(event_dict, client=self.events) as event:
            params = {}
            copy_struct_to_dict(request.params, params)
            res = self.pool.start_task(event, params)
            _, result, error = res.get()
            if error is not None:
                exc = ProcessingException(error)
                logger.error(error)
                context.abort_with_status(rpc_status.to_status(exc.to_rpc_status()))
                return
            response = pipeline_pb2.ProcessEventInPipelineResponse()
            copy_dict_to_struct(event_to_dict(event), response.event)
            response.result.elapsed_time.FromTimedelta(result.elapsed_time)
            for component_result in result.component_results:
                cr_response = response.result.component_results.add()
                cr_response.identifier = component_result.identifier
                copy_dict_to_struct(component_result.result_dict, cr_response.result_dict)
                for k, l in component_result.timing_info.items():
                    cr_response.timing_info[k].FromTimedelta(l)

            if request.keep_after:
                event.lease()
        return response


class PipelineServer:
    def __init__(self,
                 pool: MpPipelinePool,
                 events_address: EventsAddressLike,
                 host: str,
                 port: int = 0,
                 *,
                 sid: Optional[str] = None,
                 workers: Optional[int] = None,
                 write_address: bool = False):
        self.pool = pool
        self.pipeline_name = pool.pipeline.name
        self.host = host
        self.sid = sid or str(uuid.uuid4())
        self.write_address = write_address

        health_servicer = health.HealthServicer()
        health_servicer.set('', 'SERVING')
        health_servicer.set(self.pipeline_name, 'SERVING')
        self.events = events_client(events_address)
        servicer = PipelineServicer(self.pool, self.events)
        workers = workers or 10
        self._thread_pool = thread.ThreadPoolExecutor(max_workers=workers)
        config = _config.Config()
        options = config.get("grpc.processor_options", {})
        self._server = grpc.server(self._thread_pool, options=list(options.items()))
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self._server)
        pipeline_pb2_grpc.add_PipelineServicer_to_server(servicer, self._server)
        self._port = self._server.add_insecure_port(f"{self.host}:{port}")
        if port != 0 and self._port != port:
            raise ValueError(f"Unable to bind on port {port}, likely in use.")
        self._address_file = None

    @property
    def port(self) -> int:
        """Port the hosted server is bound to.
        """
        return self._port

    def start(self):
        self._server.start()
        if self.write_address:
            self._address_file = utilities.write_address_file(f'{self.host}:{self.port}', self.sid)
        logger.info(
            'Started pipeline server with name: "%s"  on address: "%s:%d"',
            self.pipeline_name, self.host, self.port)

    def stop(self, *, grace: Optional[float] = None) -> threading.Event:
        print(f'Shutting down pipeline server with name: '
              f'"{self.pipeline_name}" on address: "{self.host}:{self.port}')
        if self._address_file is not None:
            self._address_file.unlink()
        self._thread_pool.shutdown()
        self.events.close()
        return self._server.stop(grace)
