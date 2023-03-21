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
"""Module for deploying a set of processing services and the events server all at once.

Examples:
    See python/mtap/examples/exampleDeploymentConfiguration.yml for an example of the yaml deployment configuration
    which can be loaded using :py:meth:`~mtap.deployment.Deployment.from_yaml_file`

    An example configuration

    >>> deploy = Deployment(
    >>>     GlobalSettings(host='0.0.0.0'),
    >>>     EventsDeployment(port=10100, workers=8),
    >>>     SharedProcessorConfig(workers=8, jvm_args=['-Xms32m', '-Xmx8g'], classpath='blah.jar'),
    >>>     ProcessorDeployment(implementation='python',
    >>>                         entry_point='mtap.examples.example_processor',
    >>>                         instances=4,
    >>>                         port=10101,
    >>>                         workers=4),
    >>>     ProcessorDeployment(implementation='java',
    >>>                         entry_point='edu.umn.nlpie.mtap.WordOccurrencesExampleProcessor',
    >>>                         port=10105)
    >>> )
    >>> deploy.run_servers()



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
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import grpc

from mtap import utilities, _config

__all__ = [
    'Deployment', 'GlobalSettings', 'SharedProcessorConfig', 'EventsDeployment', 'ServiceDeployment',
    'ProcessorDeployment', 'main', 'deployment_parser', 'ServiceDeploymentException',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GlobalSettings:
    """Settings shared by event service and all processors.

    Keyword Args:
        host (~typing.Optional[str]): The global host override, forces all services to use a specific host name.
        mtap_config (~typing.Optional[str]): The path to an MTAP config file to load for all services.
        log_level (~typing.Optional[str]): A python logging level to pass to all services.
        register (~typing.Optional[bool]): Whether services should register with service discovery.

    Attributes:
        host (~typing.Optional[str]): The global host override, forces all services to use a specific host name.
        mtap_config (~typing.Optional[str]): The path to an MTAP config file to load for all services.
        log_level (~typing.Optional[str]): A python logging level to pass to all services.
        register (~typing.Optional[bool]): Whether services should register with service discovery.

    """

    def __init__(self, *,
                 host: Optional[str] = None,
                 mtap_config: Optional[str] = None,
                 log_level: Optional[str] = None,
                 register: Optional[bool] = None):
        self.host = host
        self.mtap_config = mtap_config
        self.log_level = log_level
        self.register = register

    @staticmethod
    def from_conf(conf: Optional[Dict]) -> 'GlobalSettings':
        """Creates a global settings object from a configuration dictionary.

        Keyword Args:
            conf (~typing.Optional[~typing.Dict]): The configuration dictionary.

        Returns:
            GlobalSettings: The global settings object.

        """
        conf = conf or {}
        return GlobalSettings(host=conf.get('host'), mtap_config=conf.get('mtap_config'),
                              log_level=conf.get('log_level'), register=conf.get('register'))


class SharedProcessorConfig:
    """Configuration that is shared between multiple processor services.

    Keyword Args:
        events_addresses (~typing.Optional[~typing.List[str]]): An optional GRPC-compatible target for the events
            service to be used by all processors.
        workers (~typing.Optional[int]): The default number of worker threads which will perform
            processing.
        additional_args (~typing.Optional[~typing.List[str]]): a list of additional arguments that
            should be appended to every processor.
        jvm_args (~typing.Optional[~typing.List[str]]): a list of JVM arguments for all java
            processors.
        java_classpath (~typing.Optional[str]): A classpath string that will be passed to all java
            processors.
        startup_timeout (~typing.Optional[float]): The default startup timeout for processors.
        mp_spawn_method (~typing.Optional[str]): A :meth:`multiprocessing.get_context` argument to create
            the multiprocessing context.

    Attributes:
        events_addresses (~typing.Optional[~typing.List[str]]): An optional GRPC-compatible target for the events
            service to be used by all processors.
        workers (~typing.Optional[int]): The default number of worker threads which will perform
            processing.
        additional_args (~typing.Optional[~typing.List[str]]): a list of additional arguments that
            should be appended to every processor.
        jvm_args (~typing.Optional[~typing.List[str]]): a list of JVM arguments for all java
            processors.
        java_classpath (~typing.Optional[str]): A classpath string that will be passed to all java
            processors.
        startup_timeout (~typing.Optional[float]): The default startup timeout for processors.
        mp_spawn_method (~typing.Optional[str]): A :meth:`multiprocessing.get_context` argument to create
            the multiprocessing context.

    """

    def __init__(self, *,
                 events_addresses: Optional[List[str]] = None,
                 workers: Optional[int] = None,
                 additional_args: Optional[List[str]] = None,
                 jvm_args: Optional[List[str]] = None,
                 java_classpath: Optional[str] = None,
                 java_additional_args: Optional[List[str]] = None,
                 startup_timeout: Optional[float] = None,
                 mp_spawn_method: Optional[str] = None):
        self.events_addresses = events_addresses
        self.workers = workers
        self.additional_args = additional_args
        self.jvm_args = jvm_args
        self.java_classpath = java_classpath
        self.java_additional_args = java_additional_args
        self.startup_timeout = startup_timeout or 30.0
        self.mp_spawn_method = mp_spawn_method

    @staticmethod
    def from_conf(conf: Optional[Dict]) -> 'SharedProcessorConfig':
        """Builds a configuration from a dictionary representation.

        Args:
            conf (~typing.Optional[~typing.Dict]): The configuration dictionary.

        Returns:
            SharedProcessorConfig object.

        """
        conf = conf or {}
        return SharedProcessorConfig(**conf)


class ServiceDeployment:
    """Shared configuration for services, both events and processors.

    Keyword Args:
        workers (~typing.Optional[int]): The number of workers.
        register (~typing.Optional[bool]): Whether to use service discovery.
        mtap_config (~typing.Optional[str]): A path to the mtap configuration.
        log_level (~typing.Optional[str]): The log level.

    Attributes:
        workers (~typing.Optional[int]): The number of workers.
        register (~typing.Optional[bool]): Whether to use service discovery.
        mtap_config (~typing.Optional[str]): A path to the mtap configuration.
        log_level (~typing.Optional[str]): The log level.
    """
    def __init__(self, *,
                 workers: Optional[int],
                 register: Optional[bool],
                 mtap_config: Optional[str],
                 log_level: Optional[str]):
        self.workers = workers
        self.register = register
        self.mtap_config = mtap_config
        self.log_level = log_level

    def _service_args(self,
                      host: Optional[str] = None,
                      port: Optional[int] = None,
                      unique_service_identifier: Optional[List[str]] = None,
                      register_default: Optional[bool] = None,
                      global_host: Optional[str] = None,
                      workers_default: Optional[int] = None,
                      mtap_config_default: Optional[str] = None,
                      log_level_default: Optional[str] = None):
        call = []

        host = global_host or host
        if host is not None:
            call.extend(['--host', str(host)])

        if port is not None:
            call.extend(['--port', str(port)])

        if self.register or register_default:
            call.append('--register')

        sid = unique_service_identifier or str(uuid.uuid4())
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


class EventsDeployment:
    """Deployment configuration for the events service.

    Keyword Args:
        enabled (bool): Whether an events service should be created.
        addresses (~typing.Optional[~typing.Sequence[str]]): The host address of the events service.
        workers (~typing.Optional[int]): The number of worker threads the events service should use.
        register (~typing.Optional[bool]): Whether to register the events service with discovery.
        mtap_config (~typing.Optional[str]): Path to an mtap configuration file.
        log_level (~typing.Optional[str]): The log level for the events service.

    Attributes:
        enabled (bool): Whether an events service should be created.
        addresses (~typing.Optional[~typing.Sequence[str]]): The host address of the events service.
        service_deployment (ServiceDeployment):
            The service deployment settings (workers, registration, config, logging).
    """

    def __init__(self, *,
                 enabled: bool = True,
                 addresses: Optional[Sequence[str]] = None,
                 workers: Optional[int] = None,
                 register: Optional[bool] = None,
                 mtap_config: Optional[str] = None,
                 log_level: Optional[str] = None):
        self.enabled = enabled
        self.addresses = addresses
        self.service_deployment = ServiceDeployment(workers=workers, register=register, mtap_config=mtap_config,
                                                    log_level=log_level)

    def create_calls(self, global_settings: GlobalSettings) -> Iterable[Tuple[List[str], str]]:
        for address in self.addresses:
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
            service_args, sid = self.service_deployment._service_args(
                host=host,
                port=port,
                register_default=global_settings.register,
                global_host=global_settings.host,
                mtap_config_default=global_settings.mtap_config,
                log_level_default=global_settings.log_level
            )
            call.extend(service_args)
            yield call, sid

    @staticmethod
    def from_conf(conf: Optional[Dict]) -> 'EventsDeployment':
        """Creates the EventsDeployment configuration option from a configuration dictionary.

        Args:
            conf (~typing.Optional[~typing.Dict]): The configuration dictionary

        Returns:
            EventsDeployment or None from the configuration dictionary.

        """
        conf = conf or {}

        enabled = conf.get('enabled')
        if enabled is None:
            enabled = False

        address = conf.get('address', None) or conf.get('addresses', None)
        if address is None:
            addresses = []
        elif isinstance(address, str):
            addresses = [address]
        elif isinstance(address, Iterable):
            addresses = list(address)
        else:
            raise ValueError('Unrecognized type of address: ' + type(address))

        return EventsDeployment(enabled=enabled, addresses=addresses,
                                workers=conf.get('workers'), register=conf.get('register'),
                                mtap_config=conf.get('mtap_config'))


class ProcessorDeployment:
    """Deployment configuration for an MTAP processor.

    Used to construct the command for launching the processor. The processor should be a Java Class
    with a main method or a Python module with a main block. It should accept the standard MTAP
    processor deployment arguments and launch an MTAP processor using :func:`mtap.run_processor` or
    the equivalent Java method.

    Args:
        implementation (str): Either "java" or "python".
        entry_point (str): Either the java main class, or the python main module.

    Keyword Args:
        enabled (~typing.Optional[bool]): Whether the processor should be launched as part of
            deployment. Default is `True` if `None`.
        instances (~typing.Optional[int]): The number of instances of the processor to launch.
            Default is `1` if `None`.
        host (~typing.Optional[str]): The listening host for the processor service.
        port (~typing.Optional[int]): The listening port for the processor service.
        workers (~typing.Optional[int]): The number of worker threads per instance.
        register (~typing.Optional[bool]):
            Whether the processor should register with the discovery service specified in the MTAP
            configuration
        mtap_config (~typing.Optional[str]): Path to the MTAP configuration file.
        log_level (~typing.Optional[str]): The log level for the processor.
        identifier (~typing.Optional[str]): An optional identifier override to use for registration.
        pre_args (~typing.Optional[~typing.List[str]]):
            Arguments that occur prior to the MTAP service arguments (like host, port, etc).
        additional_args (~typing.Optional[~typing.List[str]]):
            Arguments that occur after the MTAP service arguments.
        startup_timeout (~typing.Optional[float]): Optional override startup timeout.
        mp_spawn_method (~typing.Optional[str]): A :meth:`multiprocessing.get_context` argument to create
            the multiprocessing context.

    Attributes:
        implementation (str): Either "java" or "python".
        entry_point (str): Either the java main class, or the python main module.
        enabled (bool): Whether the processor should be launched as part of deployment.
        instances (int): The number of instances of the processor to launch.
        host (~typing.Optional[str]): The listening host for the processor service.
        port (~typing.Optional[int]): The listening port for the processor service.
        service_deployment (ServiceDeployment):
            The service deployment settings (workers, registration, config, logging).
        pre_args (~typing.Optional[~typing.List[str]]):
            Arguments that occur prior to the MTAP service arguments (like host, port, etc).
        additional_args (~typing.Optional[~typing.List[str]]):
            Arguments that occur after the MTAP service arguments.
        startup_timeout (~typing.Optional[float]): Optional override startup timeout.
        mp_spawn_method (~typing.Optional[str]): A :meth:`multiprocessing.get_context` argument to create
            the multiprocessing context.

    """

    def __init__(self,
                 implementation: str,
                 entry_point: str,
                 *, enabled: Optional[bool] = None,
                 instances: Optional[int] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 workers: Optional[int] = None,
                 register: Optional[bool] = None,
                 mtap_config: Optional[str] = None,
                 log_level: Optional[str] = None,
                 name: Optional[str] = None,
                 unique_service_identifier: Optional[List[str]] = None,
                 pre_args: Optional[List[str]] = None,
                 additional_args: Optional[List[str]] = None,
                 startup_timeout: Optional[float] = None,
                 mp_spawn_method: Optional[str] = None):
        self.implementation = implementation
        self.entry_point = entry_point
        self.enabled = enabled if enabled is not None else True
        self.instances = instances or 1
        if not isinstance(self.instances, int) or self.instances < 1:
            raise ValueError("Instances must be strictly positive integer.")
        self.name = name
        self.unique_service_identifier = unique_service_identifier
        self.pre_args = pre_args
        self.additional_args = additional_args
        self.host = host
        self.port = port
        self.service_deployment = ServiceDeployment(workers=workers, register=register, mtap_config=mtap_config,
                                                    log_level=log_level)
        self.startup_timeout = startup_timeout
        self.mp_spawn_method = mp_spawn_method

    @staticmethod
    def from_conf(conf: Dict) -> 'ProcessorDeployment':
        """Creates an MTAP processor deployment configuration from a configuration dictionary.

        Args:
            conf (~typing.Dict): The configuration dictionary.

        Returns:
            ProcessorDeployment object that can be used to constuct the call for the processor.

        """
        return ProcessorDeployment(**conf)

    def create_calls(self,
                     global_settings: GlobalSettings,
                     shared_config: SharedProcessorConfig) -> Iterable[Tuple[List[str], str]]:
        if isinstance(self.port, list):
            ports = self.port
        elif self.port is None:
            ports = [None] * self.instances
        else:
            ports = list(range(self.port, self.port + self.instances))
        for port in ports:
            if self.implementation == 'python':
                call = [PYTHON_EXE, '-m', self.entry_point]
                mp_spawn_method = shared_config.mp_spawn_method
                if self.mp_spawn_method is not None:
                    mp_spawn_method = self.mp_spawn_method
                if mp_spawn_method is not None:
                    call.extend(['--mp-spawn-method', mp_spawn_method])
            elif self.implementation == 'java':
                call = [str(JAVA_EXE)]
                if shared_config.jvm_args is not None:
                    call.extend(shared_config.jvm_args)
                if shared_config.java_classpath is not None:
                    call.extend(['-cp', shared_config.java_classpath])
                call.append(self.entry_point)
            else:
                raise ValueError('Unrecognized implementation: ' + self.implementation)

            if self.pre_args is not None:
                call.extend(self.pre_args)

            service_args, sid = self.service_deployment._service_args(
                host=self.host,
                port=port,
                unique_service_identifier=self.unique_service_identifier,
                register_default=global_settings.register,
                global_host=global_settings.host,
                mtap_config_default=global_settings.mtap_config,
                log_level_default=global_settings.log_level,
                workers_default=shared_config.workers
            )
            call.extend(service_args)

            if self.name is not None:
                call.extend(['--name', self.name])

            events_addresses = shared_config.events_addresses
            if events_addresses is not None:
                call.extend(['--events', ','.join(events_addresses)])

            if self.additional_args is not None:
                call.extend(self.additional_args)

            if shared_config.additional_args is not None:
                call.extend(shared_config.additional_args)

            if self.implementation == 'java' and shared_config.java_additional_args is not None:
                call.extend(shared_config.java_additional_args)

            yield call, sid


class Deployment:
    """An automatic deployment configuration which launches a configurable set of MTAP services.

    Args:
         global_settings (~typing.Optional[GlobalSettings]): Settings shared among all services.
         events_deployment (~typing.Optional[EventsDeployment]):
            Deployment settings for the events service.
         shared_processor_config (~typing.Optional[SharedProcessorConfig]):
            Shared configuration settings for all processors.
         *processors (ProcessorDeployment): Configurations for individual processors.

    Attributes:
        global_settings (~typing.Optional[GlobalSettings]): Settings shared among all services.
        events_deployment (~typing.Optional[EventsDeployment]):
            Deployment settings for the events service.
        shared_processor_config (~typing.Optional[SharedProcessorConfig]):
            Shared configuration settings for all processors.
        processors (~typing.List[ProcessorDeployment]): Configurations for individual processors.
    """

    def __init__(self,
                 global_settings: Optional[GlobalSettings] = None,
                 events_deployment: Optional[EventsDeployment] = None,
                 shared_processor_config: Optional[SharedProcessorConfig] = None,
                 *processors: ProcessorDeployment):
        self.global_settings = global_settings
        self.events_deployment = events_deployment
        self.shared_processor_config = shared_processor_config
        self.processors = list(processors)
        self._processor_listeners = []

    @staticmethod
    def load_configuration(conf: Dict) -> 'Deployment':
        """Creates a deployment object from a configuration dictionary.

        Args:
            conf (~typing.Dict): The configuration dictionary.

        Returns:
            Deployment object created.

        """
        global_settings = GlobalSettings.from_conf(conf.get('global'))
        events = EventsDeployment.from_conf(conf.get('events_service'))
        shared_processor_config = SharedProcessorConfig.from_conf(conf.get('shared_processor_config'))
        processors_list = conf.get('processors', [])
        processors = [ProcessorDeployment.from_conf(c) for c in processors_list]
        return Deployment(global_settings, events, shared_processor_config, *processors)

    @staticmethod
    def from_yaml_file(conf_path: Union[pathlib.Path, str]) -> 'Deployment':
        """Loads a deployment configuration from a yaml file.

        Args:
            conf_path (str or pathlib.Path): The path to the yaml configuration file.

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
        return Deployment.load_configuration(conf)

    @contextmanager
    def run_servers(self):
        """A context manager that starts all the configured services in subprocesses and returns.

        Raises:
            ServiceDeploymentException: If one or more of the services fails to launch.

        Examples

        >>> deploy = Deployment.from_yaml_file('deploy_config.yml')
        >>> with deploy.run_servers():
        >>>     # do something that requires the servers.
        >>> # servers are automatically shutdown / terminated when the block is exited
        """
        try:
            self._do_launch_all_processors()
            yield self
        finally:
            self.shutdown()

    def run_servers_and_wait(self):
        """Starts the specified servers and blocks until KeyboardInterrupt, SIGINT, or SIGTERM are received.
        """
        e = threading.Event()
        signal.signal(signal.SIGINT, lambda *_: e.set())
        signal.signal(signal.SIGTERM, lambda *_: e.set())

        with self.run_servers():
            try:
                e.wait()
            except KeyboardInterrupt:
                pass

    def _do_launch_all_processors(self):
        c = _config.Config()
        enable_proxy = c.get('grpc.enable_proxy', False)
        events_addresses = []

        # deploy events service
        if self.events_deployment.enabled:
            for call, sid in self.events_deployment.create_calls(self.global_settings):
                # Start new session here because otherwise subprocesses get hit with signals meant for parent
                events_address = self._start_subprocess(call, "events", sid, 30, enable_proxy)
                events_addresses.append(events_address)

        # attach deployed events service addresses if it's not already specified or will be picked up by service disc.
        if (not self.global_settings.register
                and not self.events_deployment.service_deployment.register
                and self.shared_processor_config.events_addresses is None):
            self.shared_processor_config.events_addresses = events_addresses

        # deploy processors
        for processor_deployment in self.processors:
            if processor_deployment.enabled:
                for call, sid in processor_deployment.create_calls(self.global_settings,
                                                                   self.shared_processor_config):
                    logger.debug('Launching processor with call: %s', call)
                    # Start new session here because otherwise subprocesses get hit with signals meant for parent
                    startup_timeout = (processor_deployment.startup_timeout
                                       or self.shared_processor_config.startup_timeout)
                    self._start_subprocess(call, processor_deployment.entry_point, sid, startup_timeout, enable_proxy)
        print('Done deploying all servers.', flush=True)

    def shutdown(self):
        """Shuts down all processors.

        Returns:

        """
        print("Shutting down all processors")
        excs = []
        for p, listener in self._processor_listeners:
            try:
                p.terminate()
                listener.join(timeout=15.0)
                if listener.is_alive():
                    print(f'Unsuccessfully terminated processor {p.args}... killing.')
                    p.kill()
                    listener.join()
            except Exception as e:
                print(f"Failed to properly shutdown processor {p.args}")
                excs.append(e)

    def _start_subprocess(self,
                          call: List[str],
                          name: Any,
                          sid: str,
                          startup_timeout: float,
                          enable_proxy: bool = False) -> str:
        # starts process and listener, stores for later cleanup, returns address.
        p = subprocess.Popen(call, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        listener = threading.Thread(target=_listen, args=(p,))
        listener.start()
        self._processor_listeners.append((p, listener))  # Adding early so it gets cleaned up on failure
        address = None
        deadline = time.time() + startup_timeout
        while time.time() < deadline:
            try:
                address = utilities.read_address(sid)
                break
            except FileNotFoundError:
                time.sleep(1)
        if address is None:
            raise ServiceDeploymentException(f'Failed to launch, timed out waiting: {name}')
        with grpc.insecure_channel(address,
                                   options=[('grpc.enable_http_proxy', enable_proxy)]) as channel:
            future = grpc.channel_ready_future(channel)
            try:
                timeout = deadline - time.time()
                if timeout < 0:
                    raise ServiceDeploymentException(f'Failed to launch, timed out waiting: {name}')
                future.result(timeout=timeout)
            except grpc.FutureTimeoutError:
                raise ServiceDeploymentException(f'Failed to launch, unresponsive: {name}')
        return address


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
        example = pathlib.Path(__file__).parent / "examples" / "exampleDeploymentConfiguration.yml"
        shutil.copyfile(str(example), "exampleDeploymentConfiguration.yml")
        print('Writing "exampleDeploymentConfiguration.yml" to ' + str(pathlib.Path.cwd()))


def deployment_parser() -> argparse.ArgumentParser:
    """Creates a parser for configuration that can be passed to the deployment main method.

    Returns:
        ~argparse.ArgumentParser: The argument parser object that will create a namespace that can
        be passed to :func:`main`.

    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--log-level', metavar='LEVEL',
                        help="The log level to use for the deployment script.")
    subparsers = parser.add_subparsers(title='mode')

    run_servers = subparsers.add_parser('run_servers')
    run_servers.add_argument('deploy_config', metavar='CONFIG_FILE', type=pathlib.Path,
                             help="A path to the deployment configuration to deploy.")
    run_servers.set_defaults(mode='run_servers')

    write_example = subparsers.add_parser('write_example')
    write_example.set_defaults(mode='write_example')

    return parser


if __name__ == '__main__':
    main()
