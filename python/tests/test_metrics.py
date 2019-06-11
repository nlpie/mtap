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

from nlpnewt import Event
from nlpnewt.metrics import Accuracy, Metrics


def test_accuracy():
    with Event(event_id='1') as event:
        doc = event.create_document('test', 'This is some text.')
        with doc.get_labeler('tested') as tested:
            tested(0, 5)
            tested(6, 10)
            tested(11, 20)
            tested(21, 29)
            tested(31, 39)

        with doc.get_labeler('target') as target:
            target(0, 5)
            target(6, 10)
            target(11, 20)
            target(21, 30)
            target(31, 39)

        acc = Accuracy()
        metrics = Metrics(acc, tested='tested', target='target')
        metrics.process_document(doc, params={})
        assert abs(acc.value - 0.8) < 1e-6
