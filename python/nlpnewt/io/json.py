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
"""Serializer for JSON."""
import io
from pathlib import Path
from typing import Union, Optional

from nlpnewt.events import Event, EventsClient
from nlpnewt.io.serialization import Serializer, serializer, event_to_dict, dict_to_event


@serializer('json')
class JsonSerializer(Serializer):
    """Serializer implementation that performs serialization to JSON.
    """

    def __init__(self):
        import json
        self.json = json

    @property
    def extension(self) -> str:
        return '.json'

    def event_to_file(self, event: Event, f: Path):
        d = event_to_dict(event)
        try:
            self.json.dump(d, f)
        except AttributeError:
            f = Path(f)
            f.parent.mkdir(parents=True, exist_ok=True)
            with f.open('w') as f:
                self.json.dump(d, f)

    def file_to_event(self, f: Union[Path, str, io.IOBase],
                      client: Optional[EventsClient] = None) -> Event:
        try:
            d = self.json.load(f)
        except AttributeError:
            if isinstance(f, str):
                f = Path(f)
            with f.open('r') as f:
                d = self.json.load(f)
        return dict_to_event(d, client=client)
