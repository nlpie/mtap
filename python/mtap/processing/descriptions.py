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
"""Descriptors for processor functionality."""
import typing
from typing import NamedTuple, Optional, List, Type, Dict, Any

if typing.TYPE_CHECKING:
    from mtap.processing.base import EventProcessor

__all__ = [
    'PropertyDescription',
    'label_property',
    'LabelDescription',
    'label_index',
    'ParameterDescription',
    'parameter',
    'processor',
]

PropertyDescription = NamedTuple('PropertyDescription',
                                 [('name', str),
                                  ('description', Optional[str]),
                                  ('data_type', Optional[str]),
                                  ('nullable', bool)])
PropertyDescription.__doc__ = """A description of a property of the labels on a label index."""
PropertyDescription.name.__doc__ = """str: The property's variable name."""
PropertyDescription.description.__doc__ = """~typing.Optional[str]: A short description of the 
property."""
PropertyDescription.data_type.__doc__ = """~typing.Optional[str] The data type of the property: str, 
float, or bool; List[T] or Mapping[T1, T2] of those."""
PropertyDescription.nullable.__doc__ = """bool: Whether the property can have a valid value of 
null."""


def label_property(name: str,
                   *, nullable: bool = False,
                   description: Optional[str] = None,
                   data_type: Optional[str] = None) -> PropertyDescription:
    """Creates a description for a property on a label.

    Args: 
        name (str): The property's name.
        
    Keyword Args:
        nullable (bool): Whether the property can have a valid value of null.
        description (~typing.Optional[str]): A short description of the property.
        data_type (~typing.Optional[str]):
            The data type of the property: str, float, or bool; List[T] or Mapping[T1, T2] of those.

    Returns:
        PropertyDescription: An object describing a label's property.
    """
    return PropertyDescription(name, description, data_type, nullable)


LabelDescription = NamedTuple('LabelDescription',
                              [('name', str),
                               ('reference', Optional[str]),
                               ('name_from_parameter', Optional[str]),
                               ('optional', bool),
                               ('description', Optional[str]),
                               ('properties', List[PropertyDescription])])
LabelDescription.__doc__ = """A description of input or output label index."""
LabelDescription.name_from_parameter.__doc__ = """~typing.Optional[str]: If the label index gets 
its name from a processor parameter, the name of the parameter."""
LabelDescription.optional.__doc__ = """bool: Whether this label index is an optional input or 
output."""
LabelDescription.name.__doc__ = """~typing.Optional[str]: The label index name."""
LabelDescription.description.__doc__ = """~typing.Optional[str]:  A short description of the label 
index."""
LabelDescription.properties.__doc__ = """~typing.Optional[~typing.List[PropertyDescription]]: The 
properties of the labels in the label index."""


def label_index(name: str,
                *,
                reference: Optional[str] = None,
                optional: bool = False,
                name_from_parameter: Optional[str] = None,
                description: Optional[str] = None,
                properties: Optional[List[PropertyDescription]] = None) -> LabelDescription:
    """Creates a description for a label type.

    Args:
        name (str): The label index name.

    Keyword Args:
        reference (~typing.Optional[str]):
            If this is an output of another processor, that processor's name followed by a slash
            and the default output name of the index go here.
            Example: "sentence-detector/sentences".
        optional (bool): Whether this label index is an optional input or output.
        name_from_parameter (~typing.Optional[str]):
            If the label index gets its name from a processor parameter, the name of the parameter.
        description (~typing.Optional[str]): A short description of the label index.
        properties (~typing.Optional[~typing.List[PropertyDescription]]):
            The properties of the labels in the label index.

    Returns:
        LabelDescription: An object describing a label index.
    """
    if properties is None:
        properties = []
    return LabelDescription(name, reference, name_from_parameter, optional, description, properties)


ParameterDescription = NamedTuple('ParameterDescription',
                                  [('name', str),
                                   ('description', Optional[str]),
                                   ('data_type', Optional[str]),
                                   ('required', bool)])
