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
import time
from datetime import timedelta
from typing import Dict, Any

from mtap import Pipeline, LocalProcessor, Event, EventsClient
from mtap.processing import EventProcessor


class Processor(EventProcessor):
    def __init__(self, identifier='1'):
        self.identifier = identifier

    def process(self, event: Event, params: Dict[str, Any]):
        if 'fail' in event.event_id:
            raise ValueError("fail")
        time.sleep(0.001)
        event.metadata[self.identifier] = 'True'


def test_time_result():
    processor = Processor()
    with Pipeline(
            LocalProcessor(processor, component_id='test_processor', client=None)
    ) as pipeline:
        event = Event()
        results = pipeline.run(event)
        result = results[0]
        assert result.timing_info['process_method'] >= timedelta(seconds=0.001)


def test_run_concurrently(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext']
    client.get_all_metadata.return_value = {}
    processor1 = Processor('1')
    processor2 = Processor('2')
    processor3 = Processor('3')
    with Pipeline(
            LocalProcessor(processor1, component_id='processor1', client=client),
            LocalProcessor(processor2, component_id='processor2', client=client),
            LocalProcessor(processor3, component_id='processor3', client=client)
    ) as pipeline:
        events = [Event() for _ in range(10)]
        results = pipeline.run_multithread(events, progress=False)
        for result in results:
            assert len(result) == 3


def test_run_concurrently_with_failure(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext']
    client.get_all_metadata.return_value = {}
    processor1 = Processor('1')
    processor2 = Processor('2')
    processor3 = Processor('3')
    with Pipeline(
            LocalProcessor(processor1, component_id='processor1', client=client),
            LocalProcessor(processor2, component_id='processor2', client=client),
            LocalProcessor(processor3, component_id='processor3', client=client)
    ) as pipeline:
        events = [Event(event_id=str(i), client=client) for i in range(7)] + [Event(event_id='fail_' + str(i), client=client) for i in range(4)]
        results = pipeline.run_multithread(events, progress=False, max_failures=2)
        assert len(results) == 7
        


