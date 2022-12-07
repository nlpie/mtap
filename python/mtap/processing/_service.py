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
import argparse
import concurrent.futures.thread as thread
import logging
import threading
import time
import traceback
import typing
import uuid
from typing import Any, Dict, Tuple, Sequence, Optional, Union

import google.protobuf.empty_pb2 as empty_pb2
import grpc
import grpc_health.v1.health as health
import grpc_health.v1.health_pb2_grpc as health_pb2_grpc

from mtap import _config
from mtap import _structs
from mtap import data
from mtap import utilities
from mtap.api.v1 import processing_pb2, processing_pb2_grpc
from mtap.processing import _base, _runners, _timing

if typing.TYPE_CHECKING:
    import mtap

logger = logging.getLogger(__name__)
_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def run_processor(proc: 'mtap.EventProcessor',
                  *,
                  mp: bool = False,
                  options: Optional[argparse.Namespace] = None,
                  args: Optional[Sequence[str]] = None,
                  mp_context=None):
    """Runs the processor as a GRPC service, blocking until an interrupt signal is received.

    Args:
        proc (EventProcessor): The processor to host.
        mp (bool): If true, will create instances of ``proc`` on multiple forked processes to
            process events. This is useful if the processor is computationally intensive and would
            run into Python GIL issues on a single process.
        options (~typing.Optional[~argparse.Namespace]): The parsed arguments from the parser
            returned by :func:`processor_parser`.
        args (~typing.Optional[~typing.Sequence[str]]): Arguments to parse server settings from if
            ``namespace`` was not supplied.
        mp_context: A multiprocessing context that gets passed to the process pool executor in the
            case of mp = True.

    Examples:
        Will automatically parse arguments:

        >>> run_processor(MyProcessor())

        Manual arguments:

        >>> run_processor(MyProcessor(), args=['-p', '8080'])


    """
    from mtap import EventProcessor
    if not isinstance(proc, EventProcessor):
        raise ValueError("Processor must be instance of EventProcessor class.")

    if options is None:
        processors_parser = argparse.ArgumentParser(parents=[processor_parser()])
        processors_parser.add_help = True
        options = processors_parser.parse_args(args)

    if options.log_level:
        logging.basicConfig(level=getattr(logging, options.log_level))

    events_addresses = []
    if options.events_addresses is not None:
        events_addresses.extend(options.events_addresses.split(','))

    with _config.Config() as c:
        if options.mtap_config is not None:
            c.update_from_yaml(options.mtap_config)
        # instantiate runner
        name = options.name or proc.metadata['name']
        sid = options.sid

        enable_http_proxy = options.grpc_enable_http_proxy
        if enable_http_proxy is not None:
            c['grpc.events_channel_options.grpc.enable_http_proxy'] = enable_http_proxy
        if mp:
            runner = MpProcessorRunner(proc=proc,
                                       workers=options.workers,
                                       events_address=events_addresses,
                                       processor_name=name,
                                       mp_context=mp_context)
        else:
            client = data.EventsClient(address=events_addresses)
            runner = _runners.ProcessorRunner(proc, client=client,
                                              processor_name=name,
                                              params=None)
        server = ProcessorServer(runner=runner,
                                 sid=sid,
                                 host=options.host,
                                 port=options.port,
                                 register=options.register,
                                 workers=options.workers,
                                 write_address=options.write_address)
        server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop()


_mp_processor = ...  # EventProcessor
_mp_client = ...  # EventClient


def _mp_initialize(proc: 'mtap.EventProcessor', events_address, config):
    global _mp_processor
    global _mp_client
    _config.Config(config)
    _mp_processor = proc
    _mp_client = data.EventsClient(address=events_address)


def _mp_call_process(event_id, event_service_instance_id, params):
    global _mp_processor
    global _mp_client
    with _base.Processor.enter_context() as c, \
            data.Event(event_id=event_id, event_service_instance_id=event_service_instance_id,
                       client=_mp_client) as event:
        with _base.Processor.started_stopwatch('process_method'):
            result = _mp_processor.process(event, params)
        return result, c.times, event.created_indices


class MpProcessorRunner:
    __slots__ = ('pool', 'metadata', 'processor_name', 'component_id')

    def __init__(self,
                 proc: 'mtap.EventProcessor',
                 processor_name: str,
                 component_id: 'Optional[str]' = None,
                 workers: 'Optional[int]' = 8,
                 events_address: 'Optional[Union[str, Sequence[str]]]' = None,
                 mp_context=None):
        if mp_context is None:
            import multiprocessing as mp
            mp_context = mp
        config = _config.Config()
        self.pool = mp_context.Pool(workers,
                                    initializer=_mp_initialize,
                                    initargs=(proc, events_address, dict(config)))
        self.metadata = proc.metadata
        self.processor_name = processor_name
        self.component_id = component_id or processor_name

    def call_process(self,
                     event_id: str,
                     event_service_instance_id: str,
                     params: Optional[Dict[str, Any]]) -> Tuple[Dict, Dict, Dict]:
        p = dict()
        if params is not None:
            p.update(params)

        return self.pool.apply(_mp_call_process, args=(event_id, event_service_instance_id, p))

    def close(self):
        self.pool.terminate()
        self.pool.join()


