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

from pkg_resources import get_distribution, DistributionNotFound

from . import constants
from . import events
from . import labels
from . import label_indices
from . import processing
from ._config import Config
from ._events_service import EventsServer
from .events import Events
from .events import proto_label_adapter
from .labels import GenericLabel
from .labels import Location
from .label_indices import label_index
from .processing import Pipeline
from .processing import processor
from .processing import ProcessorServer

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = "development0"

__all__ = [
    '__version__',
    'constants',
    'events',
    'labels',
    'label_indices',
    'processing',
    'Config',
    'EventsServer',
    'Events',
    'proto_label_adapter',
    'GenericLabel',
    'Location',
    'label_index',
    'Pipeline',
    'processor',
    'ProcessorServer'
]
