#  Copyright 2020 Regents of the University of Minnesota.
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
"""Module for deploying a set of processing services and the events server all
at once.

See python/mtap/examples/exampleDeploymentConfiguration.yml for an example
of the yaml deployment configuration
which can be loaded using
:py:meth:`~mtap.deployment.Deployment.from_yaml_file`
"""
import argparse
import logging
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from os import PathLike
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import grpc
from importlib_resources import files, as_file

from mtap import utilities, _config

__all__ = [
    'Deployment',
    'GlobalSettings',
    'SharedProcessorConfig',
    'EventsDeployment',
    'ProcessorDeployment',
    'main',
    'deployment_parser',
    'ServiceDeploymentException',
]

logger = logging.getLogger('mtap.deployment')

PYTHON_EXE = sys.executable


def _get_java() -> str:
    try:
        return str(pathlib.Path(os.environ['JAVA_HOME']) / 'bin' / 'java')
    except KeyError:
        return 'java'


JAVA_EXE = _get_java()


def _listen(process: subprocess.Popen) -> int:
    for line in process.stdout:
        print(line.decode(), end='', flush=True)
    return process.wait()


class ServiceDeploymentException(Exception):
    """Exception raised in the case of a service failing to launch.
    """

    def __init__(self, service_name: str, msg: str):
        super().__init__(service_name, msg)
        self.service_name = service_name
        self.msg = msg


@dataclass
class GlobalSettings:
    """Settings shared by event service and all processors.
    """
    host: Optional[str] = None
    """The global host override, forces all services to use a specific host
    name."""

    mtap_config: Optional[str] = None
    """The path to an MTAP config file to load for all services."""

    log_level: Optional[str] = None
    """A python logging level to pass to all services."""

    register: Optional[bool] = None
    """Whether services should register with service discovery."""

    @staticmethod
    def from_dict(conf: Optional[Dict[str, Any]]) -> 'GlobalSettings':
        """Creates a global settings object from a configuration dictionary.

        Keyword Args:
            conf: The configuration dictionary.

        Returns:
            The global settings object.

        """
        conf = conf or {}
        return GlobalSettings(**conf)


@dataclass
class SharedProcessorConfig:
    """Configuration that is shared between multiple processor services.
    """

    events_addresses: Optional[List[str]] = None
    """An optional GRPC-compatible target for the events service to be used by
    all processors.
    """

    workers: Optional[int] = None
    """The default number of worker threads which will perform processing."""

    additional_args: Optional[List[str]] = None
    """A list of additional arguments that should be appended to every
    processor.
    """

    jvm_args: Optional[List[str]] = None
    """A list of JVM arguments for all Java processors."""

    java_classpath: Optional[str] = None
    """A classpath string that will be passed to all Java processors."""

    java_additional_args: Optional[List[str]] = None
    """A list of additional arguments that is added to only Java processors."""

    startup_timeout: float = 30
    """The default startup timeout for processors."""

    mp_spawn_method: Optional[str] = None
    """A :meth:`multiprocessing.get_context` argument to create the
    multiprocessing context.
    """

    @staticmethod
    def from_dict(conf: Optional[Dict[str, Any]]) -> 'SharedProcessorConfig':
        """Builds a configuration from a dictionary representation.

        Args:
            conf: The configuration dictionary.

        Returns:
            A shared processor config object.
        """
        conf = conf or {}
        return SharedProcessorConfig(**conf)


