# Copyright 2023 Regents of the University of Minnesota.
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
import copy
import multiprocessing
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from mtap._events_client import EventsAddressLike
from mtap.pipeline._remote_runner import RemoteProcessorRunner
from mtap.processing import ProcessorOptions, serve_forever, EventProcessor
from mtap.processing._service import subprocess_run_processor
from mtap.utilities import find_free_port


class RemoteProcessor:
    """A remote processor in a pipeline."""

    name: str
    """The processor service name used for health checking and discovery."""

    address: Optional[str]
    """Optionally an address to use, will use service discovery
    configuration to locate the processor if this is ``None`` or
    omitted.
    """

    component_id: str
    """How the processor's results will be identified locally.
    Will be modified to be unique if it is not unique relative to other
    components in a pipeline.
    """

    params: Dict[str, Any]
    """A parameter dictionary that will be passed to the
    processor as parameters with every event or document processed.
    Values should be json-serializable.
    """

    enable_proxy: bool
    """Whether the grpc channel used to connect to the service
    should respect the ``http_proxy`` environment variable.
    """

    enabled: bool
    """Whether the processor is enabled and should be run in the pipeline."""

    def __init__(self,
                 name: str,
                 address: Optional[str] = None,
                 component_id: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None,
                 enable_proxy: bool = False,
                 enabled: bool = True):
        self.name = name
        self.address = address
        self.component_id = self.name if component_id is None else component_id
        self.params = {} if params is None else params
        self.enable_proxy = enable_proxy
        self.enabled = enabled

    @asynccontextmanager
    async def create_runner(self, events_address: EventsAddressLike, workers: int) -> RemoteProcessorRunner:
        if not self.enabled:
            raise ValueError("Cannot create pipeline component for processor that is not enabled.")
        with RemoteProcessorRunner(
                processor_name=self.name, component_id=self.component_id, address=self.address,
                params=copy.deepcopy(self.params), enable_proxy=self.enable_proxy) as runner:
            yield runner

    def __repr__(self):
        return f'RemoteProcessor(name={self.name}, address={self.address}, component_id={self.component_id}, ' \
               f'params={self.params}, enable_proxy={self.enable_proxy}, enabled={self.enabled})'


class LocalProcessor(RemoteProcessor):
    """A configuration of a locally-invoked processor."""

    processor: EventProcessor
    """The processor instance to run with the pipeline."""

    mp_context: multiprocessing
    """A multiprocessing context to use to run the processor on subprocesses."""

    workers: Optional[int]
    """The number of subprocesses to spin up for the processor to do work."""

    def __init__(self,
                 processor: EventProcessor,
                 component_id: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None,
                 enable_proxy: bool = False,
                 enabled: bool = True,
                 mp_context: multiprocessing = None,
                 workers: int = None):
        super().__init__(
            name=processor.metadata['name'], component_id=component_id, params=params,
            enable_proxy=enable_proxy, enabled=enabled)
        self.processor = processor
        self.mp_context = mp_context
        self.workers = workers

    @asynccontextmanager
    async def create_runner(self,
                            events_address: EventsAddressLike,
                            workers: int) -> RemoteProcessorRunner:
        if not self.enabled:
            raise ValueError("Cannot create pipeline component for processor that is not enabled.")
        if self.workers:
            workers = self.workers
        host = '127.0.0.1'
        port = find_free_port()
        self.address = f'{host}:{port}'
        opts = ProcessorOptions(
            host=host, port=port, workers=workers, events_addresses=events_address,
            name=self.component_id
        )

        async with subprocess_run_processor(self.processor, opts), \
                super().create_runner(events_address, workers) as runner:
            yield runner
