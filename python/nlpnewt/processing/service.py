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
import traceback
from argparse import Namespace, ArgumentParser
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Dict, Any

import grpc
from grpc_health.v1 import health, health_pb2_grpc

from nlpnewt import _structs
from nlpnewt._config import Config
from nlpnewt.events import Events
from nlpnewt.api.v1 import processing_pb2_grpc, processing_pb2
from nlpnewt.processing._runners import ProcessorRunner, ProcessingTimesCollector
from nlpnewt.processing.base import EventProcessor

logger = logging.getLogger(__name__)


def run_processor(proc: 'EventProcessor',
                  namespace: Namespace = None,
                  args: List[str] = None):
    """Runs the processor as a GRPC service, blocking until an interrupt signal is received.

    Parameters
    ----------
    proc: EventProcessor
        The processor to host.
    namespace: optional, Namespace
        The parsed arguments from the parser returned by :func:`processor_parser`.
    args: optional, list of str
        Arguments to parse server settings from if ``namespace`` was not supplied.

    """
    if namespace is None:
        processors_parser = ArgumentParser(parents=[processor_parser()])
        processors_parser.add_help = True
        namespace = processors_parser.parse_args(args)

    with Config() as c:
        if namespace.newt_config is not None:
            c.update_from_yaml(namespace.newt_config)
        server = ProcessorServer(proc=proc,
                                 address=namespace.address,
                                 port=namespace.port,
                                 register=namespace.register,
                                 workers=namespace.workers,
                                 processor_id=namespace.identifier,
                                 events_address=namespace.events_address)
        server.start()
        e = threading.Event()

        def handler(_a, _b):
            print("Shutting down", flush=True)
            server.stop()
            e.set()

        signal.signal(signal.SIGINT, handler)
        e.wait()


def processor_parser() -> ArgumentParser:
    """An :obj:`ArgumentParser` that can be used to parse the settings for :func:`run_processor`.

    Returns
    -------
    ArgumentParser
        A parser containing server settings.

    Examples
    --------
    Using this as a parent parser:

    >>> parser = ArgumentParser(parents=[processor_parser()])
    >>> parser.add_argument('--my-arg-1')
    >>> parser.add_argument('--my-arg-2')
    >>> args = parser.parse_args()
    >>> processor = MyProcessor(args.my_arg_1, args.my_arg_2)
    >>> run_processor

    """
    processors_parser = ArgumentParser(add_help=False)
    processors_parser.add_argument('--address', '-a', default="127.0.0.1", metavar="HOST",
                                   help='the address to serve the service on')
    processors_parser.add_argument('--port', '-p', type=int, default=0, metavar="PORT",
                                   help='the port to serve the service on')
    processors_parser.add_argument('--workers', '-w', type=int, default=10,
                                   help='number of worker threads to handle requests')
    processors_parser.add_argument('--register', '-r', action='store_true',
                                   help='whether to register the service with the configured '
                                        'service discovery')
    processors_parser.add_argument("--newt-config", default=None,
                                   help="path to newt config file")
    processors_parser.add_argument('--events-address', '--events', '-e', default=None,
                                   help='address of the events service to use, '
                                        'omit to use discovery')
    processors_parser.add_argument('--identifier', '-i',
                                   help="Optional argument if you want the processor to register "
                                        "under a different identifier than its name.")
    return processors_parser


