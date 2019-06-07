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
    name = None

    @abstractmethod
    def update(self, document: Document, tested_index: LabelIndex, target_index: LabelIndex) -> Any:
        ...


@processor('newt-metrics')
class Metrics(DocumentProcessor):
    def __init__(self, *metrics: Metric, tested: str, target: str):
        self.tested = tested
        self.target = target
        self.metrics = metrics

    def process_document(self, document: Document,
                         params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tested = document.get_label_index(self.tested)
        target = document.get_label_index(self.target)
        local = {}
        for metric in self.metrics:
            local[metric.name] = metric.update(document, tested, target)
        return local


class Accuracy(Metric):
    def __init__(self, name: str = 'accuracy', mode: str = 'equals', print_debug: bool = False):
        self.correct = 0
        self.total = 0
        self.name = name
        self.mode = mode
        self.print_debug = print_debug

    @property
    def value(self) -> float:
        return self.correct / self.total

    def update(self, document: Document, tested_index: LabelIndex, target_index: LabelIndex) -> Any:
        correct = 0
        total = 0
        for target_label in target_index:
            total += 1
            if self.mode == 'equals':
                if target_label in tested_index:
                    correct += 1
                elif self.print_debug:
                    print('Not found:', target_label)
                    print('"', target_label.get_covered_text(document.text), '"')
                    overlapping = tested_index.overlapping(target_label)
                    print('Overlapping:', overlapping)
                    for overlap in overlapping:
                        print('"', overlap.get_covered_text(document.text), '"')
            if self.mode == 'location':
                if len(tested_index.at(target_label)) > 0:
                    correct += 1
                elif self.print_debug:
                    print('Not found:', target_label)
                    print('"', target_label.get_covered_text(document.text), '"')
                    overlapping = tested_index.overlapping(target_label)
                    print('Overlapping:', overlapping)
                    for overlap in overlapping:
                        print('"', overlap.get_covered_text(document.text), '"')
        self.correct += correct
        self.total += total
        return correct / total if total != 0 else 1.

