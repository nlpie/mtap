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
from enum import Enum
from typing import NamedTuple


class LabelIndexType(Enum):
    """The type of serialized labels contained in the label index."""
    UNKNOWN = 0
    """Label index not set or type not known."""

    GENERIC = 1
    """JSON / Generic Label index"""

    CUSTOM = 2
    """Other / custom protobuf label index"""


LabelIndexType.UNKNOWN.__doc__ = """Label index not set or type not known."""
LabelIndexType.GENERIC.__doc__ = """JSON / Generic Label index"""
LabelIndexType.CUSTOM.__doc__ = """Other / custom protobuf label index"""


LabelIndexInfo = NamedTuple('LabelIndexInfo',
                            [('index_name', str),
                             ('type', LabelIndexType)])
LabelIndexInfo.__doc__ = """Information about a label index contained on a document."""
LabelIndexInfo.index_name.__doc__ = """str: The name of the label index."""
LabelIndexInfo.type.__doc__ = """LabelIndexType: The type of the label index."""