@dataclass
class _ServiceDeployment:
    workers: Optional[int] = None
    register: Optional[bool] = None
    mtap_config: Optional[str] = None
    log_level: Optional[str] = None

    def service_args(
            self,
            host: Optional[str] = None,
            port: Optional[int] = None,
            sid: Optional[List[str]] = None,
            register_default: Optional[bool] = None,
            global_host: Optional[str] = None,
            workers_default: Optional[int] = None,
            mtap_config_default: Optional[str] = None,
            log_level_default: Optional[str] = None
    ) -> Tuple[List[str], str]:
        call = []

        host = global_host or host
        if host is not None:
            call.extend(['--host', str(host)])

        if port is not None:
            call.extend(['--port', str(port)])

        if self.register or register_default:
            call.append('--register')

        sid = sid or str(uuid.uuid4())
        call.extend(["--sid", sid])

        workers = self.workers or workers_default
        if workers is not None:
            call.extend(['--workers', str(workers)])

        mtap_config = self.mtap_config or mtap_config_default
        if mtap_config is not None:
            call.extend(['--mtap-config', mtap_config])

        log_level = self.log_level or log_level_default
        if log_level is not None:
            call.extend(['--log-level', log_level])

        call.append('--write-address')
        return call, sid


@dataclass
class EventsDeployment:
    """Deployment configuration for the events service.
    """

    enabled: bool = False
    """Whether an events service should be created."""

    address: Optional[str] = None
    """The host address of one events service to launch."""

    addresses: Optional[Sequence[str]] = None
    """The host addresses of multiple events services to launch."""

    workers: Optional[int] = None
    """The number of worker threads the events service should use."""

    register: Optional[bool] = None
    """Whether to register the events service with discovery."""

    mtap_config: Optional[str] = None
    """Path to an mtap configuration file."""

    log_level: Optional[str] = None
    """The log level for the events service."""

    startup_timeout: int = 10
    """The startup timeout for events deployment."""

    @staticmethod
    def from_dict(conf: Optional[Dict]) -> 'EventsDeployment':
        """Creates the EventsDeployment configuration option from a
        configuration dictionary.

        Args:
            conf: The configuration dictionary

        Returns:
            EventsDeployment or None from the configuration dictionary.
        """
        conf = conf or {}
        return EventsDeployment(**conf)


def _create_events_calls(
        events: EventsDeployment,
        global_settings: GlobalSettings
) -> Iterable[Tuple[List[str], str]]:
    if events.addresses is not None and events.address is not None:
        raise ValueError(
            'Only one of `address` and `addresses` can be specified.'
        )

    service_deployment = _ServiceDeployment(
        workers=events.workers,
        register=events.register,
        mtap_config=events.mtap_config,
        log_level=events.log_level
    )

    if events.addresses is None:
        addresses = [events.address]
    else:
        addresses = events.addresses

    for address in addresses:
        host = None
        port = None
        if address:
            splits = address.split(':')
            if len(splits) == 2:
                host, port = splits
                if host == '':
                    host = None
            else:
                host = splits[0]
        call = [PYTHON_EXE, '-m', 'mtap', 'events']
        service_args, sid = service_deployment.service_args(
            host=host,
            port=port,
            register_default=global_settings.register,
            global_host=global_settings.host,
            mtap_config_default=global_settings.mtap_config,
            log_level_default=global_settings.log_level
        )
        call.extend(service_args)
        yield call, sid


