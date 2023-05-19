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
from time import sleep

from datetime import timedelta
from typing import Dict, Any

from mtap import Event, EventProcessor


def test_started_stopwatch():
    class TestProcessor(EventProcessor):
        def process(self, event: Event, params: Dict[str, Any]):
            with self.started_stopwatch('foo') as stopwatch:
                sleep(1 / 1000)
            return stopwatch._duration

    pr = TestProcessor()
    assert pr.process(None, None) >= timedelta(milliseconds=1)


def test_not_started_stopwatch():
    class TestProcessor(EventProcessor):
        def process(self, event: Event, params: Dict[str, Any]):
            with self.unstarted_stopwatch('foo') as stopwatch:
                for _ in range(20):
                    stopwatch.start()
                    sleep(1 / 1000)
                    stopwatch.stop()
            return stopwatch._duration

    pr = TestProcessor()
    assert pr.process(None, None) >= timedelta(milliseconds=20)
