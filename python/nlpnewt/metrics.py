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
"""Provides functionality for measuring processor performance against gold standards."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Sequence, Iterable

from nlpnewt.events import Document
from nlpnewt.label_indices import LabelIndex
from nlpnewt.labels import Label
from nlpnewt.processing import DocumentProcessor, processor


class Metric(ABC):
    """Base class for metrics.

    """
    name = None

    @abstractmethod
    def update(self, document: Document, tested_index: LabelIndex, target_index: LabelIndex) -> Any:
        ...


@processor('newt-metrics')
class Metrics(DocumentProcessor):
    """A document process that computes a set of metrics.

    Attributes
    ----------
    tested: str
        The tested index.
    target: str
        The target / gold standard index.

    """

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


def print_overlapping(document, target_label, tested_index):
    print('Not found:', target_label)
    print('"', target_label.get_covered_text(document.text), '"')
    overlapping = tested_index.overlapping(target_label)
    print('Overlapping:', overlapping)
    for overlap in overlapping:
        print('"', overlap.get_covered_text(document.text), '"')


class Accuracy(Metric):
    def __init__(self,
                 name: str = 'accuracy',
                 mode: str = 'equals',
                 print_debug: bool = False,
                 boundary_fuzz: int = 0,
                 fields: Optional[Sequence[str]] = ...):
        """An accuracy metric with several options for equivalence.

        Parameters
        ----------
        name: str
            An identifier for the metric.
        mode: str
            'equals' - counts as a hit if there is one and only one label at the same location in
            the tested index as the target index and it has the same values for its fields
            'location' - counts as a hit if there is one and only one label at the same location in
            the tested index as the target index.
            'any' - counts as a hit if there is one or more labels at the same location with the
            same values for its fields.
        print_debug: bool
            If true will print debug information about the misses.
        boundary_fuzz: int
            How different the target label boundaries can be from the tested boundaries before it
            doesn't count as a match.
        fields: Sequence[str]
            The field names to compare for equivalency.
        """
        self.correct = 0
        self.total = 0
        self.name = name
        self.mode = mode
        self.print_debug = print_debug
        self.boundary_fuzz = boundary_fuzz
        self.fields = fields

    @property
    def value(self) -> float:
        return self.correct / self.total if self.total > 0 else 1.

    def find_candidates(self, tested_index: LabelIndex, target_label: Label) -> LabelIndex:
        if self.boundary_fuzz == 0:
            index = tested_index.at(target_label)
        else:
            index = tested_index.inside(
                target_label.start_index - 1,
                target_label.end_index + 1
            ).covering(
                target_label.start_index + 1,
                target_label.end_index - 1
            )
        return index

    def fields_match(self, tested_label: Label, target_label: Label) -> bool:
        fields = self.fields if self.fields is not ... else target_label.fields.keys() - {'start_index', 'end_index'}
        return all(getattr(tested_label, field) == getattr(target_label, field) for field in fields)

    def has_match(self, candidates: LabelIndex, target_label: Label) -> bool:
        if self.mode == 'equals':
            return len(candidates) == 1 and self.fields_match(candidates[0], target_label)
        elif self.mode == 'location':
            return len(candidates) > 0
        elif self.mode == 'any':
            return any(self.fields_match(candidate, target_label) for candidate in candidates)

    def update(self, document: Document, tested_index: LabelIndex, target_index: LabelIndex) -> Any:
        correct = 0
        total = 0
        for target_label in target_index:
            total += 1
            candidates = self.find_candidates(tested_index, target_label)
            if self.has_match(candidates, target_label):
                correct += 1
            elif self.print_debug:
                print_overlapping(document, target_label, tested_index)

        self.correct += correct
        self.total += total
        return correct / total if total != 0 else 1.
