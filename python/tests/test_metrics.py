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

from mtap import Event
from mtap.metrics import Accuracy, Metrics, BeginTokenBinaryClassification


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


def test_any():
    with Event(event_id='1') as event:
        doc = event.create_document('test', 'This is some text.')
        with doc.get_labeler('tested') as tested:
            tested(0, 5, x=1)
            tested(0, 5, x=3)
        with doc.get_labeler('target') as target:
            target(0, 5, x=1)
            target(6, 10, x=2)

        acc = Accuracy(mode='any')
        metrics = Metrics(acc, tested='tested', target='target')
        metrics.process_document(doc, params={})
        assert abs(acc.value - 0.5) < 1e-6


def test_fields():
    with Event(event_id='1') as event:
        doc = event.create_document('test', 'This is some text.')
        with doc.get_labeler('tested') as tested:
            tested(0, 5, x=1, y=3)
            tested(6, 10, x=3, y=4)
        with doc.get_labeler('target') as target:
            target(0, 5, x=1, y=5)
            target(6, 10, x=2, y=6)

        acc = Accuracy(fields=['x'])
        metrics = Metrics(acc, tested='tested', target='target')
        metrics.process_document(doc, params={})
        assert abs(acc.value - 0.5) < 1e-6


def test_boundary_fuzz_equals():
    with Event(event_id='1') as event:
        doc = event.create_document('test', 'This is some text.')
        with doc.get_labeler('tested') as tested:
            tested(0, 5)
            tested(6, 10)
            tested(11, 20)
            tested(21, 29)
            tested(31, 39)

        with doc.get_labeler('target') as target:
            target(0, 6)
            target(7, 10)
            target(11, 19)
            target(20, 30)
            target(49, 50)

        acc = Accuracy(boundary_fuzz=1)
        metrics = Metrics(acc, tested='tested', target='target')
        metrics.process_document(doc, params={})
        assert abs(acc.value - 0.8) < 1e-6


def test_begin_token_precision_recall_f1():
    with Event() as event:
        doc = event.create_document('test', 'The quick brown fox jumps over the lazy dog.')
        with doc.get_labeler('tested') as label_tested:
            label_tested(0, 9)
            label_tested(10, 19)
            label_tested(20, 44)
        with doc.get_labeler('target') as label_target:
            label_target(0, 19)
            label_target(20, 30)
            label_target(31, 44)

        metric = BeginTokenBinaryClassification()
        metric.update(doc, doc.get_label_index('tested'), doc.get_label_index('target'))
        assert metric.precision == 2 / 3
        assert metric.recall == 2 / 3
        assert metric.f1 == 2 / 3

