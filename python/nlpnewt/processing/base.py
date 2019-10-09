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
"""Internal processors and pipelines functionality."""
import contextlib

import threading
from abc import ABCMeta, abstractmethod
from datetime import timedelta, datetime
from typing import List, ContextManager, Any, Dict, NamedTuple, Optional

from nlpnewt.events import Event, Document

__all__ = [
    'ProcessorContext',
    'Stopwatch',
    'ProcessorMeta',
    'Processor',
    'EventProcessor',
    'DocumentProcessor',
    'ProcessingResult',
    'TimerStats',
    'AggregateTimingInfo'
]


class ProcessorContext:
    def __init__(self, identifier):
        self.times = {}
        self.identifier = identifier

    def add_time(self, key, duration):
        self.times[self.identifier + ':' + key] = duration


class Stopwatch(ContextManager, metaclass=ABCMeta):
    """A class for timing runtime of components and returning the total runtime with the
    processor's results.

    Attributes
    ==========
    duration: timedelta
        The amount of time elapsed for this timer.

    Examples
    ========
    >>> # in an EventProcessor or DocumentProcessor process method call
    >>> with self.started_stopwatch('key'):
    >>>     timed_routine()


    >>> # in an EventProcessor or DocumentProcessor process method call
    >>> with self.unstarted_stopwatch('key') as stopwatch:
    >>>     for a in b:
    >>>         # work you don't want timed
    >>>         ...
    >>>         stopwatch.start()
    >>>         # work you want timed
    >>>         ...
    >>>         stopwatch.stop()


    """

    def __init__(self, context: Optional = None, key: Optional[str] = None):
        self._key = key
        self._context = context
        self._running = False
        self.duration = timedelta()
        self._start = None

    def start(self):
        """Starts the timer.
        """
        if not self._running:
            self._running = True
            self._start = datetime.now()

    def stop(self):
        """Stops / pauses the timer
        """
        if self._running:
            self._running = False
            self.duration += datetime.now() - self._start

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._running:
            self.stop()
        try:
            self._context.add_time(self._key, self.duration)
        except AttributeError:  # If context is None
            pass


class ProcessorMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls.metadata = {
            'description': None,
            'inputs': [],
            'outputs': []
        }
        return cls


processor_local = threading.local()


class Processor(metaclass=ProcessorMeta):
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._health_callback = None
        return instance

    def update_serving_status(self, status: str):
        """Updates the serving status of the processor for health checking.

        Parameters
        ----------
        status: str
            One of "SERVING", "NOT_SERVING", "UNKNOWN".

        """
        if self._health_callback is not None:
            self._health_callback(status)

    @staticmethod
    def started_stopwatch(key: str) -> Stopwatch:
        """An object that can be used to time aspects of processing. The stopwatch will be started
        at creation.

        Parameters
        ----------
        key: str
            The key to store the time under

        Returns
        -------
        Stopwatch
            An object that is used to do the timing.

        Examples
        --------
        >>> # In a process method
        >>> with self.started_stopwatch('key'):
        >>>     # do work
        >>>

        """
        try:
            stopwatch = processor_local.context.unstarted_stopwatch(key)
        except AttributeError:
            stopwatch = Stopwatch()
        stopwatch.start()
        return stopwatch

    @staticmethod
    def unstarted_stopwatch(key: str) -> Stopwatch:
        """An object that can be used to time aspects of processing. The stopwatch will be stopped
        at creation.

        Parameters
        ----------
        key: str
            The key to store the time under

        Returns
        -------
        Stopwatch
            An object that is used to do the timing.

        Examples
        --------
        >>> # In a process method
        >>> with self.unstarted_stopwatch('key') as stopwatch:
        >>>     for x in y:
        >>>         # work you don't want timed
        >>>         ...
        >>>         stopwatch.start()
        >>>         # work you do want timed
        >>>         ...
        >>>         stopwatch.stop()


        """
        try:
            return processor_local.context.unstarted_stopwatch(key)
        except AttributeError:
            return Stopwatch()

    @staticmethod
    @contextlib.contextmanager
    def enter_context(identifier: str) -> ContextManager[ProcessorContext]:
        """Used by the mnlp framework to enter a processing context. Users should not need to call
        this in normal usage.

        Parameters
        ----------
        identifier: str
            The context identifier, either processor identifier or pipeline component identifier.

        Returns
        -------
        ContextManager[ProcessorContext]
            A context manager for a ProcessorContext object.

        """
        try:
            old_context = processor_local.context
            identifier = old_context.identifier + '.' + identifier
        except AttributeError:
            old_context = None
        try:
            processor_local.context = ProcessorContext(identifier)
            yield processor_local.context
        finally:
            del processor_local.context
            if old_context is not None:
                processor_local.context = old_context


