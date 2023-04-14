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
import typing
from typing import NamedTuple, Optional, List, Dict, Any

if typing.TYPE_CHECKING:
    from mtap import EventProcessor

__all__ = [
    'label_property',
    'labels',
    'parameter',
    'processor',
]


def processor(name: str,
              *,
              human_name: Optional[str] = None,
              description: Optional[str] = None,
              parameters: 'Optional[List[parameter]]' = None,
              inputs: 'Optional[List[labels]]' = None,
              outputs: 'Optional[List[labels]]' = None,
              **additional_metadata: Any):
    """Decorator which attaches a service name and metadata to a processor.
    Which then can be used for runtime reflection of how the processor works.

    Args:
        name: Identifying service name both for launching via command line and
            for service registration.
            Should be a mix of alphanumeric characters and dashes so that it
            plays nice with the DNS name requirements of service discovery
            tools like Consul.
        human_name: An optional human name for the processor.
        description: A short description of the processor and what it does.
        parameters: The processor's parameters.
        inputs: String identifiers for the label output from a previously-run
            processor that this processor requires as an input.

            Takes the format ``"[processor-name]/[output]"``. Examples would be
            ``"tagger/pos_tags"`` or ``"sentence-detector/sentences"``.
        outputs: The label indices this processor outputs.
        **additional_metadata: Any other data that should be added to the
            processor's metadata, should be serializable to yaml and json.

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

    def decorator(cls):
        cls.metadata = {
            'name': name,
            'human_name': human_name,
            'description': description
        }
        if parameters is not None:
            cls.metadata['parameters'] = [_parameter_to_map(p)
                                          for p in parameters]
        if inputs is not None:
            cls.metadata['inputs'] = [_desc_to_dict(desc) for desc in inputs]
        if outputs is not None:
            cls.metadata['outputs'] = [_desc_to_dict(desc) for desc in outputs]
        if additional_metadata is not None:
            cls.metadata.update(additional_metadata)
        if 'implementation_lang' not in cls.metadata:
            cls.metadata['implementation_lang'] = 'Python'

        return cls

    return decorator


class parameter(NamedTuple):
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


class labels(NamedTuple):
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

    properties: 'Optional[List[label_property]]' = None
    """The properties of the labels in the label index."""


class label_property(NamedTuple):
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


def _desc_to_dict(description: labels) -> dict:
    m = {
        'name': description.name
    }
    if description.name_from_parameter is not None:
        m['name_from_parameter'] = description.name_from_parameter
    if description.reference is not None:
        m['reference'] = description.reference
    if description.optional is not None:
        m['optional'] = description.optional
    if description.description is not None:
        m['description'] = description.description
    if description.properties is not None:
        m['properties'] = [_prop_to_dict(p) for p in description.properties]
    return m


def _prop_to_dict(p: label_property) -> Dict[str, Any]:
    m = {
        'name': p.name
    }
    if p.description is not None:
        m['description'] = p.description
    if p.data_type is not None:
        m['data_type'] = p.data_type
    if p.nullable is not None:
        m['nullable'] = p.nullable
    return m


def _parameter_to_map(p: parameter) -> Dict[str, Any]:
    m = {
        'name': p.name
    }
    if p.description is not None:
        m['description'] = p.description
    if p.data_type is not None:
        m['data_type'] = p.data_type
    if p.required is not None:
        m['required'] = p.required
    return m
