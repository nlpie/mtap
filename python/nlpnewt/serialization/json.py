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
from pathlib import Path

from nlpnewt.events import Event
from nlpnewt.serialization.serializers import Serializer, serializer
from nlpnewt.serialization.shared import event_to_dict


@serializer('json')
class JsonSerializer(Serializer):
    def __init__(self):
        import json
        self.json = json

    @property
    def extension(self) -> str:
        return '.json'

    def event_to_file(self, event: Event, filepath: Path):
        d = event_to_dict(event)
        if isinstance(filepath, str):
            filepath = Path(filepath)
        with filepath.open('w') as f:
            self.json.dump(d, f)
