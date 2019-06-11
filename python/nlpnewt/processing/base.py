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

from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import List, ContextManager, Any, Dict, NamedTuple, Optional, Type

from nlpnewt.events import Event, Document
from nlpnewt.processing._context import processor_local

__all__ = [
    'property_description',
    'label_description',
    'processor',
    'EventProcessor',
    'DocumentProcessor',
    'ProcessingResult',
    'TimerStats',
    'AggregateTimingInfo'
]

PropertyDescription = NamedTuple('PropertyDescription',
                                 [('name', str),
                                  ('description', Optional[str]),
                                  ('type', Optional[str])])


def property_description(name: str,
                         description: Optional[str] = None,
                         type: Optional[str] = None) -> PropertyDescription:
    """Creates a description for a property on a label.

    Parameters
    ----------
    name: str
        The property's name.
    description: optional str
        A short description of the property.
    type: optional str
        The data type of the property.

    Returns
    -------
    PropertyDescription
        An object describing a label's property.

    """
    return PropertyDescription(name, description, type)


LabelDescription = NamedTuple('LabelIndexDescription',
                              [('name', str),
                               ('description', Optional[str]),
                               ('properties', List[PropertyDescription])])


def label_description(name: str,
                      description: Optional[str] = None,
                      properties: Optional[List[PropertyDescription]] = None):
    """Creates a description for a label type.

    Parameters
    ----------
    name: str
        The label index name.
    description: optional str
        A short description of the label index.
    properties: optional list of PropertyDescription

    Returns
    -------
    LabelDescription
        An object describing a label.

    """
    if properties is None:
        properties = []
    return LabelDescription(name, description, properties)


def _desc_to_dict(description: LabelDescription) -> dict:
    return {
        'name': description.name,
        'description': description.description,
        'properties': [
            {
                'name': p.name,
                'description': p.description,
                'type': p.type
            } for p in description.properties
        ]
    }


def processor(name: str,
              description: Optional[str] = None,
              inputs: Optional[List[LabelDescription]] = None,
              outputs: Optional[List[LabelDescription]] = None,
              additional_metadata: Optional[Dict[str, Any]] = None):
    """Decorator which attaches a service name to a processor for launching with the nlpnewt command
    line


    Parameters
    ----------
    name: str
        Identifying service name both for launching via command line and for service registration.

        Should be a mix of alphanumeric characters and dashes so that they play nice with the DNS
        name requirements of stuff like Consul.

        This can be modified for service registration at runtime by overriding
        :func:'Processor.registration_processor_name'.
    description: optional str
        A short description of the processor and what it does.
    inputs: optional list of LabelDescription
        The label indices this processor uses as inputs.
    outputs: optional list of LabelDescription
        The label indices this processor outputs.
    additional_metadata: dict
        Any other data that should be added to the processor's metadata, should be serializable to
        yaml and json.

    Returns
    -------
    decorator
        To be applied to instances of EventProcessor or DocumentProcessor. This decorator sets
        the attribute 'name' on the processor.

    Examples
    --------
    >>> @processor('example-text-converter')
    >>> class TextConverter(EventProcessor):
    >>>

    or

    >>> @processor('example-sentence-detector')
    >>> class SentenceDetector(DocumentProcessor):
    >>>

    """
    if inputs is None:
        inputs = []
    if outputs is None:
        outputs = []

    def decorator(f: Type[EventProcessor]) -> Type[EventProcessor]:
        f.metadata['name'] = name
        f.metadata['description'] = description
        f.metadata['inputs'] = [_desc_to_dict(desc) for desc in inputs]
        f.metadata['outputs'] = [_desc_to_dict(desc) for desc in outputs]
        if additional_metadata is not None:
            f.metadata.update(additional_metadata)
        return f

    return decorator


class ProcessorMeta(ABCMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls.metadata = {
            'description': None,
            'inputs': [],
            'outputs': []
        }
        return cls


class EventProcessor(metaclass=ProcessorMeta):
    """Abstract base class for an event processor.

    Implementation should either have the default constructor or one which takes a single argument
    of type :obj:`ProcessorContext`.

    Examples
    --------
    >>> class ExampleProcessor(EventProcessor):
    >>>     def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          pass
    >>>


    >>> class ExampleProcessor(EventProcessor):
    >>>     def process(self, event: Event, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    >>>          with self.context.stopwatch('key'):
    >>>               # use stopwatch

    """

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._health_callback = None
        return instance

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
    def stopwatch(key: str) -> ContextManager:
        """An object that can be used to time aspects of processing.

        Parameters
        ----------
        key: str
            The key to store the time under

        Returns
        -------
        ContextManager
            A context manager object that is used to do the timing.

        Examples
        --------
        >>> # In a process method
        >>> with context.stopwatch('something'):
        >>>     # do work
        >>>

        """
        return processor_local.context.stopwatch(key)

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
    >>>          with self.context.stopwatch('key'):
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
        document = event[params['document_name']]
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
