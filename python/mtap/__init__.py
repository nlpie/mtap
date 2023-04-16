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
"""Public API and access points for the MTAP Framework."""

from mtap._config import Config
from mtap._document import Document
from mtap._event import Event
from mtap._events_client import events_client
from mtap._labels import GenericLabel, label, Location
from mtap._label_indices import label_index

from mtap.processing import (
    DocumentProcessor,
    EventProcessor,
    processor_parser,
    run_processor
)

from mtap.descriptors import (
    processor
)

from mtap.pipeline import (
    Pipeline,
    LocalProcessor,
    RemoteProcessor,
)

from mtap.version import (
    __version__,
    __version_tuple__,
    version,
    version_tuple
)
