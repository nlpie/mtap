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
from typing import Union, Optional, Dict, Any

from mtap._document import Document
from mtap._event import Event

EventLike = Union[Event, Document]


def event_and_params(target: EventLike, params: Optional[Dict[str, Any]]):
    try:
        document_name = target.document_name
        params = {} if params is None else dict(params)
        params['document_name'] = document_name
        event = target.event
    except AttributeError:
        event = target
    return event, params