ParameterDescription.__doc__ = """A description of a processor parameter."""
ParameterDescription.name.__doc__ = """str: The parameter name / key."""
ParameterDescription.description.__doc__ = """optional, str: A short description of the property and 
what it does."""
ParameterDescription.data_type.__doc__ = """optional, str:  The data type of the parameter. str, 
float, or bool; List[T] or Mapping[T1, T2] of those."""
ParameterDescription.required.__doc__ = """bool: Whether the parameter is required."""


def parameter(name: str,
              *, required: bool = False,
              data_type: Optional[str] = None,
              description: Optional[str] = None) -> ParameterDescription:
    """A description of one of the processor's parameters.

    Args:
        name (str): The parameter name / key.

    Keyword Args:
        required (bool): Whether the processor parameter is required.
        data_type (~typing.Optional[str]):
            The data type of the parameter. str, float, or bool; List[T] or Mapping[T1, T2] of
            those.
        description (~typing.Optional[str]): A short description of the property and what it does.

    Returns:
        ParameterDescription: The parameter description object
    """
    return ParameterDescription(name=name, description=description, data_type=data_type,
                                required=required)


def _desc_to_dict(description: LabelDescription) -> dict:
    return {
        'name': description.name,
        'name_from_parameter': description.name_from_parameter,
        'reference': description.reference,
        'optional': description.optional,
        'description': description.description,
        'properties': [
            {
                'name': p.name,
                'description': p.description,
                'data_type': p.data_type,
                'nullable': p.nullable
            } for p in description.properties
        ]
    }


def processor(name: str,
              *,
              human_name: Optional[str] = None,
              description: Optional[str] = None,
              parameters: Optional[List[ParameterDescription]] = None,
              inputs: Optional[List[LabelDescription]] = None,
              outputs: Optional[List[LabelDescription]] = None,
              **additional_metadata: str):
    """Decorator which attaches a service name and metadata to a processor. Which then can be used
    for runtime reflection of how the processor works.

    Args:
        name (str):
            Identifying service name both for launching via command line and for service
            registration.

            Should be a mix of alphanumeric characters and dashes so that it plays nice with the
            DNS name requirements of service discovery tools like Consul. Can be overridden at
            runtime via the `identifier` option on :func:`processor_parser`.

    Keyword Args:
        human_name (~typing.Optional[str]): An option human name for the processor.
        description (~typing.Optional[str]): A short description of the processor and what it does.
        parameters (~typing.Optional[~typing.List[ParameterDescription]]):
            The processor's parameters.
        inputs (~typing.Optional[~typing.List[str]]):
            String identifiers for the output from a processor that this processor uses as an input.

            Takes the format "[processor-name]/[output]". Examples would be "tagger:pos_tags" or
            "sentence-detector:sentences".
        outputs (~typing.Optional[~typing.List[LabelDescription]]):
            The label indices this processor outputs.
        **additional_metadata (~typing.Any):
            Any other data that should be added to the processor's metadata, should be serializable
            to yaml and json.

    Returns:
        A decorator to be applied to instances of EventProcessor or DocumentProcessor. This
        decorator attaches the metadata so it can be reflected at runtime.

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
        >>>            description="counts the number of times the letters a and b occur in a document",
        >>>            parameters=[
        >>>                parameter('do_work', required=True, data_type='bool',
        >>>                          description="Whether the processor should do anything.")
        >>>            ],
        >>>            outputs=[
        >>>                label_index('mtap.examples.letter_counts',
        >>>                            properties=[label_property('letter', data_type='str'),
        >>>                                        label_property('count', data_type='int')])
        >>>            ])
        >>> class ExampleProcessor(DocumentProcessor):
        >>>     ...


    """
    if parameters is None:
        parameters = []
    if inputs is None:
        inputs = []
    if outputs is None:
        outputs = []

    def decorator(f: Type['EventProcessor']) -> Type['EventProcessor']:
        f.metadata['name'] = name
        f.metadata['human_name'] = human_name
        f.metadata['description'] = description
        f.metadata['parameters'] = [{
            'name': p.name,
            'description': p.description,
            'data_type': p.data_type,
            'required': p.required
        } for p in parameters]
        f.metadata['inputs'] = [_desc_to_dict(desc) for desc in inputs]
        f.metadata['outputs'] = [_desc_to_dict(desc) for desc in outputs]
        if additional_metadata is not None:
            f.metadata.update(additional_metadata)
        return f

    return decorator
