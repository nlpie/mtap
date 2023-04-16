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
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Dict, Any, Tuple


class ProcessingComponent(ABC):
    __slots__ = ()

    metadata = {}

    @property
    @abstractmethod
    def processor_name(self) -> str:
        ...

    @property
    @abstractmethod
    def component_id(self) -> str:
        ...

    @abstractmethod
    def call_process(
            self,
            event_id: str,
            event_instance_id: str,
            params: Optional[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, timedelta], Dict[str, list[str]]]:
        """Calls a processor.

        Parameters
            event_id: The event to process.
            event_instance_id: The service instance the event is stored on.
            params: The processor parameters.

        Returns
            A tuple of the processing result dictionary, the processor times
            dictionary, and the "created indices" dictionary.
        """
        ...

    def close(self):
        pass
