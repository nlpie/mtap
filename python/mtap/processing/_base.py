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
from abc import ABCMeta, abstractmethod, ABC
from datetime import timedelta, datetime
from typing import List, ContextManager, Any, Dict, NamedTuple, Optional, Mapping, Generator, \
    Tuple, TYPE_CHECKING

from mtap import data


if TYPE_CHECKING:
    import mtap
    import mtap.processing as processing


class ProcessorContext:
    def __init__(self):
        self.times = {}

    def add_time(self, key, duration):
        try:
            self.times[key] += duration
        except KeyError:
            self.times[key] = duration


class Stopwatch(ContextManager, metaclass=ABCMeta):
    """A class for timing runtime of components and returning the total runtime with the
    processor's results.

    Attributes:
        duration (~datetime.timedelta): The amount of time elapsed for this timer.

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
        cls.metadata = {}
        return cls


processor_local = threading.local()


class Processor:
    """Mixin used by all processor abstract base classes that provides the ability to update
    serving status and use timers.
    """

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._health_callback = None
        return instance

    def update_serving_status(self, status: str):
        """Updates the serving status of the processor for health checking.

        Args:
            status (str): One of "SERVING", "NOT_SERVING", "UNKNOWN".
        """
        if self._health_callback is not None:
            self._health_callback(status)

    @property
    def custom_label_adapters(self) -> Mapping[str, data.ProtoLabelAdapter]:
        """Used to provide non-standard proto label adapters for specific index names.

        Returns:

        """
        return {}

    @staticmethod
    def current_context() -> Optional['processing.ProcessorContext']:
        return getattr(processor_local, 'context', None)

    @staticmethod
    def started_stopwatch(key: str) -> Stopwatch:
        """An object that can be used to time aspects of processing. The stopwatch will be started
        at creation.

        Args:
            key (str): The key to store the time under.

        Returns:
            Stopwatch: An object that is used to do the timing.

        Examples:
            >>> # In a process method
            >>> with self.started_stopwatch('key'):
            >>>     # do work
            >>>     ...

        """
        stopwatch = Stopwatch(getattr(processor_local, 'context', None), key)
        stopwatch.start()
        return stopwatch

    @staticmethod
    def unstarted_stopwatch(key: str) -> 'processing.Stopwatch':
        """An object that can be used to time aspects of processing. The stopwatch will be stopped
        at creation.

        Args:
            key (str): The key to store the time under.

        Returns:
            Stopwatch: An object that is used to do the timing.

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
        return Stopwatch(getattr(processor_local, 'context', None), key)

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


