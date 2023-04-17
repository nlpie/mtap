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
from dataclasses import dataclass, field
from typing import Dict, Optional, TYPE_CHECKING, Any

if TYPE_CHECKING:
    import multiprocessing


@dataclass
class MpConfig:
    """Configuration object for pipeline multiprocessing.
    """
    show_progress: bool = False
    """Whether progress should be displayed in the console."""

    params: Dict[str, Any] = field(default_factory=dict)

    workers: int = 10
    """Number of workers to concurrently process events through the
    pipeline."""

    read_ahead: int = 10
    """The number of documents to read onto the events service(s) to
    queue for processing."""

    close_events: bool = False
    """Whether any events passed from the source to the pipeline should
    be closed when the pipeline is completed."""

    log_level: str = 'INFO'
    """"""

    mp_start_method: str = "spawn"
    """The start method for multiprocessing processes see:
    :meth:`multiprocessing.get_context`."""

    mp_context: Optional['multiprocessing'] = None
    """An optional mp_context. If set overrides the ``mp_start_method``
    attribute. If not set will use
    ``multiprocessing.get_context(mp_start_method)``
    to create the context.
    """

    @staticmethod
    def from_configuration(conf: Dict) -> 'MpConfig':
        return MpConfig(**conf)
