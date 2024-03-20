#  Copyright (c) Regents of the University of Minnesota.
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

import pickle
import time
from datetime import timedelta
from pathlib import Path
from typing import Dict, Any

from mtap import (
    Pipeline,
    EventProcessor,
    Event,
    processor,
    RemoteProcessor,
    LocalProcessor
)
from mtap._events_client import EventsClient
from mtap.pipeline import MpConfig, SimpleErrorHandler, \
    TerminationErrorHandler


@processor('test-processor')
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
        event.metadata['processor'] = self.identifier
        self.processed += 1


def test_time_result(mocker):
    client = mocker.Mock(EventsClient)
    client.get_all_document_names.return_value = ['plaintext']
    client.get_all_metadata.return_value = {}
    client.instance_id = 0
    pipeline = Pipeline(
        LocalProcessor(Processor(),
                       component_id='test_processor')
    )
    with pipeline.activate() as active:
        active.components[0]._client = client
        event = Event()
        result = active.run(event)
        assert result.component_results[0].timing_info['process_method'] \
               >= timedelta(seconds=0.001)


def test_load_from_config():
    pipeline = Pipeline.from_yaml_file(Path(__file__).parent / 'pipeline.yml')
    assert pipeline.name == 'mtap-test-pipeline'
    assert len(pipeline.error_handlers) == 2
    assert isinstance(pipeline.error_handlers[0], SimpleErrorHandler)
    assert isinstance(pipeline.error_handlers[1], TerminationErrorHandler)
    assert pipeline.error_handlers[1].max_failures == 3
    assert not pipeline.mp_config.show_progress
    assert pipeline.mp_config.workers == 12
    assert pipeline.mp_config.read_ahead == 4
    assert not pipeline.mp_config.close_events
    assert len(pipeline) == 2
    assert pipeline[0].name == 'processor-1'
    assert pipeline[0].address == 'localhost:1234'
    assert pipeline[1].name == 'processor-2'
    assert pipeline[1].address == 'localhost:5678'


def test_serialization():
    p = Pipeline(
        RemoteProcessor(
            name='processor-1',
            address='localhost:1234'
        ),
        RemoteProcessor(
            name='processor-2',
            address='localhost:5678'
        ),
        name='mtap-test-pipeline',
        mp_config=MpConfig(
            show_progress=False,
            workers=12,
            read_ahead=4,
            close_events=False
        ),
    )
    s = pickle.dumps(p)
    r = pickle.loads(s)
    assert r.name == 'mtap-test-pipeline'
    assert not r.mp_config.show_progress
    assert r.mp_config.workers == 12
    assert r.mp_config.read_ahead == 4
    assert not r.mp_config.close_events
    assert len(r) == 2
    assert r[0].name == 'processor-1'
    assert r[0].address == 'localhost:1234'
    assert r[1].name == 'processor-2'
    assert r[1].address == 'localhost:5678'
