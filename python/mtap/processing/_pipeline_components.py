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
import typing
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from mtap.data import EventsAddressLike
from mtap.processing import _runners

if typing.TYPE_CHECKING:
    from mtap import EventProcessor, processing


class ComponentDescriptor(ABC):
    """A configuration which describes either a local or remote pipeline
    component and what the pipeline needs to do to call the component.
    """
    __slots__ = ()

    @property
    @abstractmethod
    def component_id(self) -> str:
        ...

    @abstractmethod
    def create_pipeline_component(
            self,
            events_address: EventsAddressLike
    ) -> 'processing.ProcessingComponent':
        pass


class LocalProcessor(ComponentDescriptor):
    """A configuration of a locally-invoked processor.

    Attributes:
        processor: The processor instance to run with the pipeline.
        component_id: How the processor's results will be identified locally.
            Will be modified to be unique if it is not unique relative to other
            components in the pipeline.
        params: An optional parameter dictionary that will be passed to the
            processor as parameters with every event or document processed.
            Values should be json-serializable.
    """
    __slots__ = ('processor', 'component_id', 'params')

    processor: 'EventProcessor'
    component_id: str
    params: Dict[str, Any]

    def __init__(self,
                 processor: 'EventProcessor',
                 *, component_id: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None):
        self.processor = processor
        self.component_id = component_id or self.processor.metadata['name']
        self.params = params or {}

    def __reduce__(self):
        params = (
            self.processor,
            self.component_id,
            self.params
        )
        return LocalProcessor, params

    def create_pipeline_component(
            self,
            events_address: EventsAddressLike
    ) -> 'processing.ProcessingComponent':
        runner = _runners.LocalRunner(processor=self.processor,
                                      events_address=events_address,
                                      component_id=self.component_id,
                                      params=copy.deepcopy(self.params))
        return runner

    def __repr__(self):
        return (f"LocalProcessor(proc={self.processor}, "
                f"component_id={self.component_id}, "
                f"params={self.params}")


class RemoteProcessor(ComponentDescriptor):
    """A remote processor in a pipeline.

    Attributes:
        processor_name: The identifier used for health checking and
            discovery.
        address: Optionally an address to use, will use service discovery
            configuration to locate the processor if this is ``None`` or
            omitted.
        component_id: How the processor's results will be identified locally.
            Will be modified to be unique if it is not unique relative to other
            components in a pipeline.
        params: A parameter dictionary that will be passed to the
            processor as parameters with every event or document processed.
            Values should be json-serializable.
        enable_proxy: Whether the grpc channel used to connect to the service
            should respect the ``http_proxy`` environment variable.
    """
    __slots__ = (
        'processor_name',
        'address',
        'component_id',
        'params',
        'enable_proxy'
    )

    processor_name: str
    address: Optional[str]
    component_id: str
    params: Dict[str, Any]
    enable_proxy: bool

    def __init__(self,
                 processor_name: str,
                 *, address: Optional[str] = None,
                 component_id: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None,
                 enable_proxy: bool = False):
        self.processor_name = processor_name
        self.address = address
        self.component_id = component_id or self.processor_name
        self.params = params or {}
        self.enable_proxy = enable_proxy

    def create_pipeline_component(
            self,
            events_address: EventsAddressLike
    ) -> 'processing.ProcessingComponent':
        runner = _runners.RemoteRunner(processor_name=self.processor_name,
                                       component_id=self.component_id,
                                       address=self.address,
                                       params=copy.deepcopy(self.params),
                                       enable_proxy=self.enable_proxy)
        return runner

    def __repr__(self):
        return (f"RemoteProcessor(processor_name={self.processor_name}, "
                f"address={self.address}, "
                f"component_id={self.component_id}, "
                f"params={self.params})")