@dataclass
class ProcessorDeployment:
    """Deployment configuration for an MTAP processor.

    Used to construct the command for launching the processor. The processor
    should be a Java Class with a main method or a Python module with a main
    block. It should accept the standard MTAP processor deployment arguments
    and launch an MTAP processor using :func:`mtap.run_processor` or the
    equivalent Java method.
    """
    implementation: str
    """Either "java" or "python"."""

    entry_point: str
    """Either the java main class, or the python main module."""

    enabled: bool = True
    """Whether the processor should be launched as part of deployment."""

    instances: int = 1
    """The number of instances of the processor to launch."""

    host: Optional[str] = None
    """The listening host for the processor service."""

    port: Optional[int] = None
    """The listening port for the processor service."""

    workers: Optional[int] = None
    """The number of worker threads per instance."""

    register: Optional[bool] = None
    """Whether the processor should register with the discovery service
    specified in the MTAP config file.
    """

    mtap_config: Optional[str] = None
    """Path to the MTAP configuration file."""

    log_level: Optional[str] = None
    """The log level for the processor."""

    name: Optional[str] = None
    """An optional service name override to use for registration."""

    sid: Union[str, List[str], None] = None
    """An optional service instance unique identifier. If instances is 1 this
    should be a string, if instances is more than 1 this should be a list of
    strings, one for each instance.
    """

    pre_args: Optional[List[str]] = None
    """Arguments that occur prior to the MTAP service arguments (like host,
    port, etc).
    """

    additional_args: Optional[List[str]] = None
    """Arguments that occur after the MTAP service arguments."""

    startup_timeout: Optional[float] = None
    """Optional override startup timeout."""

    @staticmethod
    def from_dict(conf: Dict) -> 'ProcessorDeployment':
        """Creates an MTAP processor deployment configuration from a
        configuration dictionary.

        Args:
            conf: The configuration dictionary.

        Returns:
            ProcessorDeployment object that can be used to construct the call
            for the processor.
        """
        return ProcessorDeployment(**conf)


def _create_processor_calls(
        depl: ProcessorDeployment,
        global_settings: GlobalSettings,
        shared_config: SharedProcessorConfig
) -> Iterable[Tuple[List[str], str]]:
    service_deployment = _ServiceDeployment(
        workers=depl.workers,
        register=depl.register,
        mtap_config=depl.mtap_config,
        log_level=depl.log_level
    )

    if isinstance(depl.port, list):
        ports = depl.port
    elif depl.port is None:
        ports = [None] * depl.instances
    else:
        ports = list(range(depl.port, depl.port + depl.instances))
    for port in ports:
        yield from _create_processor_call(depl, global_settings, port,
                                          service_deployment, shared_config)


def _create_processor_call(depl, global_settings, port, service_deployment,
                           shared_config):
    call = _implementation_args(depl, shared_config)
    if depl.pre_args is not None:
        call.extend(depl.pre_args)
    service_args, sid = service_deployment.service_args(
        host=depl.host,
        port=port,
        sid=depl.sid,
        register_default=global_settings.register,
        global_host=global_settings.host,
        mtap_config_default=global_settings.mtap_config,
        log_level_default=global_settings.log_level,
        workers_default=shared_config.workers
    )
    call.extend(service_args)
    if depl.name is not None:
        call.extend(['--name', depl.name])
    events_addresses = shared_config.events_addresses
    if events_addresses is not None:
        call.extend(['--events', ','.join(events_addresses)])
    if depl.additional_args is not None:
        call.extend(depl.additional_args)
    if shared_config.additional_args is not None:
        call.extend(shared_config.additional_args)
    if (depl.implementation == 'java'
            and shared_config.java_additional_args is not None):
        call.extend(shared_config.java_additional_args)
    yield call, sid


def _implementation_args(depl, shared_config):
    if depl.implementation == 'python':
        call = [PYTHON_EXE, '-m', depl.entry_point]
    elif depl.implementation == 'java':
        call = [str(JAVA_EXE)]
        if shared_config.jvm_args is not None:
            call.extend(shared_config.jvm_args)
        if shared_config.java_classpath is not None:
            call.extend(['-cp', shared_config.java_classpath])
        call.append(depl.entry_point)
    else:
        raise ValueError(
            'Unrecognized implementation: ' + depl.implementation)
    return call


