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
from typing import NamedTuple, Optional, List, Type, Dict, Any

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
PropertyDescription.__doc__ = '''A description of a property of the labels on a label index.'''
PropertyDescription.name.__doc__ = '''str: The property's variable name.'''
PropertyDescription.description.__doc__ = '''optional str: A short description of the property.'''
PropertyDescription.data_type.__doc__ = '''optional str: The data type of the property: str, float, 
or bool; List[T] or Mapping[T1, T2] of those.'''
PropertyDescription.nullable.__doc__ = '''bool: Whether the property can have a valid value of 
null.'''


def label_property(name: str,
                   description: Optional[str] = None,
                   data_type: Optional[str] = None,
                   nullable: bool = False) -> PropertyDescription:
    """Creates a description for a property on a label.

    Parameters
    ----------
    name: str
        The property's name.
    description: optional str
        A short description of the property.
    data_type: optional str
        The data type of the property: str, float, or bool; List[T] or Mapping[T1, T2] of those.
    nullable: bool
        Whether the property can have a valid value of null.

    Returns
    -------
    PropertyDescription
        An object describing a label's property.

    """
    return PropertyDescription(name, description, data_type, nullable)


LabelDescription = NamedTuple('LabelIndexDescription',
                              [('name', str),
                               ('name_from_parameter', Optional[str]),
                               ('optional', bool),
                               ('description', Optional[str]),
                               ('properties', List[PropertyDescription])])
LabelDescription.__doc__ = '''A description of input or output label index.'''
LabelDescription.name_from_parameter.__doc__ = '''optional str: If the label index gets its name 
from a parameter, the name of the parameter.'''
LabelDescription.optional.__doc__ = '''bool: Whether this label index is an optional input or 
output.'''
LabelDescription.name.__doc__ = '''optional str: The label index name.'''
LabelDescription.description.__doc__ = '''optional str:  A short description of the label index.'''
LabelDescription.properties.__doc__ = '''optional list of PropertyDescription: The properties of 
the labels in the label index.'''


def label_index(name: str,
                name_from_parameter: Optional[str] = None,
                optional: bool = False,
                description: Optional[str] = None,
                properties: Optional[List[PropertyDescription]] = None):
    """Creates a description for a label type.

    Parameters
    ----------
    name: str
        The label index name.
    name_from_parameter: optional str
        If the label index gets its name from a parameter, the name of the parameter.
    optional: bool
        Whether this label index is an optional input or output.
    description: optional str
        A short description of the label index.
    properties: optional list of PropertyDescription
        The properties of the labels in the label index.

    Returns
    -------
    LabelDescription
        An object describing a label.

    """
    if properties is None:
        properties = []
    return LabelDescription(name, name_from_parameter, optional, description, properties)


ParameterDescription = NamedTuple('ParameterDescription',
                                  [('name', str),
                                   ('description', Optional[str]),
                                   ('data_type', Optional[str]),
                                   ('required', bool)])
ParameterDescription.__doc__ = '''A description of a processor parameter.'''
ParameterDescription.name.__doc__ = '''str: The parameter name / key.'''
ParameterDescription.description.__doc__ = '''optional str: A short description of the property and 
what it does.'''
ParameterDescription.data_type.__doc__ = '''optional str:  The data type of the parameter. str, 
float, or bool; List[T] or Mapping[T1, T2] of those.'''
ParameterDescription.required.__doc__ = '''bool: Whether the parameter is required.'''


def parameter(name: str,
              required: bool = False,
              data_type: Optional[str] = None,
              description: Optional[str] = None) -> ParameterDescription:
    """A description of a processor's parameters.

    Parameters
    ----------
    name: str
        The parameter name / key.
    required: bool
        Whether the processor parameter is required.
    data_type: optional str
        The data type of the parameter. str, float, or bool; List[T] or Mapping[T1, T2] of those.
    description: optional str
        A short description of the property and what it does.

    Returns
    -------
    ParameterDescription
        The parameter description object

    """
    return ParameterDescription(name=name, description=description, data_type=data_type,
                                required=required)


def _desc_to_dict(description: LabelDescription) -> dict:
    return {
        'name': description.name,
        'name_from_parameter': description.name_from_parameter,
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
              description: Optional[str] = None,
              entry_point: Optional[str] = None,
              language: str = 'python',
              parameters: Optional[List[ParameterDescription]] = None,
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
    entry_point: optional str
        The processor's entry point / main module.
    language: str
        The processor's language.
    parameters: optional list of ParameterDescription
        The processor's parameters.
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
    if parameters is None:
        parameters = []
    if inputs is None:
        inputs = []
    if outputs is None:
        outputs = []

    def decorator(f: Type['EventProcessor']) -> Type['EventProcessor']:
        f.metadata['name'] = name
        f.metadata['description'] = description
        f.metadata['entry_point'] = entry_point
        f.metadata['language'] = language
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
