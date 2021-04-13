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
#
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
"""Module for deploying a set of processing services and the events server all at once.

Examples:

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
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import grpc

from mtap import utilities, _config

__all__ = [
    'Deployment', 'GlobalSettings', 'SharedProcessorConfig', 'EventsDeployment',
    'ProcessorDeployment', 'main', 'deployment_parser', 'ServiceDeploymentException',
]

logger = logging.getLogger(__name__)

PYTHON_EXE = sys.executable


def _get_java() -> str:
    try:
        return pathlib.Path(os.environ['JAVA_HOME']) / 'bin' / 'java'
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
        host (Optional[str]): The global host, by default will use "127.0.0.1".
        mtap_config (Optional[str]): The path to an MTAP config file to load for all services.
        log_level (Optional[str]): A python logging level to pass to all services.
        register (Optional[str]): Whether services should register with service discovery.

    Attributes:
        host (Optional[str]): The global host, by default will use "127.0.0.1".
        mtap_config (Optional[str]): The path to an MTAP config file to load for all services.
        log_level (Optional[str]): A python logging level to pass to all services.
        register (Optional[str]): Whether services should register with service discovery.

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
            conf (Optional[Dict]): The configuration dictionary.

        Returns:
            GlobalSettings: The global settings object.

        """
        conf = conf or {}
        return GlobalSettings(host=conf.get('host'), mtap_config=conf.get('mtapConfig'),
                              log_level=conf.get('logLevel'), register=conf.get('register'))


class SharedProcessorConfig:
    """Configuration that is shared between multiple processor services.

    Keyword Args:
        events_address (Optional[str]): An optional GRPC-compatible target for the events
            service to be used by all processors.
        workers (Optional[int]): The default number of worker threads which will perform
            processing.
        additional_args (Optional[List[str]]): a list of additional arguments that
            should be appended to every processor.
        jvm_args (Optional[List[str]]): a list of JVM arguments for all java
            processors.
        classpath (Optional[str]): A classpath string that will be passed to all java
            processors.
        startup_timeout (Optional[int]): The default startup timeout for processors.

    Attributes:
        events_address (Optional[str]): An optional GRPC-compatible target for the events
            service to be used by all processors.
        workers (Optional[int]): The default number of worker threads which will perform
            processing.
        additional_args (Optional[List[str]]): a list of additional arguments that
            should be appended to every processor.
        jvm_args (Optional[List[str]]): a list of JVM arguments for all java
            processors.
        classpath (Optional[str]): A classpath string that will be passed to all java
            processors.
        startup_timeout (Optional[int]): The default startup timeout for processors.

    """

    def __init__(self,
                 events_address: Optional[str] = None,
                 workers: Optional[int] = None,
                 additional_args: Optional[List[str]] = None,
                 jvm_args: Optional[List[str]] = None,
                 classpath: Optional[str] = None,
                 startup_timeout: Optional[int] = None):
        self.events_address = events_address
        self.workers = workers
        self.additional_args = additional_args
        self.jvm_args = jvm_args
        self.classpath = classpath
        self.startup_timeout = startup_timeout or 30

    @staticmethod
    def from_conf(conf: Optional[Dict]) -> 'SharedProcessorConfig':
        """Builds a configuration from a dictionary representation.

        Args:
            conf (Optional[Dict]): The configuration dictionary.

        Returns:
            SharedProcessorConfig object.

        """
        conf = conf or {}
        return SharedProcessorConfig(events_address=conf.get('eventsAddress'),
                                     workers=conf.get('workers'),
                                     additional_args=conf.get('args'),
                                     jvm_args=conf.get('jvmArgs'),
                                     classpath=conf.get('javaClasspath'),
                                     startup_timeout=conf.get('startupTimeout'))


class _ServiceDeployment:
    def __init__(self,
                 host: Optional[str],
                 workers: Optional[int],
                 register: Optional[bool],
                 mtap_config: Optional[str],
                 log_level: Optional[str]):
        self.host = host
        self.workers = workers
        self.register = register
        self.mtap_config = mtap_config
        self.log_level = log_level

    def service_args(self,
                     port: Optional[int],
                     register_default: Optional[bool] = None,
                     host_default: Optional[str] = None,
                     workers_default: Optional[int] = None,
                     mtap_config_default: Optional[str] = None,
                     log_level_default: Optional[str] = None):
        call = []

        host = self.host or host_default
        if host is not None:
            call.extend(['--host', str(host)])

        if port is not None:
            call.extend(['--port', str(port)])

        if self.register or register_default:
            call.append('--register')

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
        return call


