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
from datetime import timedelta
from typing import Dict, Any

import time

from mtap import Pipeline, LocalProcessor, Event
from mtap.processing import EventProcessor


class Processor(EventProcessor):
    def process(self, event: Event, params: Dict[str, Any]):
        time.sleep(0.001)


def test_time_result():
    processor = Processor()
    with Pipeline(
        LocalProcessor(processor, component_id='test_processor', client=None)
    ) as pipeline:
        event = Event()
        results = pipeline.run(event)
        result = results[0]
        assert result.timing_info['process_method'] >= timedelta(seconds=0.001)