class EventProcessor(Processor, metaclass=ProcessorMeta):
    """Abstract base class for an event processor.

    Examples:
        >>> class ExampleProcessor(EventProcessor):
        ...     def process(self, event, params):
        ...          # do work on the event
        ...          ...
    """

    @abstractmethod
    def process(self, event: 'mtap.Event', params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs processing on an event, implemented by the subclass.

        Parameters:
            event (Event): The event object to be processed.
            params (~typing.Dict[str, ~typing.Any]):
                Processing parameters. A dictionary of strings mapped to json-serializable values.

        Returns:
            ~typing.Optional[~typing.Dict[str, Any]]:
                An arbitrary dictionary of strings mapped to json-serializable values which will be
                returned to the caller, even remotely.
        """
        ...

    def default_adapters(self) -> Optional[Mapping[str, data.ProtoLabelAdapter]]:
        """Can be overridden to return a mapping from label index names to adapters that will then
        be used in any documents or events provided to this processor's process methods.

        Returns:
            Mapping[str, ProtoLabelAdapter]: The mapping (dict-like) of label index names to
            ProtoLabelAdapters to be used for those indices.

        """
        pass

    def close(self):
        """Can be overridden for cleaning up anything that needs to be cleaned up. Will be called
        by the framework after it's done with the processor."""
        pass


class DocumentProcessor(EventProcessor, metaclass=ProcessorMeta):
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

    @abstractmethod
    def process_document(self,
                         document: 'mtap.Document',
                         params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Performs processing of a document on an event, implemented by the subclass.

        Args:
            document (~mtap.Document): The document object to be processed.
            params (~typing.Dict[str, ~typing.Any]):
                Processing parameters. A dictionary of strings mapped to json-serializable values.

        Returns:
            ~typing.Dict[str, ~typing.Any]:
                An arbitrary dictionary of strings mapped to json-serializable values that will be
                returned to the caller of the processor.
        """
        ...

    def close(self):
        """Can be overridden for cleaning up anything that needs to be cleaned up. Will be called
        by the framework after it's done with the processor."""
        pass

    def process(self, event: 'mtap.Event', params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        document = event.documents[params['document_name']]
        return self.process_document(document, params)


class ProcessingError(Exception):
    """Exception for when processing results in a failure."""
    pass


ProcessingResult = NamedTuple('ProcessingResult',
                              [('identifier', str),
                               ('result_dict', Dict),
                               ('timing_info', Dict),
                               ('created_indices', Dict[str, List[str]])])

ProcessingResult.__doc__ = """The result of processing one document or event."""
ProcessingResult.identifier.__doc__ = """The id of the processor with respect to the pipeline."""
ProcessingResult.result_dict.__doc__ = """The json object returned by the processor as its results."""
ProcessingResult.timing_info.__doc__ = """A dictionary of the times taken processing this 
document"""
ProcessingResult.created_indices.__doc__ = """Any indices that have been added to documents by this 
processor."""


class PipelineResult(NamedTuple('PipelineResult',
                                [('component_results', List[ProcessingResult]),
                                 ('elapsed_time', timedelta)])):
    """The result of processing an event or document in a pipeline.

    Attributes:
        component_results (List[ProcessingResult]): The processing results for each individual
            component
        elapsed_time (timedelta): The elapsed time for the entire pipeline.

    Args:
        component_results (List[ProcessingResult]): The processing results for each individual
            component
        elapsed_time (timedelta): The elapsed time for the entire pipeline.

    """
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    def component_result(self, identifier: str) -> ProcessingResult:
        """Returns the component result for a specific identifier.

        Args:
            identifier: The processor's identifier in the pipeline.

        Returns:
            ProcessingResult: The result for the specified processor.

        """
        try:
            return next(filter(lambda x: x.identifier == identifier, self.component_results))
        except StopIteration:
            raise KeyError('No result for identifier: ' + identifier)


TimerStats = NamedTuple('TimerStats',
                        [('mean', timedelta),
                         ('std', timedelta),
                         ('min', timedelta),
                         ('max', timedelta),
                         ('sum', timedelta)])
TimerStats.__doc__ = """Statistics about a specific keyed measured duration recorded by a 
:obj:`~mtap.processing.base.Stopwatch`."""
TimerStats.mean.__doc__ = """The sample mean of all measured durations."""
TimerStats.std.__doc__ = """The sample standard deviation of all measured 
durations."""
TimerStats.max.__doc__ = """The minimum of all measured durations."""
TimerStats.min.__doc__ = """The maximum of all measured durations."""
TimerStats.sum.__doc__ = """The sum of all measured durations."""


class AggregateTimingInfo(NamedTuple('AggregateTimingInfo',
                                     [('identifier', str),
                                      ('timing_info', Dict[str, 'processing.TimerStats'])])):
    """Collection of all of the timing info for a specific processor.

    Attributes:
        identifier (str): The ID of the processor with respect to the pipeline.
        timing_info (dict[str, TimerStats]):
            A map from all of the timer keys for the processor to the aggregated duration statistics.
    """

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

    @staticmethod
    def csv_header() -> str:
        """Returns the header for CSV formatted timing data.

        Returns:
             str
        """
        return 'key,mean,std,min,max,sum\n'

    def timing_csv(self) -> Generator[str, None, None]:
        """Returns the timing data formatted as a string, generating each

        Returns:
            Generator[str]
        """
        for key, stats in self.timing_info.items():
            yield '{}:{},{},{},{},{},{}\n'.format(self.identifier, key, stats.mean, stats.std,
                                                  stats.min, stats.max, stats.sum)


class ProcessingComponent(ABC):
    component_id = None  # str: The component_id of the component in a pipeline
    descriptor = None  # ComponentDescriptor: The ComponentDescriptor used to create the component.
    processor_id = None

    @abstractmethod
    def call_process(self, event_id: str,
                     params: Optional[Dict[str, Any]]) -> Tuple[Dict, Dict, Dict]:
        """Calls a processor.

        Parameters
        ----------
        event_id: str
            The event to process.
        params: Dict
            The processor parameters.

        Returns
        -------
        tuple of dict, dict, dict
            A tuple of the processing result dictionary, the processor times dictionary, and the
            created indices dictionary.

        """
        ...

    def close(self):
        ...


class ComponentDescriptor(ABC):
    """A configuration which describes either a local or remote pipeline component and what the
    pipeline needs to do to call the component.
    """

    @abstractmethod
    def create_pipeline_component(self, config: 'mtap.Config',
                                  component_ids: Dict[str, int]) -> 'processing.ProcessingComponent':
        pass