class _ProcessorServicer(processing_pb2_grpc.ProcessorServicer):
    def __init__(self,
                 config: Config,
                 pr: EventProcessor,
                 address: str,
                 health_servicer: health.HealthServicer,
                 events_address=None,
                 register: bool = False,
                 processor_id=None,
                 params: Dict[str, Any] = None):
        self.config = config
        self.pr = pr
        self.address = address
        self.pr._health_callback = self.update_serving_status
        self.processor_id = processor_id or pr.metadata['name']
        self.events_address = events_address
        self.register = register
        self.params = params
        self.health_servicer = health_servicer
        self._runner = None

        self._times_collector = ProcessingTimesCollector()
        self._deregister = None

    def update_serving_status(self, status):
        self.health_servicer.set(self.processor_id, status)

    def start(self, port: int):
        # instantiate runner
        events = Events(address=self.events_address)
        self._runner = ProcessorRunner(self.pr, events=events, identifier=self.processor_id,
                                       params=self.params)

        self.health_servicer.set(self.processor_id, 'SERVING')

        if self.register:
            from nlpnewt._discovery import Discovery
            service_registration = Discovery(config=self.config)
            self._deregister = service_registration.register_processor_service(
                self.address,
                port,
                self._runner.component_id,
                'v1'
            )

    def shutdown(self):
        self.health_servicer.set(self.processor_id, 'NOT_SERVING')
        if self._deregister is not None:
            self._deregister()
        self._runner.close()
        self._times_collector.close()

    def Process(self, request, context=None):
        params = {}
        _structs.copy_struct_to_dict(request.params, params)
        try:
            response = processing_pb2.ProcessResponse()
            result, times, added_indices = self._runner.call_process(request.event_id, params)
            if result is not None:
                _structs.copy_dict_to_struct(result, response.result, [])

            self._times_collector.add_times(times)
            for k, l in times.items():
                response.timing_info[k].FromTimedelta(l)
            for document_name, l in added_indices.items():
                for index_name in l:
                    created_index = response.created_indices.add()
                    created_index.document_name = document_name
                    created_index.index_name = index_name
            return response
        except Exception as e:
            logger.error(str(e))
            logger.error(traceback.format_exc())
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

    def GetStats(self, request, context):
        r = processing_pb2.GetStatsResponse(processed=self._runner.processed,
                                            failures=self._runner.failure_count)
        for k, v in self._times_collector.get_aggregates(self._runner.component_id).items():
            ts = r.timing_stats[k]
            ts.mean.FromTimedelta(v.mean)
            ts.std.FromTimedelta(v.std)
            ts.max.FromTimedelta(v.max)
            ts.min.FromTimedelta(v.min)
            ts.sum.FromTimedelta(v.sum)
        return r

    def GetInfo(self, request, context):
        return processing_pb2.GetInfoResponse(name=self.pr.metadata['name'],
                                              identifier=self.processor_id)


class ProcessorServer:
    """Host a NLP-NEWT processor as a service.

    Parameters
    ----------
    proc: EventProcessor
        The name of the processor as registered with :func:`processor`.
    address: str
        The address / hostname / IP to host the server on.
    port: int
        The port to host the server on, or 0 to use a random port.
    register: bool, optional
        Whether to register the processor with service discovery.
    events_address: str, optional
        The address of the events server, or omitted / None if the events service should be
        discovered.
    processor_id: str, optional
        The identifier to register the processor under, if omitted the processor name will be used.
    workers: int, optional
        The number of workers that should handle requests.
    params: Dict[str, Any]
        A set of default parameters that will be passed to the processor every time it runs.

    """

    def __init__(self,
                 proc: EventProcessor,
                 address: str,
                 port: int,
                 *,
                 register: bool = False,
                 events_address: str = None,
                 processor_id: str = None,
                 workers: int = None,
                 params: Dict[str, Any] = None):
        self.pr = proc
        self.address = address
        self._port = port
        self.processor_id = processor_id or proc.metadata['name']
        self.params = params or {}
        self.events_address = events_address

        self._health_servicer = health.HealthServicer()
        self._health_servicer.set('', 'SERVING')
        self._servicer = _ProcessorServicer(
            config=Config(),
            pr=proc,
            address=address,
            health_servicer=self._health_servicer,
            register=register,
            processor_id=processor_id,
            params=params,
            events_address=events_address
        )
        prefix = self.processor_id + "-worker"
        workers = workers or 10
        thread_pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix=prefix)
        self._server = grpc.server(thread_pool)
        health_pb2_grpc.add_HealthServicer_to_server(self._health_servicer, self._server)
        processing_pb2_grpc.add_ProcessorServicer_to_server(self._servicer, self._server)
        self._port = self._server.add_insecure_port("{}:{}".format(self.address, self.port))
        self._stopped_event = threading.Event()

    @property
    def port(self) -> int:
        """Returns the port that the server is listening on.

        Returns
        -------
        int
            Bound port.

        """
        return self._port

    def start(self):
        """Starts the service.
        """
        self._server.start()
        self._servicer.start(self.port)
        logger.info('Started processor server with id: "%s"  on address: "%s:%d"',
                    self.processor_id, self.address, self.port)

    def stop(self, *, grace=None):
        """De-registers (if registered with service discovery) the service and immediately stops
        accepting requests, completely stopping the service after a specified `grace` time.

        During the grace period the server will continue to process existing requests, but it will
        not accept any new requests. This function is idempotent, multiple calls will shutdown
        the server after the soonest grace to expire, calling the shutdown event for all calls to
        this function.

        Parameters
        ----------
        grace: float, optional
            The grace period that the server should continue processing requests for shutdown.

        Returns
        -------
        threading.Event
            A shutdown event for the server.
        """
        logger.info('Shutting down processor server with id: "%s"  on address: "%s:%d"',
                    self.processor_id, self.address, self.port)
        self._servicer.shutdown()
        shutdown_event = self._server.stop(grace=grace)
        shutdown_event.wait()