class EventProcessor(Processor):
    """Abstract base class for an event processor.

    Implementation should either have the default constructor or one which takes a single argument
    of type :obj:`ProcessorContext`.

    Examples
    --------
    >>> class ExampleProcessor(EventProcessor):
    >>>     def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          pass
    >>>

    """

    @abstractmethod
    def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs processing on an event.

        Parameters
        ----------
        event: Event
            The event object to be processed.
        params: typing.Dict[str, Any]
            Processing parameters. A dictionary of strings mapped to json-serializable values.

        Returns
        -------
        typing.Dict[str, Any], optional
            A dictionary of strings mapped to strings. This likewise may be replaced with a json
            struct at a later point.

        """
        ...

    def close(self):
        """Used for cleaning up anything that needs to be cleaned up.

        """
        pass


class DocumentProcessor(EventProcessor, metaclass=ProcessorMeta):
    """Abstract base class for a document processor.

    Examples
    --------
    >>> class ExampleProcessor(DocumentProcessor):
    >>>     def process(self,
    >>>                 document: Document,
    >>>                 params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          pass
    >>>


    >>> class ExampleProcessor(DocumentProcessor):
    >>>     def process(self,
    >>>                 document: Document,
    >>>                 params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          with self.context.unstarted_stopwatch('key'):
    >>>               # use stopwatch

    """

    @abstractmethod
    def process_document(self, document: Document, params: Dict[str, Any]) -> Optional[
        Dict[str, Any]]:
        """Implemented by the subclass, your processor.

        Parameters
        ----------
        document: Document
            The document object to be processed.
        params: typing.Dict[str, Any]
            Processing parameters. A dictionary of strings mapped to json-serializable values.

        Returns
        -------
        typing.Dict[str, Any], optional
            A dictionary of strings mapped to strings. This likewise may be replaced with a json
            struct at a later point.

        """
        ...

    def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calls the subclass's implementation of :func:`process_document` """
        document = event.documents[params['document_name']]
        return self.process_document(document, params)


ProcessingResult = NamedTuple('ProcessingResult',
                              [('identifier', str),
                               ('results', Dict),
                               ('timing_info', Dict),
                               ('created_indices', Dict[str, List[str]])])

ProcessingResult.__doc__ = """The result of processing one document or event."""
ProcessingResult.identifier.__doc__ = \
    "str: The id of the processor with respect to the pipeline."
ProcessingResult.results.__doc__ = \
    "dict[str, typing.Any]: The json object returned by the processor as its results."
ProcessingResult.timing_info.__doc__ = \
    "dict[str, datetime.timedelta]: A dictionary of the times taken processing this document"
ProcessingResult.created_indices.__doc__ = \
    "dict[str, list[str]]: Any indices that have been added to documents by this processor."

TimerStats = NamedTuple('TimerStats',
                        [('mean', timedelta),
                         ('std', timedelta),
                         ('min', timedelta),
                         ('max', timedelta),
                         ('sum', timedelta)])
TimerStats.__doc__ = """Statistics about a labeled runtime."""
TimerStats.mean.__doc__ = "datetime.timedelta: The mean duration."
TimerStats.std.__doc__ = "datetime.timedelta: The standard deviation of all times."
TimerStats.max.__doc__ = "datetime.timedelta: The minimum of all times."
TimerStats.min.__doc__ = "datetime.timedelta: The maximum of all times."
TimerStats.sum.__doc__ = "datetime.timedelta: The sum of all times."

_AggregateTimingInfo = NamedTuple('AggregateTimingInfo',
                                  [('identifier', str),
                                   ('timing_info', Dict[str, TimerStats])])

_AggregateTimingInfo.identifier.__doc__ = \
    "str: The ID of the processor with respect to the pipeline."
_AggregateTimingInfo.timing_info.__doc__ = \
    "dict[str, TimerStats]: A map from all of the timer labels to their aggregate values."


class AggregateTimingInfo(_AggregateTimingInfo):
    """Collection of all of the timing info for a specific processor."""

    def print_times(self):
        """Prints the aggregate timing info for all processing components using ``print``.

        """
        print(self.identifier)
        print("-------------------------------------")
        for key, stats in self.timing_info.items():
            print("  [{}]\n"
                  "    mean: {}\n"
                  "    std: {}\n"
                  "    min: {}\n"
                  "    max: {}\n"
                  "    sum: {}".format(key, stats.mean, stats.std, stats.min,
                                       stats.max, stats.sum))
        print("")
