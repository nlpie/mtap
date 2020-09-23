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

from mtap import version
from mtap._config import Config
from mtap._events_service import EventsServer
from mtap.data import Document
from mtap.data import Event
from mtap.data import EventsClient
from mtap.data import GenericLabel
from mtap.data import label
from mtap.data import label_index
from mtap.data import Location
from mtap.processing import descriptions
from mtap.processing import DocumentProcessor
from mtap.processing import EventProcessor
from mtap.processing import processor_parser
from mtap.processing import LocalProcessor
from mtap.processing import Pipeline
from mtap.processing import ProcessorServer
from mtap.processing import RemoteProcessor
from mtap.processing import processor
from mtap.processing import run_processor

__version__ = version.version

__all__ = [s for s in dir()]