def processor_parser() -> argparse.ArgumentParser:
    """An :class:`~argparse.ArgumentParser` that can be used to parse the settings for
    :func:`run_processor`.

    Returns:
        ~argparse.ArgumentParser: A parser containing server settings.

    Examples:
        Using this as a parent parser:

        >>> parser = ArgumentParser(parents=[processor_parser()])
        >>> parser.add_argument('--my-arg-1')
        >>> parser.add_argument('--my-arg-2')
        >>> args = parser.parse_args()
        >>> processor = MyProcessor(args.my_arg_1, args.my_arg_2)
        >>> run_processor(processor, args)

    """
    processors_parser = argparse.ArgumentParser(add_help=False)
    processors_parser.add_argument('--host', '--address', '-a', default="127.0.0.1", metavar="HOST",
                                   help='the address to serve the service on')
    processors_parser.add_argument('--port', '-p', type=int, default=0, metavar="PORT",
                                   help='the port to serve the service on')
    processors_parser.add_argument('--workers', '-w', type=int, default=10,
                                   help='number of worker threads to handle requests')
    processors_parser.add_argument('--register', '-r', action='store_true',
                                   help='whether to register the service with the configured '
                                        'service discovery')
    processors_parser.add_argument("--mtap-config", default=None,
                                   help="path to MTAP config file")
    processors_parser.add_argument('--events-addresses', '--events-address', '--events', '-e',
                                   default=None,
                                   help='address of the events service to use, '
                                        'omit to use discovery')
    processors_parser.add_argument('--name', '-n',
                                   help="Optional override service name, defaults to the processor annotation")
    processors_parser.add_argument('--sid',
                                   help="A unique identifier for this instance of the processor service.")
    processors_parser.add_argument('--write-address', action='store_true',
                                   help='If set, will write the server address ')
    processors_parser.add_argument('--log-level', type=str, default='INFO',
                                   help="Sets the python log level.")
    processors_parser.add_argument('--grpc-enable-http-proxy', action='store_true',
                                   help="If set, will enable usage of http_proxy by grpc.")
    processors_parser.add_argument('--mp-spawn-method',
                                   choices=['spawn', 'fork', 'forkserver', None],
                                   help="A multiprocessing spawn method to use.")
    return processors_parser


def _label_index_meta_to_proto(d, message):
    message.name = d['name'] or ''
    message.name_from_parameter = d['name_from_parameter'] or ''
    message.optional = d.get('optional', False)
    message.description = d['description'] or ''
    for property_meta in d['properties']:
        p = message.properties.add()
        p.name = property_meta['name'] or ''
        p.description = property_meta['description'] or ''
        p.data_type = property_meta['data_type'] or ''
        p.nullable = property_meta['nullable']


class _ProcessorServicer(processing_pb2_grpc.ProcessorServicer):
    def __init__(self,
                 config: 'mtap.Config',
                 address: str,
                 sid: str,
                 runner: '_base.ProcessingComponent',
                 health_servicer: health.HealthServicer,
                 register: bool = False):
        self.config = config
        self.address = address
        self.sid = sid
        self._runner = runner
        self.register = register
        self.health_servicer = health_servicer

        self._times_map = {}
        self._deregister = None
        self.processed = 0
        self.failure_count = 0

    def start(self, port: int):

        self.health_servicer.set(self._runner, 'SERVING')

        if self.register:
            from mtap._discovery import Discovery
            service_registration = Discovery(config=self.config)
            self._deregister = service_registration.register_processor_service(self._runner.processor_name,
                                                                               self.sid,
                                                                               self.address,
                                                                               port,
                                                                               'v1')

    def shutdown(self):
        self.health_servicer.set(self._runner.processor_name, 'NOT_SERVING')
        if self._deregister is not None:
            self._deregister()
        self._runner.close()

    def Process(self, request, context=None):
        event_id = request.event_id
        event_service_instance_id = request.event_service_instance_id
        logger.debug(
            'processor_name: %s received process request on event_id: %s with event_service_instance_id: %s',
            self._runner.processor_name, event_id, event_service_instance_id)
        params = {}
        _structs.copy_struct_to_dict(request.params, params)
        try:
            response = processing_pb2.ProcessResponse()
            result, times, added_indices = self._runner.call_process(
                event_id,
                event_service_instance_id,
                params
            )
            if result is not None:
                _structs.copy_dict_to_struct(result, response.result, [])

            _timing.add_times(self._times_map, times)
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
            return empty_pb2.Empty()

    def GetStats(self, request, context):
        r = processing_pb2.GetStatsResponse(processed=self.processed,
                                            failures=self.failure_count)
        for k, v in _timing.create_timer_stats(self._times_map, self._runner.component_id).items():
            ts = r.timing_stats[k]
            ts.mean.FromTimedelta(v.mean)
            ts.std.FromTimedelta(v.std)
            ts.max.FromTimedelta(v.max)
            ts.min.FromTimedelta(v.min)
            ts.sum.FromTimedelta(v.sum)
        return r

    def GetInfo(self, request, context):
        response = processing_pb2.GetInfoResponse()
        _structs.copy_dict_to_struct(self._runner.metadata, response.metadata)
        return response


