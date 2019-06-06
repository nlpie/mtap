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
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from nlpnewt.events import Document
from nlpnewt.label_indices import LabelIndex
from nlpnewt.processing import DocumentProcessor, processor


class Metric(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def update(self, tested_index: LabelIndex, target_index: LabelIndex) -> Any:
        ...


@processor('newt-metrics')
class Metrics(DocumentProcessor):
    def __init__(self, *metrics: Metric, tested: str, target: str):
        self.tested = tested
        self.target = target
        self.metrics = metrics

    def process(self, document: Document, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tested = document.get_label_index(self.tested)
        target = document.get_label_index(self.target)
        local = {}
        for metric in self.metrics:
            local[metric.name] = metric.update(tested, target)
        return local


class Accuracy(Metric):
    def __init__(self):
        self.correct = 0
        self.total = 0

    @property
    def name(self) -> str:
        return 'accuracy'

    def update(self, tested_index: LabelIndex, target_index: LabelIndex) -> Any:
        correct = 0
        total = 0
        for target_label in target_index:
            total += 1
            if target_label in tested_index:
                correct += 1
        self.correct += correct
        self.total += total
        return correct / total

    def value(self):
        return self.correct / self.total
