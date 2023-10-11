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
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from mtap._events_client import EventsAddressLike
from mtap.processing import ProcessingComponent, EventProcessor, LocalRunner, \
    RemoteRunner


DEFAULT_COMPONENT_ID = 'pipeline_component'


class ComponentDescriptor(ABC):
    """A configuration which describes either a local or remote pipeline
    component and what the pipeline needs to do to call the component.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def component_id(self) -> str:
        """How the processor's results will be identified locally.
        Will be modified to be unique if it is not unique relative to other
        components in the pipeline.
        """
        ...

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether the processor is enabled and should be run in the pipeline."""
        ...

    @abstractmethod
    def create_pipeline_component(
            self,
            events_address: EventsAddressLike
    ) -> ProcessingComponent:
        """Turns the descriptor into a component that can be used during processing."""
        pass


@dataclass
class LocalProcessor(ComponentDescriptor):
    """A configuration of a locally-invoked processor."""

    processor: EventProcessor
    """The processor instance to run with the pipeline."""

    component_id: str = DEFAULT_COMPONENT_ID
    """How the processor's results will be identified locally.
    Will be modified to be unique if it is not unique relative to other
    components in the pipeline.
    """

    params: Dict[str, Any] = field(default_factory=dict)
    """An optional parameter dictionary that will be passed to the
    processor as parameters with every event or document processed.
    Values should be json-serializable.
    """

    enabled: bool = True
    """Whether the processor is enabled and should be run in the pipeline."""

    def __post_init__(self):
        if self.component_id is DEFAULT_COMPONENT_ID:
            self.component_id = self.processor.metadata['name']

    def create_pipeline_component(
            self,
            events_address: EventsAddressLike
    ) -> ProcessingComponent:
        if not self.enabled:
            raise ValueError("Cannot create pipeline component for processor that is not enabled.")
        runner = LocalRunner(processor=self.processor,
                             events_address=events_address,
                             component_id=self.component_id,
                             params=copy.deepcopy(self.params))
        return runner


@dataclass
class RemoteProcessor(ComponentDescriptor):
    """A remote processor in a pipeline."""

    name: str
    """The processor service name used for health checking and discovery."""

    address: Optional[str] = None
    """Optionally an address to use, will use service discovery
    configuration to locate the processor if this is ``None`` or
    omitted.
    """

    component_id: str = DEFAULT_COMPONENT_ID
    """How the processor's results will be identified locally.
    Will be modified to be unique if it is not unique relative to other
    components in a pipeline.
    """

    params: Dict[str, Any] = field(default_factory=dict)
    """A parameter dictionary that will be passed to the
    processor as parameters with every event or document processed.
    Values should be json-serializable.
    """

    enable_proxy: bool = False
    """Whether the grpc channel used to connect to the service
    should respect the ``http_proxy`` environment variable.
    """

    enabled: bool = True
    """Whether the processor is enabled and should be run in the pipeline."""

    call_timeout: float = 10.0
    """A customizable timeout for calls to the remote processor."""

    def __post_init__(self):
        if self.component_id is DEFAULT_COMPONENT_ID:
            self.component_id = self.name

    def create_pipeline_component(
            self,
            events_address: EventsAddressLike
    ) -> ProcessingComponent:
        if not self.enabled:
            raise ValueError("Cannot create pipeline component for processor that is not enabled.")
        runner = RemoteRunner(processor_name=self.name,
                              component_id=self.component_id,
                              address=self.address,
                              params=copy.deepcopy(self.params),
                              enable_proxy=self.enable_proxy,
                              call_timeout=self.call_timeout)
        return runner