class ProcessorServer:
    """Host a MTAP processor as a service.

    Args:
        proc (EventProcessor): The event processor to host.
        host (str): The address / hostname / IP to host the server on.
        port (int): The port to host the server on, or 0 to use a random port.

    Keyword Args:
        register (~typing.Optional[bool]): Whether to register the processor with service discovery.
        events_address (~typing.Optional[str]):
            The address of the events server, or omitted / None if the events service should be
            discovered.
        processor_name (~typing.Optional[str]):
            The identifier to register the processor under, if omitted the processor name will be
            used.
        workers (~typing.Optional[int]):
            The number of workers that should handle requests. Defaults to 10.
        params (~typing.Optional[~typing.Mapping[str, ~typing.Any]):
            A set of default parameters that will be passed to the processor every time it runs.
        grpc_enable_http_proxy (bool):
            Enables or disables the grpc channel to the event service using http_proxy or
            https_proxy environment variables.
    """

    def __init__(self,
                 runner: 'mtap.processing.ProcessingComponent',
                 host: str,
                 port: int = 0,
                 *,
                 sid: Optional[None] = None,
                 register: bool = False,
                 workers: Optional[int] = None,
                 write_address: bool = False,
                 config: 'Optional[mtap.Config]' = None):
        self.host = host
        self._port = port
        self.processor_name = runner.processor_name
        self.sid = sid or str(uuid.uuid4())
        self.write_address = write_address

        if config is None:
            config = _config.Config()

        self._health_servicer = health.HealthServicer()
        self._health_servicer.set('', 'SERVING')
        self._health_servicer.set(self.processor_name, 'SERVING')
        self._servicer = _ProcessorServicer(
            config=config,
            address=host,
            sid=self.sid,
            runner=runner,
            health_servicer=self._health_servicer,
            register=register
        )
        workers = workers or 10
        thread_pool = thread.ThreadPoolExecutor(max_workers=workers)
        options = config.get("grpc.processor_options", {})
        self._server = grpc.server(thread_pool, options=list(options.items()))
        health_pb2_grpc.add_HealthServicer_to_server(self._health_servicer, self._server)
        processing_pb2_grpc.add_ProcessorServicer_to_server(self._servicer, self._server)
        self._port = self._server.add_insecure_port("{}:{}".format(self.host, self.port))
        self._stopped_event = threading.Event()
        self._address_file = None

    @property
    def port(self) -> int:
        """int: Port the hosted server is bound to.
        """
        return self._port

    def start(self):
        """Starts the service.
        """
        self._server.start()
        self._servicer.start(self.port)
        if self.write_address:
            self._address_file = utilities.write_address_file('{}:{}'.format(self.host, self.port), self.sid)
        logger.info('Started processor server with name: "%s"  on address: "%s:%d"',
                    self.processor_name, self.host, self.port)

    def stop(self, *, grace: Optional[float] = None) -> threading.Event:
        """De-registers (if registered with service discovery) the service and immediately stops
        accepting requests, completely stopping the service after a specified `grace` time.

        During the grace period the server will continue to process existing requests, but it will
        not accept any new requests. This function is idempotent, multiple calls will shutdown
        the server after the soonest grace to expire, calling the shutdown event for all calls to
        this function.

        Keyword Args:
            grace (~typing.Optional[float]):
                The grace period that the server should continue processing requests for shutdown.

        Returns:
            threading.Event: A shutdown event for the server.
        """
        print('Shutting down processor server with name: "{}"  on address: "{}:{}"'.format(
            self.processor_name, self.host, self.port))
        if self._address_file is not None:
            self._address_file.unlink()
        self._servicer.shutdown()
        return self._server.stop(grace=grace)
