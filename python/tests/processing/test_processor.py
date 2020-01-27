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
from datetime import timedelta

from mtap.processing.base import Processor


def test_stopwatch_no_fail_outside_context():
    blah = False
    with Processor.started_stopwatch('foo'):
        blah = True
    assert blah


def test_preserves_times():
    with Processor.enter_context() as context:
        context.add_time("foo", timedelta(seconds=2))
        context.add_time("foo", timedelta(seconds=2))
        assert context.times["foo"] == timedelta(seconds=4)