class EventsDeployment:
    """Deployment configuration for the events service.

    Keyword Args:
        enabled (bool): Whether an events service should be created.
        host (~typing.Optional[str]): The host address of the events service.
        port (~typing.Optional[int]): Which port to host on.
        workers (~typing.Optional[int]): The number of worker threads the events service should use.
        register (~typing.Optional[bool]): Whether to register the events service with discovery.
        mtap_config (~typing.Optional[str]): Path to an mtap configuration file.
        log_level (~typing.Optional[str]): The log level for the events service.

    """

    def __init__(self, *,
                 enabled: bool = True,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 workers: Optional[int] = None,
                 register: Optional[bool] = None,
                 mtap_config: Optional[str] = None,
                 log_level: Optional[str] = None):
        self.enabled = enabled
        self.port = port
        self.service_deployment = _ServiceDeployment(host, workers, register, mtap_config,
                                                     log_level)

    def create_call(self, global_settings: GlobalSettings) -> List[str]:
        call = [PYTHON_EXE, '-m', 'mtap', 'events']
        service_args = self.service_deployment.service_args(
            port=self.port,
            register_default=global_settings.register,
            host_default=global_settings.host,
            mtap_config_default=global_settings.mtap_config,
            log_level_default=global_settings.log_level
        )
        call.extend(service_args)
        return call

    @staticmethod
    def from_conf(conf: Optional[Dict]) -> 'EventsDeployment':
        """Creates the EventsDeployment configuration option from a configuration dictionary.

        Args:
            conf (Optional[Dict]): The configuration dictionary

        Returns:
            EventsDeployment or None from the configuration dictionary.

        """
        conf = conf or {}

        enabled = conf.get('enabled')
        if enabled is None:
            enabled = False

        return EventsDeployment(enabled=enabled, host=conf.get('host'), port=conf.get('port'),
                                workers=conf.get('workers'), register=conf.get('register'),
                                mtap_config=conf.get('mtapConfig'))


class ProcessorDeployment:
    """Deployment configuration for an MTAP processor.

    Used to construct the command for launching the processor. The processor should be a Java Class
    with a main method or a Python module with a main block. It should accept the standard MTAP
    processor deployment arguments and launch an MTAP processor using :func:`mtap.run_processor` or
    the equivalent Java method.

    Args:
        implementation (str): Either "java" or "python".
        entry_point (str): Either the java main class, or the python main module.
        enabled (bool): Whether the processor should be launched as part of deployment.
        instances (int): The number of instances of the processor to launch.
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
        startup_timeout (Optional[int]): Optional override startup timeout.

    """

    def __init__(self,
                 implementation: str,
                 entry_point: str,
                 *, enabled: bool = True,
                 instances: int = 1,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 workers: Optional[int] = None,
                 register: Optional[bool] = None,
                 mtap_config: Optional[str] = None,
                 log_level: Optional[str] = None,
                 identifier: Optional[str] = None,
                 pre_args: Optional[List[str]] = None,
                 additional_args: Optional[List[str]] = None,
                 startup_timeout: Optional[int] = None):
        self.enabled = enabled
        self.implementation = implementation
        self.entry_point = entry_point
        self.instances = instances or 1
        self.identifier = identifier
        self.pre_args = pre_args
        self.additional_args = additional_args
        self.port = port
        self.service_deployment = _ServiceDeployment(host, workers, register, mtap_config,
                                                     log_level)
        self.startup_timeout = startup_timeout

    @staticmethod
    def from_conf(conf: Dict) -> 'ProcessorDeployment':
        """Creates an MTAP processor deployment configuration from a configuration dictionary.

        Args:
            conf (Dict): The configuration dictionary.

        Returns:
            ProcessorDeployment object that can be used to constuct the call for the processor.

        """
        return ProcessorDeployment(implementation=conf['implementation'],
                                   entry_point=conf['entryPoint'],
                                   enabled=conf.get('enabled', True),
                                   instances=conf.get('instances', 1),
                                   host=conf.get('host'),
                                   port=conf.get('port'),
                                   workers=conf.get('workers'),
                                   register=conf.get('register'),
                                   mtap_config=conf.get('mtapConfig'),
                                   log_level=conf.get('logLevel'),
                                   identifier=conf.get('identifier'),
                                   pre_args=conf.get('preArgs'),
                                   additional_args=conf.get('args'),
                                   startup_timeout=conf.get('startupTimeout'))

    def create_calls(self,
                     global_settings: GlobalSettings,
                     shared_config: SharedProcessorConfig) -> Iterable[List[str]]:
        if isinstance(self.port, list):
            ports = self.port
        elif self.port is None:
            ports = [None] * self.instances
        else:
            ports = list(range(self.port, self.port + self.instances))
        for port in ports:
            if self.implementation == 'python':
                call = [PYTHON_EXE, '-m', self.entry_point]
            elif self.implementation == 'java':
                call = [str(JAVA_EXE)]
                if shared_config.jvm_args is not None:
                    call.extend(shared_config.jvm_args)
                if shared_config.classpath is not None:
                    call.extend(['-cp', shared_config.classpath])
                call.append(self.entry_point)
            else:
                raise ValueError('Unrecognized implementation: ' + self.implementation)

            if self.pre_args is not None:
                call.extend(self.pre_args)

            service_args = self.service_deployment.service_args(
                port=port,
                register_default=global_settings.register,
                host_default=global_settings.host,
                mtap_config_default=global_settings.mtap_config,
                log_level_default=global_settings.log_level,
                workers_default=shared_config.workers
            )
            call.extend(service_args)

            if self.identifier is not None:
                call.extend(['--identifier', self.identifier])

            events_address = shared_config.events_address
            if events_address is not None:
                call.extend(['--events', events_address])

            if self.additional_args is not None:
                call.extend(self.additional_args)

            if shared_config.additional_args is not None:
                call.extend(shared_config.additional_args)

            yield call


