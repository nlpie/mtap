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
"""Tools for reading in files annotated using BRAT (https://brat.nlplab.org/)."""

from contextlib import contextmanager
from pathlib import Path
from typing import Union, Iterable, Optional

from mtap._document import Document
from mtap._event import Event
from mtap._events_client import EventsClient

__all__ = [
    'ann_to_labels',
    'read_brat_document',
    'read_brat_documents',
]


def read_brat_documents(
        directory: Union[Path, str],
        client: Optional[EventsClient] = None,
        document_name: str = 'plaintext',
        label_index_name_prefix: str = '',
        encoding: Optional[str] = None,
        create_indices: Optional[Iterable[str]] = None
) -> Iterable[Event]:
    """Reads a directory full of BRAT-annotated ".txt" and ".ann" files,
    creating events for each .txt containing labels created from the
    annotations in its ".ann" counterpart.

    Args:
        directory: The directory containing the files or subdirectories
            containing the files.
        client: The client to the events server to add the documents to.
        document_name: The document name to create on each event containing
            the brat data.
        label_index_name_prefix: A prefix to append to the brat annotation
            names.
        encoding: The encoding to use when reading the files.
        create_indices: These indices will be created no matter what,
            even if empty.

    Returns:
        Iterable of all the events from the directory of brat documents.

    Examples:
        >>> client = mtap.EventsClient()
        >>> for event in read_brat_documents('docs', client=client):
        >>>   with event:
        >>>      # use event

    """
    directory = Path(directory)
    for txt_file in directory.glob('**/*.txt'):
        with read_brat_document(txt_file, client=client,
                                document_name=document_name,
                                label_index_name_prefix=label_index_name_prefix,
                                encoding=encoding,
                                relative_to=directory,
                                create_indices=create_indices) as event:
            yield event


@contextmanager
def read_brat_document(txt_file: Union[Path, str],
                       client: Optional[EventsClient] = None,
                       document_name: str = 'plaintext',
                       label_index_name_prefix: str = '',
                       encoding: Optional[str] = None,
                       relative_to: Optional[Union[Path, str]] = None,
                       create_indices: Optional[
                           Iterable[str]] = None) -> Event:
    """Reads a BRAT .txt and .ann file pair into an Event.

    Args:
        txt_file: The path to the .txt file.
        client: The client to the events server to add the documents to.
        document_name: The document name to create on the event to hold the
            brat data.
        label_index_name_prefix: A prefix to append to the brat annotation
            names.
        encoding: The encoding to use when reading the files.
        relative_to: A str of a path or a Path object for which the event_id
            will be relative to, if this is omitted then the file's name
            without extension will be used.
        create_indices: These indices will be created no matter what,
            even if empty.

    Returns:
        An event containing the text and annotations as labels.

    """
    txt_file = Path(txt_file)
    ann_file = txt_file.with_suffix('.ann')
    if relative_to is not None:
        relative_to = Path(relative_to)
        event_id = str(txt_file.with_suffix('').relative_to(relative_to))
    else:
        event_id = txt_file.stem
    with Event(event_id=event_id, client=client) as event:
        with txt_file.open('r', encoding=encoding) as f:
            txt = f.read()
        document = event.create_document(document_name=document_name, text=txt)
        ann_to_labels(ann_file, document,
                      label_index_name_prefix=label_index_name_prefix,
                      encoding=encoding, create_indices=create_indices)
        yield event


def ann_to_labels(ann_file: Union[str, Path],
                  document: Document,
                  label_index_name_prefix: str,
                  encoding: Optional[str],
                  create_indices: Optional[Iterable[str]] = None):
    """Reads all the annotations in a brat annotations file into a document.

    Args:
        ann_file: A BRAT .ann file to load annotations from.
        document: The document to add labels to.
        label_index_name_prefix: A prefix to append to the brat annotation
            names.
        encoding: The encoding to use when reading the ann file.
        create_indices: These indices will be created no matter what,
            even if empty.
    """
    labelers = {}
    if create_indices is not None:
        for index in create_indices:
            labelers[index] = document.get_labeler(index)
    ann_file = Path(ann_file)
    with ann_file.open('r', encoding=encoding) as f:
        for line in f.readlines():
            splits = line.split('\t')
            if len(splits) < 3 or not splits[0].startswith('T'):
                continue
            name, bounds = splits[1].split(' ', maxsplit=1)
            name = label_index_name_prefix + name
            bounds = bounds.split(';')
            min_start = float('Inf')
            max_end = 0
            for pair in bounds:
                start_index, end_index = pair.split(' ')
                min_start = min(min_start, int(start_index))
                max_end = max(max_end, int(end_index))
            try:
                labeler = labelers[name]
            except KeyError:
                labeler = document.get_labeler(name)
                labelers[name] = labeler
            labeler(min_start, max_end)
    for labeler in labelers.values():
        labeler.done()
