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
"""Public API and access points for the nlpnewt Framework."""

from nlpnewt import constants
from nlpnewt import events
from nlpnewt import io
from nlpnewt import label_indices
from nlpnewt import labels
from nlpnewt import metrics
from nlpnewt import processing
from nlpnewt import processors
from nlpnewt import version
from nlpnewt._config import Config
from nlpnewt._events_service import EventsServer
from nlpnewt.events import Document
from nlpnewt.events import Event
from nlpnewt.events import EventsClient
from nlpnewt.events import proto_label_adapter
from nlpnewt.label_indices import label_index
from nlpnewt.labels import GenericLabel
from nlpnewt.labels import Location
from nlpnewt.processing import LocalProcessor
from nlpnewt.processing import Pipeline
from nlpnewt.processing import ProcessorServer
from nlpnewt.processing import RemoteProcessor
from nlpnewt.processing import processor
from nlpnewt.processing import processor_parser
from nlpnewt.processing import run_processor

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