@dataclass
class Deployment:
    """An automatic deployment configuration which launches a configurable set
    of MTAP services.
    """

    global_settings: Optional[GlobalSettings] = None
    """Settings shared among all services."""

    events_deployment: Optional[EventsDeployment] = None
    """Deployment settings for the events service."""

    shared_processor_config: Optional[SharedProcessorConfig] = None
    """Shared configuration settings for all processors."""

    processors: List[ProcessorDeployment] = None
    """Configurations for individual processors."""

    @staticmethod
    def from_dict(conf: Dict) -> 'Deployment':
        """Creates a deployment object from a configuration dictionary.

        Args:
            conf: The configuration dictionary.

        Returns:
            Deployment object created.

        """
        global_settings = GlobalSettings.from_dict(conf.get('global'))
        events = EventsDeployment.from_dict(conf.get('events_service'))
        shared_processor_config = SharedProcessorConfig.from_dict(
            conf.get('shared_processor_config')
        )
        proc_confs = conf.get('processors', [])
        processors = [ProcessorDeployment.from_dict(c) for c in proc_confs]
        return Deployment(
            global_settings,
            events,
            shared_processor_config,
            processors
        )

    @staticmethod
    def from_yaml_file(conf_path: Union[str, bytes, PathLike]) -> 'Deployment':
        """Loads a deployment configuration from a yaml file.

        Args:
            conf_path: The path to the yaml configuration file.

        Returns:
            Deployment object created from the configuration.

        """
        conf_path = pathlib.Path(conf_path)
        from yaml import load
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        with conf_path.open('rb') as f:
            conf = load(f, Loader=Loader)
        return Deployment.from_dict(conf)

    @contextmanager
    def run_servers(self) -> Tuple[List[str], List[List[str]]]:
        """A context manager that starts all the configured services in
        subprocesses and returns.

        Raises:
            ServiceDeploymentException: If one or more of the services fails
                to launch.

        Examples

        >>> deploy = Deployment.from_yaml_file('deploy_config.yml')
        >>> with deploy.run_servers():
        >>>     # do something that requires the servers.
        >>> # servers are automatically shutdown / terminated
        """
        with _ActiveDeployment() as depl:
            addresses = self._do_launch_all_processors(depl)
            yield addresses

    def run_servers_and_wait(self):
        """Starts the specified servers and blocks until KeyboardInterrupt,
        SIGINT, or SIGTERM are received.

        Raises:
            ServiceDeploymentException: If one or more of the services fails
                to launch.
        """
        e = threading.Event()
        signal.signal(signal.SIGINT, lambda *_: e.set())
        signal.signal(signal.SIGTERM, lambda *_: e.set())

        with self.run_servers():
            try:
                e.wait()
            except KeyboardInterrupt:
                pass

    def _do_launch_all_processors(self, depl: '_ActiveDeployment'):
        c = _config.Config()
        enable_proxy = c.get('grpc.enable_proxy', False)
        events_addresses = []

        # deploy events service
        if self.events_deployment.enabled:
            calls = _create_events_calls(self.events_deployment,
                                         self.global_settings)
            for call, sid in calls:
                # Start new session here because otherwise subprocesses
                # get hit with signals meant for parent
                events_address = depl.start_subprocess(
                    call,
                    "events",
                    sid,
                    self.events_deployment.startup_timeout,
                    enable_proxy
                )
                events_addresses.append(events_address)

        # attach deployed events service addresses if it's not already
        # specified or will be picked up by service disc.
        if (not self.global_settings.register
                and not self.events_deployment.register
                and self.shared_processor_config.events_addresses is None):
            self.shared_processor_config.events_addresses = events_addresses

        # deploy processors
        all_processor_addresses = []
        for processor_deployment in self.processors:
            if processor_deployment.enabled:
                calls = _create_processor_calls(
                    processor_deployment,
                    self.global_settings,
                    self.shared_processor_config,
                )
                processor_addresses = []
                for call, sid in calls:
                    logger.debug('Launching processor with call: %s', call)
                    # Start new session here because otherwise subprocesses get
                    # hit with signals meant for parent
                    startup_timeout = (
                            processor_deployment.startup_timeout
                            or self.shared_processor_config.startup_timeout
                    )
                    address = depl.start_subprocess(
                        call,
                        processor_deployment.entry_point,
                        sid,
                        startup_timeout,
                        enable_proxy
                    )
                    processor_addresses.append(address)
                all_processor_addresses.append(processor_addresses)
        print('Done deploying all servers.', flush=True)
        return events_addresses, all_processor_addresses


