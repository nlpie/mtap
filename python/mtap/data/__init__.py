#  Copyright 2020 Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""Module for MTAP's Data Model

Attributes:
    GENERIC_ADAPTER (~mtap.data.ProtoLabelAdapter): label adapter used for standard
        (non-distinct) :obj:`~mtap.GenericLabel`.
    DISTINCT_GENERIC_ADAPTER (~mtap.data.ProtoLabelAdapter): label adapter used for distinct
        (non-overlapping) :obj:`~mtap.GenericLabel`.
"""

from mtap.data._events import Document
from mtap.data._events import Event
from mtap.data._events import EventsClient
from mtap.data._events import Labeler
from mtap.data._base import LabelIndexType, LabelIndexInfo
from mtap.data._label_adapters import GENERIC_ADAPTER
from mtap.data._label_adapters import DISTINCT_GENERIC_ADAPTER
from mtap.data._label_adapters import ProtoLabelAdapter
from mtap.data._label_indices import label_index
from mtap.data._label_indices import presorted_label_index
from mtap.data._label_indices import LabelIndex
from mtap.data._labels import GenericLabel
from mtap.data._labels import Label
from mtap.data._labels import label
from mtap.data._labels import Location
