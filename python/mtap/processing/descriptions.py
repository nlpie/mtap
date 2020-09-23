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
    from mtap import EventProcessor

__all__ = [
    'label_property',
    'labels',
    'parameter',
    'processor',
]


class label_property(NamedTuple('label_property',
                                [('name', str),
                                 ('description', Optional[str]),
                                 ('data_type', Optional[str]),
                                 ('nullable', bool)])):
    """Creates a description for a property on a label.

    Args:
        name (str): The property's name.

    Keyword Args:
        description (~typing.Optional[str]): A short description of the property.
        data_type (~typing.Optional[str]):
            The data type of the property: str, float, or bool; List[T] or Mapping[T1, T2] of those.
        nullable (bool): Whether the property can have a valid value of null.
    """

    def __new__(cls,
                name: str,
                *,
                nullable: bool = False,
                description: Optional[str] = None,
                data_type: Optional[str] = None):
        return super().__new__(cls, name, description, data_type, nullable)


class labels(NamedTuple('LabelDescription',
                        [('name', str),
                         ('reference', Optional[str]),
                         ('name_from_parameter', Optional[str]),
                         ('optional', bool),
                         ('description', Optional[str]),
                         ('properties', List[label_property])])):
    """A description for a label type.

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
        properties (~typing.Optional[~typing.List[label_property]]):
            The properties of the labels in the label index.

    Attributes:
        name (str): The label index name.
        reference (~typing.Optional[str]):
            If this is an output of another processor, that processor's name followed by a slash
            and the default output name of the index go here.
            Example: "sentence-detector/sentences".
        optional (bool): Whether this label index is an optional input or output.
        name_from_parameter (~typing.Optional[str]):
            If the label index gets its name from a processor parameter, the name of the parameter.
        description (~typing.Optional[str]): A short description of the label index.
        properties (~typing.Optional[~typing.List[label_property]]):
            The properties of the labels in the label index.
    """
    def __new__(cls,
                name: str,
                *,
                reference: Optional[str] = None,
                optional: bool = False,
                name_from_parameter: Optional[str] = None,
                description: Optional[str] = None,
                properties: Optional[List[label_property]] = None):
        return super().__new__(cls, name, reference, name_from_parameter, optional, description,
                               properties)


class parameter(NamedTuple('parameter',
                           [('name', str),
                            ('description', Optional[str]),
                            ('data_type', Optional[str]),
                            ('required', bool)])):
    def __new__(cls,
                name: str,
                *,
                required: bool = False,
                data_type: Optional[str] = None,
                description: Optional[str] = None):
        """A description of one of the processor's parameters.

        Args:
            name (str): The parameter name / key.

        Keyword Args:
            required (bool): Whether the processor parameter is required.
            data_type (~typing.Optional[str]):
                The data type of the parameter. str, float, or bool; List[T] or Mapping[T1, T2] of
                those.
            description (~typing.Optional[str]): A short description of the property and what it
                does.

        Attributes:
            name (str): The parameter name / key.
            required (bool): Whether the processor parameter is required.
            data_type (~typing.Optional[str]):
                The data type of the parameter. str, float, or bool; List[T] or Mapping[T1, T2] of
                those.
            description (~typing.Optional[str]): A short description of the property and what it
                does.


        Returns:
            ParameterDescription: The parameter description object
        """
        return super().__new__(cls, name=name, description=description, data_type=data_type,
                               required=required)


def processor(name: str,
              *,
              human_name: Optional[str] = None,
              description: Optional[str] = None,
              parameters: Optional[List[parameter]] = None,
              inputs: Optional[List[labels]] = None,
              outputs: Optional[List[labels]] = None,
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
        >>>                labels('mtap.examples.letter_counts',
        >>>                            properties=[label_property('letter', data_type='str'),
        >>>                                        label_property('count', data_type='int')])
        >>>            ])
        >>> class ExampleProcessor(DocumentProcessor):
        >>>     ...


    """

    def decorator(f: Type['EventProcessor']) -> Type['EventProcessor']:
        f.metadata['name'] = name
        f.metadata['human_name'] = human_name
        f.metadata['description'] = description
        if parameters is not None:
            f.metadata['parameters'] = [_parameter_to_map(p) for p in parameters]
        if inputs is not None:
            f.metadata['inputs'] = [_desc_to_dict(desc) for desc in inputs]
        if outputs is not None:
            f.metadata['outputs'] = [_desc_to_dict(desc) for desc in outputs]
        if additional_metadata is not None:
            f.metadata.update(additional_metadata)
        if 'implementation_lang' not in f.metadata:
            f.metadata['implementation_lang'] = 'Python'
        return f

    return decorator


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
