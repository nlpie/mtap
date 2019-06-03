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
"""Shared serialization code."""
import logging
from typing import Dict

from nlpnewt.events import Event, Document, LabelIndexType
from nlpnewt.label_indices import LabelIndex
from nlpnewt.labels import GenericLabel

logger = logging.getLogger(__name__)


def event_to_dict(event: Event) -> Dict:
    """Turns the event into a python dictionary.

    Parameters
    ----------
    event: Event
        The event object.

    Returns
    -------
    dict
        A dictionary object suitable for serialization.

    """
    d = {
        'event_id': event.event_id,
        'metadata': {},
        'documents': []
    }
    for k, v in event.metadata.items():
        d['metadata'][k] = v
    for doc in event.values():
        d['documents'].append(document_to_dict(doc))
    return d


def document_to_dict(document: Document) -> Dict:
    """Turns the document into a python dictionary.

    Parameters
    ----------
    document: Document
        The document object.

    Returns
    -------
    dict
        A dictionary object suitable for serialization.

    """
    d = {
        'document_name': document.document_name,
        'text': document.text,
        'label_indices': {}
    }

    for index_info in document.get_label_indices_info():
        if index_info.type == LabelIndexType.OTHER or index_info.type == LabelIndexType.UNKNOWN:
            logger.warning(
                'Index %s of type %s will not be included in serialization.'.format(
                    index_info.index_name, index_info.type.name
                )
            )
            continue
        d['label_indices'][index_info.index_name] = label_index_to_dict(
            document.get_label_index(index_info.index_name)
        )
    return d


def label_index_to_dict(label_index: LabelIndex[GenericLabel]) -> Dict:
    """Turns the label index into a dictionary representation.

    Parameters
    ----------
    label_index: LabelIndex[GenericLabel]
        The label index itself.

    Returns
    -------
    dict
        A dictionary representing the label index.
    """
    d = {
        'json_labels': [label.fields for label in label_index]
    }
    return d
