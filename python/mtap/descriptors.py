# Copyright 2023 Regents of the University of Minnesota.
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
"""Descriptors for processor functionality."""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Type, Callable

if TYPE_CHECKING:
    from mtap.processing import EventProcessor

__all__ = [
    'label_property',
    'LabelPropertyDescriptor',
    'labels',
    'LabelIndexDescriptor',
    'parameter',
    'ParameterDescriptor',
    'processor',
    'ProcessorDescriptor'
]


@dataclass
class ProcessorDescriptor:
    """Decorator which attaches a service name and metadata to a processor.
    Which then can be used for runtime reflection of how the processor works.


    Returns:
        A decorator to be applied to instances of EventProcessor or
        DocumentProcessor. This decorator attaches the metadata, so it can be
        reflected at runtime.

    Examples:
        >>> from mtap.processing import EventProcessor
        >>> @processor('example-text-converter')
        >>> class TextConverter(EventProcessor):
        >>>     ...

        or

        >>> from mtap.processing import DocumentProcessor
        >>> @processor('example-sentence-detector')
        >>> class SentenceDetector(DocumentProcessor):
        >>>     ...

        From our own example processor:

        >>> from mtap.processing import DocumentProcessor
        >>> @processor('mtap-example-processor-python',
        >>>            human_name="Python Example Processor",
        >>>            description="counts the number of times the letters a"
        >>>                        "and b occur in a document",
        >>>            parameters=[
        >>>                parameter(
        >>>                     'do_work',
        >>>                     required=True,
        >>>                     data_type='bool',
        >>>                     description="Whether the processor should do"
        >>>                                 "anything."
        >>>                )
        >>>            ],
        >>>            outputs=[
        >>>                labels('mtap.examples.letter_counts',
        >>>                       properties=[label_property('letter',
        >>>                                                  data_type='str'),
        >>>                                   label_property('count',
        >>>                                                  data_type='int')])
        >>>            ])
        >>> class ExampleProcessor(DocumentProcessor):
        >>>     ...
    """

    name: str
    """Identifying service name both for launching via command line and
    for service registration.

    Should be a mix of alphanumeric characters and dashes so that it
    plays nice with the DNS name requirements of service discovery
    tools like Consul.
    """

    human_name: Optional[str] = None
    """An optional human name for the processor."""

    description: Optional[str] = None
    """A short description of the processor and what it does."""

    parameters: Optional[List['ParameterDescriptor']] = None
    """The processor's parameters."""

    inputs: Optional[List['LabelIndexDescriptor']] = None
    """String identifiers for the label output from a previously-run
    processor that this processor requires as an input.

    Takes the format ``"[processor-name]/[output]"``. Examples would be
    ``"tagger/pos_tags"`` or ``"sentence-detector/sentences"``.
    """

    outputs: Optional[List['LabelIndexDescriptor']] = None
    """The label indices this processor outputs."""

    additional_data: Optional[Dict[str, Any]] = None
    """Any other data that should be added to the
    processor's metadata, should be serializable to yaml and json.
    """

    def __call__(self, cls: Type['EventProcessor']) -> Type['EventProcessor']:
        cls.metadata.update(asdict(self))
        return cls


processor: Callable[..., ProcessorDescriptor] = ProcessorDescriptor


@dataclass
class ParameterDescriptor:
    """A description of one of the processor's parameters.
    """

    name: str
    """The parameter name / key."""

    description: Optional[str] = None
    """A short description of the property and what it does."""

    data_type: Optional[str] = None
    """The data type of the parameter. str, float, or bool; List[T]
    or Mapping[T1, T2] of those."""

    required: bool = False
    """Whether the processor parameter is required."""


parameter: Callable[..., ParameterDescriptor] = ParameterDescriptor
"""Alias for :class:`~mtap.descriptors.ParameterDescriptor`."""


@dataclass
class LabelIndexDescriptor:
    """A description for a label type.
    """

    name: str
    """The label index name."""

    reference: Optional[str] = None
    """If this is an output of another processor, that processor's
    name followed by a slash and the default output name of the index
    go here.
    Example: "sentence-detector/sentences"."""

    name_from_parameter: Optional[str] = None
    """If the label index gets its name from a parameter of the processor,
    specify that name here."""

    optional: bool = False
    """Whether this label index is an optional input or  output."""

    description: Optional[str] = None
    """A short description of the label index."""

    properties: Optional[List['LabelPropertyDescriptor']] = None
    """The properties of the labels in the label index."""


labels: Callable[..., 'LabelIndexDescriptor'] = LabelIndexDescriptor
"""Alias for :class:`~mtap.descriptors.ParameterDescriptor`"""


@dataclass
class LabelPropertyDescriptor:
    """Creates a description for a property on a label.
    """

    name: str
    """The property's name."""

    description: Optional[str] = None
    """A short description of the property."""

    data_type: Optional[str] = None
    """The data type of the property. Options are ``"str"``, ``"float"``, or
    ``"bool"``; ``"List[T]"`` or ``"Mapping[str, T]"`` where ``T`` is
    one of those types."""

    nullable: bool = False
    """Whether the property can have a valid value of null."""


label_property: Callable[..., LabelPropertyDescriptor] = LabelPropertyDescriptor
"""Alias for :class:`~mtap.descriptors.LabelPropertyDescriptor`."""