class Deployment:
    """A automatic deployment configuration which launches a configurable set of MTAP services.

    Args:
         global_settings (~typing.Optional[GlobalSettings]): Settings shared among all services.
         events_deployment (~typing.Optional[EventsDeployment]):
            Deployment settings for the events service.
         shared_processor_config (~typing.Optional[SharedProcessorConfig]):
            Shared configuration settings for all processors.
         processors (vararg ProcessorDeployment): Configurations for individual processors.

    """

    def __init__(self,
                 global_settings: Optional[GlobalSettings] = None,
                 events_deployment: Optional[EventsDeployment] = None,
                 shared_processor_config: Optional[SharedProcessorConfig] = None,
                 *processors: ProcessorDeployment):
        self.global_settings = global_settings
        self.events_deployment = events_deployment
        self.shared_processor_config = shared_processor_config
        self.processors = processors

    @staticmethod
    def load_configuration(conf: Dict) -> 'Deployment':
        """Creates a deployment object from a configuration dictionary.

        Args:
            conf (Dict): The configuration dictionary.

        Returns:
            Deployment object created.

        """
        global_settings = GlobalSettings.from_conf(conf.get('global'))
        events = EventsDeployment.from_conf(conf.get('eventsService'))
        shared_processor_config = SharedProcessorConfig.from_conf(conf.get('sharedProcessorConfig'))
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

    def run_servers(self):
        """Starts all of the configured services.

        Raises:
            ServiceDeploymentException: If one of the services fails to launch.

        """
        with _config.Config() as c:
            enable_proxy = c.get('grpc.enable_proxy', False)
            events_address = None
            processes_listeners = []
            if self.events_deployment.enabled:
                call = self.events_deployment.create_call(self.global_settings)
                p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                listener, events_address = _listen_test_connectivity(p, "events", 30, enable_proxy)
                processes_listeners.append((p, listener))

            if (not self.global_settings.register
                    and not self.events_deployment.service_deployment.register
                    and self.shared_processor_config.events_address is None):
                self.shared_processor_config.events_address = events_address

            for processor_deployment in self.processors:
                if processor_deployment.enabled:
                    for call in processor_deployment.create_calls(self.global_settings,
                                                                  self.shared_processor_config):
                        logger.debug('Launching processor with call: %s', call)
                        p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        startup_timeout = (processor_deployment.startup_timeout
                                           or self.shared_processor_config.startup_timeout)
                        listener, _ = _listen_test_connectivity(p, call, startup_timeout,
                                                                enable_proxy)
                        processes_listeners.append((p, listener))

            print('Done deploying all servers.', flush=True)
            try:
                while True:
                    time.sleep(60 * 60 * 24)
            except KeyboardInterrupt:
                print("Shutting down all processors")
                for p, listener in processes_listeners:
                    listener.join(timeout=1)


def _listen_test_connectivity(p: subprocess.Popen,
                              name: Any,
                              startup_timeout: int,
                              enable_proxy: bool = False) -> Tuple[threading.Thread, str]:
    listener = threading.Thread(target=_listen, args=(p,))
    listener.start()
    address = None
    for i in range(startup_timeout):
        try:
            address = utilities.read_address(str(p.pid))
            break
        except FileNotFoundError:
            time.sleep(1)
    if address is None:
        raise ServiceDeploymentException('Timed out waiting for {} to launch'.format(name))
    with grpc.insecure_channel(address,
                               options=[('grpc.enable_http_proxy', enable_proxy)]) as channel:
        future = grpc.channel_ready_future(channel)
        try:
            future.result(timeout=startup_timeout)
        except grpc.FutureTimeoutError:
            raise ServiceDeploymentException('Failed to launch: {}'.format(name))
    return listener, address


def main(args: Optional[Sequence[str]] = None,
         conf: Optional[argparse.Namespace] = None):
    if conf is None:
        conf = deployment_parser().parse_args(args)
    if conf.log_level is not None:
        logging.basicConfig(level=getattr(logging, conf.log_level))
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
