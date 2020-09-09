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
from typing import Dict, Any, Callable, Union

import pytest

from mtap import Pipeline, LocalProcessor, Event, EventsClient, Document
from mtap.processing import EventProcessor
from mtap.processing._runners import ProcessingError
from mtap.processing.pipeline import ProcessingSource, PipelineResult


class Processor(EventProcessor):
    def __init__(self, identifier='1'):
        self.identifier = identifier
        self.seen = 0
        self.processed = 0

    def process(self, event: Event, params: Dict[str, Any]):
        self.seen += 1
        if 'fail' in event.event_id:
            raise ValueError("fail")
        time.sleep(0.001)
        event.metadata[self.identifier] = 'True'
        self.processed += 1


def test_time_result():
    processor = Processor()
    with Pipeline(
            LocalProcessor(processor, component_id='test_processor', client=None)
    ) as pipeline:
        event = Event()
        result = pipeline.run(event)
        assert result.component_results[0].timing_info['process_method'] >= timedelta(seconds=0.001)


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
        pipeline.run_multithread(events, progress=False)

        for processor in (processor1, processor2, processor3):
            assert processor.processed == 10


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
        pipeline.run_multithread(events, progress=False, max_failures=2)

        for processor in (processor1, processor2, processor3):
            assert processor.processed == 7


class Source(ProcessingSource):
    def __init__(self, events):
        self.events = events
        self.processed = 0
        self.failures = 0

    def provide(self, consume: Callable[[Union[Document, Event]], None]):
        for event in self.events:
            consume(event)

    def receive_result(self, result: PipelineResult, event: Event):
        self.processed += 1

    def receive_failure(self, exc: ProcessingError):
        self.failures += 1


def test_run_concurrently_source(mocker):
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
        source = Source([Event() for _ in range(10)])
        pipeline.run_multithread(source, progress=False)

        for processor in (processor1, processor2, processor3):
            assert processor.processed == 10
        assert source.processed == 10


def test_run_concurrently_with_failure_source(mocker):
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
        source = Source([Event(event_id=str(i), client=client) for i in range(7)] + [Event(event_id='fail_' + str(i), client=client) for i in range(4)])
        with pytest.raises(ValueError) as e_info:
            pipeline.run_multithread(source, progress=False, max_failures=2)
        assert str(e_info.value) == 'Max processing failures exceeded.'

        for processor in (processor1, processor2, processor3):
            assert processor.processed == 7
        assert source.processed == 7
        assert source.failures >= 3