class _ActiveDeployment:
    def __init__(self):
        self._processor_listeners = []

    def __enter__(self):
        return self

    def __exit__(self, __exc_type, __exc_value, __traceback):
        self.shutdown()

    def start_subprocess(
            self,
            call: List[str],
            name: Any,
            sid: str,
            startup_timeout: float,
            enable_proxy: bool = False
    ) -> str:
        # starts process and listener, stores for later cleanup, returns
        # address.
        p = subprocess.Popen(call,
                             start_new_session=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        listener = threading.Thread(target=_listen, args=(p,))
        listener.start()
        self._processor_listeners.append(
            (p, listener)
        )  # Adding early so it gets cleaned up on failure
        address = None
        deadline = time.time() + startup_timeout
        while time.time() < deadline:
            try:
                address = utilities.read_address(sid)
                break
            except FileNotFoundError:
                time.sleep(1)
        if address is None:
            raise ServiceDeploymentException(
                name,
                f'Failed to launch, timed out waiting: {name}'
            )
        with grpc.insecure_channel(
                address,
                options=[('grpc.enable_http_proxy', enable_proxy)]
        ) as channel:
            future = grpc.channel_ready_future(channel)
            try:
                timeout = deadline - time.time()
                if timeout < 0:
                    raise ServiceDeploymentException(
                        name,
                        f'Failed to launch, timed out waiting: {name}'
                    )
                future.result(timeout=timeout)
            except grpc.FutureTimeoutError:
                raise ServiceDeploymentException(
                    name,
                    f'Failed to launch, unresponsive: {name}'
                )
        return address

    def shutdown(self):
        print("Shutting down all processors")
        excs = []
        for p, listener in self._processor_listeners:
            try:
                p.terminate()
                listener.join(timeout=15.0)
                if listener.is_alive():
                    print(
                        f'Unsuccessfully terminated processor {p.args}'
                        f' ... killing.')
                    p.kill()
                    listener.join()
            except Exception as e:
                print(f"Failed to properly shutdown processor {p.args}")
                excs.append(e)


def main(args: Optional[Sequence[str]] = None,
         conf: Optional[argparse.Namespace] = None):
    if conf is None:
        conf = deployment_parser().parse_args(args)
    if conf.log_level is not None:
        logging.basicConfig(level=conf.log_level)
    if conf.mode == 'run_servers':
        deployment = Deployment.from_yaml_file(conf.deploy_config)
        deployment.run_servers()
    if conf.mode == 'write_example':
        example = files(
            "mtap.examples"
        ).joinpath(
            "exampleDeploymentConfiguration.yml"
        )
        with as_file(example) as path:
            shutil.copyfile(os.fspath(path),
                            "exampleDeploymentConfiguration.yml")
        print('Writing "exampleDeploymentConfiguration.yml" to ' + str(
            pathlib.Path.cwd()))


def deployment_parser() -> argparse.ArgumentParser:
    """Creates a parser for configuration that can be passed to the deployment
    main method.

    Returns:
        The argument parser object that will create a namespace that can
        be passed to :func:`main`.

    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--log-level',
        metavar='LEVEL',
        help="The log level to use for the deployment script."
    )
    subparsers = parser.add_subparsers(title='mode')

    run_servers = subparsers.add_parser('run_servers')
    run_servers.add_argument(
        'deploy_config',
        metavar='CONFIG_FILE',
        type=pathlib.Path,
        help="A path to the deployment configuration to deploy."
    )
    run_servers.set_defaults(mode='run_servers')

    write_example = subparsers.add_parser('write_example')
    write_example.set_defaults(mode='write_example')

    return parser


if __name__ == '__main__':
    main()
