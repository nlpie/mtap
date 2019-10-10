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

from mtap import constants
from mtap import events
from mtap import io
from mtap import label_indices
from mtap import labels
from mtap import metrics
from mtap import processing
from mtap import processors
from mtap import version
from mtap._config import Config
from mtap._events_service import EventsServer
from mtap.events import Document
from mtap.events import Event
from mtap.events import EventsClient
from mtap.events import proto_label_adapter
from mtap.label_indices import label_index
from mtap.labels import GenericLabel
from mtap.labels import Location
from mtap.processing import LocalProcessor
from mtap.processing import Pipeline
from mtap.processing import ProcessorServer
from mtap.processing import RemoteProcessor
from mtap.processing import processor
from mtap.processing import processor_parser
from mtap.processing import run_processor

__version__ = version.version

__all__ = [
    '__version__',
    'constants',
    'events',
    'labels',
    'metrics',
    'label_indices',
    'processing',
    'io',
    'Config',
    'EventsServer',
    'EventsClient',
    'Event',
    'Document',
    'proto_label_adapter',
    'GenericLabel',
    'Location',
    'label_index',
    'LocalProcessor',
    'RemoteProcessor',
    'label_index',
    'Pipeline',
    'processor',
    'processors',
    'processor_parser',
    'ProcessorServer',
    'run_processor'
]
