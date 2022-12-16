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
from mtap._events_service import EventsServer
from mtap.data import (
    Document,
    Event,
    EventsClient,
    GenericLabel,
    label,
    label_index,
    Location,
)
from mtap.processing import (
    DocumentProcessor,
    EventProcessor,
    LocalProcessor,
    Pipeline,
    ProcessorServer,
    RemoteProcessor,
    descriptions,
    processor,
    processor_parser,
    run_processor,
)
from mtap.version import *
