# Copyright 2022 Regents of the University of Minnesota.
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
from abc import ABCMeta, abstractmethod, ABC
from datetime import datetime, timedelta
from typing import (
    ContextManager,
    Any,
    Dict,
    Optional,
    Mapping,
    Tuple,
    TYPE_CHECKING,
    MutableMapping
)

from mtap import data

if TYPE_CHECKING:
    import mtap
    from mtap import Event, Document
    from mtap.data import ProtoLabelAdapter


class ProcessorContext:
    __slots__ = ('times',)

    def __init__(self):
        self.times = {}

    def add_time(self, key, duration):
        try:
            self.times[key] += duration
        except KeyError:
            self.times[key] = duration


class Stopwatch(ContextManager, metaclass=ABCMeta):
    """A class for timing runtime of components and returning the total
    runtime with the processor's results.

    Although it can be instantiated and used outside a processing context the
    normal usage would be to instantiate using
    :meth:`Processor.started_stopwatch` or
    :meth:`Processor.unstarted_stopwatch` methods.

    Attributes:
        duration: The amount of time elapsed for this timer.

    Examples:

        >>> # in an EventProcessor or DocumentProcessor process method call
        >>> with self.started_stopwatch('key'):
        >>>     timed_routine()


        >>> # in an EventProcessor or DocumentProcessor process method call
        >>> with self.unstarted_stopwatch('key') as stopwatch:
        >>>     for _ in range(10):
        >>>         # work you don't want timed
        >>>         ...
        >>>         stopwatch.start()
        >>>         # work you want timed
        >>>         ...
        >>>         stopwatch.stop()
    """
    __slots__ = ('_key', '_context', '_running', 'duration', '_start')

    duration: timedelta

    def __init__(self, key: Optional[str] = None, context: Optional = None):
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


processor_local = threading.local()


class Processor:
    """Mixin used by all processor abstract base classes that provides the
    ability to update serving status and use timers.
    """
    __slots__ = ('_health_callback')

    metadata = {}

    def update_serving_status(self, status: str):
        """Updates the serving status of the processor for health checking.

        Args:
            status (str): One of "SERVING", "NOT_SERVING", "UNKNOWN".
        """
        try:
            self._health_callback(status)
        except AttributeError:
            pass

    @staticmethod
    def current_context() -> 'Optional[ProcessorContext]':
        return getattr(processor_local, 'context', None)

    @staticmethod
    def started_stopwatch(key: str) -> Stopwatch:
        """An object that can be used to time aspects of processing. The
        stopwatch will be started at creation.

        Args:
            key: The key to store the time under.

        Returns:
            An object that is used to do the timing.

        Examples:
            >>> # In a process method
            >>> with self.started_stopwatch('key'):
            >>>     # do work
            >>>     ...

        """
        stopwatch = Stopwatch(key, getattr(processor_local, 'context', None))
        stopwatch.start()
        return stopwatch

    @staticmethod
    def unstarted_stopwatch(key: str) -> Stopwatch:
        """An object that can be used to time aspects of processing. The
        stopwatch will be stopped at creation.

        Args:
            key: The key to store the time under.

        Returns:
            An object that is used to do the timing.

        Examples:
            >>> # In a process method
            >>> with self.unstarted_stopwatch('key') as stopwatch:
            >>>     for _ in range(10):
            >>>         # work you don't want timed
            >>>         ...
            >>>         stopwatch.start()
            >>>         # work you do want timed
            >>>         ...
            >>>         stopwatch.stop()
        """
        return Stopwatch(key, getattr(processor_local, 'context', None))

    @staticmethod
    @contextlib.contextmanager
    def enter_context() -> ContextManager[ProcessorContext]:
        # Used by the MTAP framework to enter a processing context where things like timing
        # results are stored. Users should not need to call this in normal usage.
        try:
            old_context = processor_local.context
        except AttributeError:
            old_context = None
        try:
            processor_local.context = ProcessorContext()
            yield processor_local.context
        finally:
            del processor_local.context
            if old_context is not None:
                processor_local.context = old_context


class EventProcessor(Processor):
    """Abstract base class for an event processor.

    Examples:
        >>> class ExampleProcessor(EventProcessor):
        ...     def process(self, event, params):
        ...          # do work on the event
        ...          ...
    """
    __slots__ = ()

    @property
    def custom_label_adapters(self) -> 'Mapping[str, ProtoLabelAdapter]':
        """Optional method used to provide non-standard proto label adapters
        for specific index names. Default implementation returns an empty
        dictionary.

        Returns:
            A mapping from strings to label adapters.
        """
        return {}

    @abstractmethod
    def process(
            self,
            event: 'Event',
            params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Performs processing on an event, implemented by the subclass.

        Parameters:
            event: The event object to be processed.
            params: Processing parameters. A dictionary of strings mapped to
                json-serializable values.

        Returns:
            An arbitrary dictionary of strings mapped to json-serializable
            values which will be returned to the caller, even remotely.
        """
        ...

    def close(self):
        """Can be overridden for cleaning up anything that needs to be cleaned
        up. Will be called by the framework after it's done with the processor.
        """
        pass


class DocumentProcessor(EventProcessor):
    """Abstract base class for a document processor.

    Examples:
        >>> class ExampleProcessor(mtap.DocumentProcessor):
        ...     def process(self, document, params):
        ...         # do processing on document
        ...         ...


        >>> class ExampleProcessor(mtap.DocumentProcessor):
        ...     def process(self, document, params):
        ...          with self.started_stopwatch('key'):
        ...               # use stopwatch on something
        ...               ...

    """
    __slots__ = ()

    @abstractmethod
    def process_document(self,
                         document: 'Document',
                         params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs processing of a document on an event, implemented by the
        subclass.

        Args:
            document: The document object to be processed.
            params: Processing parameters. A dictionary of strings mapped to
                json-serializable values.

        Returns:
            An arbitrary dictionary of strings mapped to json-serializable
            values that will be returned to the caller of the processor.
        """
        ...

    def close(self):
        """Can be overridden for cleaning up anything that needs to be cleaned
        up. Will be called by the framework after it's done with the processor.
        """
        pass

    def process(self, event, params):
        document = event.documents[params['document_name']]
        return self.process_document(document, params)


class ProcessingComponent(ABC):
    __slots__ = ()

    metadata = {}

    @property
    @abstractmethod
    def processor_name(self) -> str:
        ...

    @property
    @abstractmethod
    def component_id(self) -> str:
        ...

    @abstractmethod
    def call_process(
            self,
            event_id: str,
            event_instance_id: str,
            params: Optional[Dict[str, Any]]
    ) -> Tuple[Dict, Dict, Dict]:
        """Calls a processor.

        Parameters
            event_id: The event to process.
            event_instance_id: The service instance the event is stored on.
            params: The processor parameters.

        Returns
            A tuple of the processing result dictionary, the processor times
            dictionary, and the "created indices" dictionary.
        """
        ...

    def close(self):
        ...
