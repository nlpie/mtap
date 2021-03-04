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
from typing import Dict, Any, Optional, Sequence, NamedTuple, Callable, Tuple, TextIO, TYPE_CHECKING

import sys

__all__ = [
    'Metric',
    'Metrics',
    'print_overlapping',
    'fields_match_test',
    'Accuracy',
    'ConfusionMatrix',
    'FirstTokenConfusion'
]

from mtap.data import presorted_label_index
from mtap.processing import DocumentProcessor, processor
from mtap.utilities import tokenization

if TYPE_CHECKING:
    import mtap
    from mtap import data, label_index


class Metric(ABC):
    """Base class for metrics.

    """
    name = None

    @abstractmethod
    def update(self,
               document: 'mtap.Document',
               tested_index: 'data.LabelIndex', target_index: 'data.LabelIndex') -> Any:
        ...


@processor('mtap-metrics')
class Metrics(DocumentProcessor):
    """A document process that computes a set of metrics.

    Args
    ---
    tested (str): The name of the index to use as the hypothesis / predictions.
    target (str): The name of the index to use as the ground truth / gold standard.
    tested_filter (~typing.Callable[[Label], bool]): A filter to apply to the tested index.
    target_filter (~typing.Callable[[Label], bool]): A filter to apply to the target index.

    """

    def __init__(self, *metrics: Metric,
                 tested: str,
                 target: str,
                 tested_filter: Callable[['data.Label'], bool] = None,
                 target_filter: Callable[['data.Label'], bool] = None):
        self.tested = tested
        self.target = target
        self.metrics = metrics
        self.tested_filter = tested_filter
        self.target_filter = target_filter

    def process_document(self, document: 'mtap.Document',
                         params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tested = document.labels[self.tested]
        if self.tested_filter is not None:
            tested = tested.filter(self.tested_filter)
        target = document.labels.get(self.target, presorted_label_index([]))
        if self.target_filter is not None:
            target = target.filter(self.target_filter)
        local = {}
        for metric in self.metrics:
            local[metric.name] = metric.update(document, tested, target)
        return local


def print_overlapping(document, target_label, tested_index):
    print('Not found:', target_label)
    print('"', target_label.text(document.text), '"')
    overlapping = tested_index.overlapping(target_label)
    print('Overlapping:', overlapping)
    for overlap in overlapping:
        print('"', overlap.text(document.text), '"')


def fields_match_test(fields: Optional[Sequence[str]] = ...):
    """Creates an equivalence test that tests whether the specified fields are equal on both labels.

    Parameters
    ----------
    fields: Optional[Sequence[str]]
        The fields to test or ... if all fields should be tested.

    """

    def fields_match(tested_label: 'data.Label', target_label: 'data.Label') -> bool:
        if fields is not ...:
            return all(
                getattr(tested_label, field) == getattr(target_label, field) for field in fields)
        else:
            return tested_label.shallow_fields_equal(target_label)

    return fields_match


class Accuracy(Metric):
    def __init__(self,
                 name: str = 'accuracy',
                 mode: str = 'equals',
                 print_debug: bool = False,
                 boundary_fuzz: int = 0,
                 fields: Optional[Sequence[str]] = ...,
                 equivalence_test: Optional[Callable[[Any, Any], bool]] = fields_match_test(...)):
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
        equivalence_test: callable
            A function which takes two argument labels, and returns true if the labels are
            equivalent for the purpose of the test.
        """
        self.correct = 0
        self.total = 0
        self.name = name
        self.mode = mode
        self.print_debug = print_debug
        self.boundary_fuzz = boundary_fuzz
        if fields is ...:
            self.equivalence_test = equivalence_test
        else:
            self.equivalence_test = fields_match_test(fields)

    @property
    def value(self) -> float:
        return self.correct / self.total if self.total > 0 else 1.

    def find_candidates(self,
                        tested_index: 'data.LabelIndex',
                        target_label: 'data.Label') -> 'data.LabelIndex':
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

    def has_match(self, candidates: 'data.LabelIndex', target_label: 'data.Label') -> bool:
        if self.mode == 'equals':
            return len(candidates) == 1 and self.equivalence_test(candidates[0], target_label)
        elif self.mode == 'location':
            return len(candidates) > 0
        elif self.mode == 'any':
            return any(self.equivalence_test(candidate, target_label) for candidate in candidates)

    def update(self, document: 'mtap.Document',
               tested_index: 'data.LabelIndex',
               target_index: 'data.LabelIndex') -> Any:
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


def _collect_tokens(index, return_insides=True):
    begins = set()
    insides = set()
    for label in index:
        for i, token in enumerate(tokenization.word_tokenize(label.text, label.start_index)):
            if i == 0:
                begins.add(token)
                if not return_insides:
                    break
            else:
                insides.add(token)

    return begins, insides


class ConfusionMatrix(NamedTuple('ConfusionMatrix',
                                 [('true_positives', float),
                                  ('false_positives', float),
                                  ('false_negatives', float)])):
    """A representation of a confusion matrix.

    Attributes
    ----------
    true_positives (float): Count of true positive examples.
    false_positives (float): Count of false positive examples.
    false_negatives (float): Count of false negative examples.
    precision (float): Ratio of true positives to the total number of positive predictions.
    recall (float): Ratio of true positives to the total number of positive ground truths.
    f1 (float): The harmonic mean of precision and recall.

    """

    def __new__(cls, true_positives: float = 0,
                false_positives: float = 0,
                false_negatives: float = 0):
        self = super().__new__(cls, true_positives, false_positives, false_negatives)
        return self

    def __add__(self, other):
        return self.__class__(self.true_positives + other.true_positives,
                              self.false_positives + other.false_positives,
                              self.false_negatives + other.false_negatives)

    @property
    def precision(self):
        predicted_positives = self.true_positives + self.false_positives
        if predicted_positives == 0:
            return 1
        return self.true_positives / predicted_positives

    @property
    def recall(self):
        ground_truth_positives = self.true_positives + self.false_negatives
        if ground_truth_positives == 0:
            return 1
        return self.true_positives / ground_truth_positives

    @property
    def f1(self):
        divisor = 2 * self.true_positives + self.false_positives + self.false_negatives
        if divisor == 0:
            return 1
        return 2 * self.true_positives / divisor


class FirstTokenConfusion(Metric):
    """A metric which treats the first word token in every label as an example of the positive
    class and calculates the precision, recall, and f1 confusion matrix metrics for that
    positive class. Useful for evaluation of segmentation tasks.

    precision = true positives / (true positives + false positives)
    recall = true positives / (true positives + false negatives)
    f1 = 2 * true positives / (2 * true positives + false positives + false negatives)

    Args
    ----
    name (str): An identifying name for the metric.
    tested_filter (~typing.Callable[[Label], bool]): A filter to apply to the tested index.
    target_filter (~typing.Callable[[Label], bool]): A filter to apply to the target index.
    print_debug (str)
        An argument to print failing examples. 'fp' prints only false positive
        errors, 'fn' prints only false negative errors, 'all' prints both false positive and false
        negative errors
    debug_range (int): The range before and after the example to print.
    debug_handle (TextIO): A text io file handle to print the debug information to.

    Attributes
    ----------
    precision (float): Ratio of true positives to the total number of positive predictions.
    recall (float): Ratio of true positives to the total number of positive ground truths.
    f1 (float): The harmonic mean of precision and recall.
    """

    def __init__(self, name: str = 'first_token_confusion',
                 tested_filter: Callable[['data.Label'], bool] = None,
                 target_filter: Callable[['data.Label'], bool] = None,
                 print_debug: str = None,
                 debug_range: int = 30,
                 debug_handle: TextIO = sys.stdout):
        self.name = name
        self._matrix = ConfusionMatrix()
        self.tested_filter = tested_filter
        self.target_filter = target_filter
        self.print_debug = print_debug
        self.debug_range = debug_range
        self.debug_handle = debug_handle

    @property
    def precision(self) -> float:
        return self._matrix.precision

    @property
    def recall(self) -> float:
        return self._matrix.recall

    @property
    def f1(self) -> float:
        return self._matrix.f1

    def update(self,
               document: 'mtap.Document',
               tested_index: 'data.LabelIndex',
               target_index: 'data.LabelIndex') -> Any:
        if self.tested_filter is not None:
            tested_index = tested_index.filter(self.tested_filter)
        if self.target_filter is not None:
            target_index = target_index.filter(self.target_filter)
        tested_tokens, _ = _collect_tokens(tested_index, return_insides=False)
        target_tokens, _ = _collect_tokens(target_index, return_insides=False)
        false_positives = tested_tokens.difference(target_tokens)
        false_negatives = target_tokens.difference(tested_tokens)
        if self.print_debug in ('fp', 'all'):
            self.debug_handle.write('False Positives\n')
            for false_positive in false_positives:
                _print_example(document.text, false_positive, self.debug_range, self.debug_handle)
            self.debug_handle.write('\n')
        if self.print_debug in ('fn', 'all'):
            self.debug_handle.write('False Negatives\n')
            for false_negative in false_negatives:
                _print_example(document.text, false_negative, self.debug_range, self.debug_handle)
            self.debug_handle.write('\n')
        local = ConfusionMatrix(
            true_positives=len(tested_tokens.intersection(target_tokens)),
            false_negatives=len(false_negatives),
            false_positives=len(false_positives)
        )
        self._matrix += local
        return {
            'precision': local.precision,
            'recall': local.recall,
            'f1': local.f1
        }


def _print_example(text: str,
                   token: Tuple[int, int],
                   debug_range: int,
                   debug_handle: TextIO):
    start, end = token
    print_start = max(0, start - debug_range)
    print_end = min(end + debug_range, len(text))
    text = text[print_start:start] + '{' + text[start:end] + '}' + text[end:print_end]
    text = text.replace('\n', ' ') + '\n'
    debug_handle.write(text)
