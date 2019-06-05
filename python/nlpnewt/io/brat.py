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
from pathlib import Path
from typing import Union, Iterable, Optional

from nlpnewt.events import Event, Events, Document


def read_brat_documents(directory: Union[Path, str],
                        events: Events,
                        document_name: str = 'plaintext',
                        label_index_name_prefix: str = '',
                        encoding: Optional[str] = None) -> Iterable[Event]:
    """Reads a directory full of BRAT-annotated ".txt" and ".ann" files, creating events for each
    .txt containing labels created from the annotations in its ".ann" counterpart.

    Parameters
    ----------
    directory: Path or str
        The directory containing the files or sub-directories containing the files.
    events: Events
        The client to the events server to add the documents to.
    document_name: str
        The document name to create on each event containing the brat data.
    label_index_name_prefix: str
        A prefix to append to the brat annotation names.
    encoding: optional str
        The encoding to use when reading the files.


    Returns
    -------
    Iterable of Event
        Iterable of all the events in the

    Examples
    --------
    >>> for event in read_brat_documents('docs', events):
    >>>   with event:
    >>>      # use event

    """
    directory = Path(directory)
    for txt_file in directory.glob('**/*.txt'):
        yield read_brat_document(txt_file, events=events, document_name=document_name,
                                 label_index_name_prefix=label_index_name_prefix, encoding=encoding)


def read_brat_document(txt_file: Union[Path, str],
                       events: Events,
                       document_name: str = 'plaintext',
                       label_index_name_prefix: str = '',
                       encoding: Optional[str] = None) -> Event:
    """Reads a BRAT .txt and .ann file pair into an Event.

    Parameters
    ----------
    txt_file
    events: Events
        The client to the events server to add the documents to.
    document_name: str
        The document name to create on the event to hold the brat data.
    label_index_name_prefix: str
        A prefix to append to the brat annotation names.
    encoding: optional str
        The encoding to use when reading the files.

    Returns
    -------
    Event
        An event containing the text and annotations as labels.

    """
    txt_file = Path(txt_file)
    ann_file = txt_file.with_suffix('.ann')
    event = events.create_event(event_id=str(txt_file))
    with txt_file.open('r', encoding=encoding) as f:
        txt = f.read()
    document = event.add_document(document_name=document_name, text=txt)
    ann_to_labels(ann_file, document, label_index_name_prefix=label_index_name_prefix,
                  encoding=encoding)
    return event


def ann_to_labels(ann_file: Union[str, Path],
                  document: Document,
                  label_index_name_prefix: str,
                  encoding: Optional[str]):
    """Reads all of the annotations in a brat annotations file into a document.

    Parameters
    ----------
    ann_file: str or Path
        A BRAT .ann file to load annotations from.
    document: Document
        The document to add labels to.
     label_index_name_prefix: str
        A prefix to append to the brat annotation names.
    encoding: optional str
        The encoding to use when reading the ann file.
    """
    labelers = {}
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
