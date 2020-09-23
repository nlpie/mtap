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
import argparse
import typing

import mtap


__all__ = [
    'copy_document', 'CopyDocument', 'main'
]


def copy_document(event: mtap.Event,
                  source_document_name: str,
                  target_document_name: str,
                  index_names: typing.Sequence[str] = ...):
    """Copies one document to another on the same event.

    Parameters
    ----------
    event: Event
        The event.
    source_document_name: str
        The source document name.
    target_document_name: str
        The target document name.
    index_names: Sequence[str]
        If specified will only copy the specified label indices, by default all indices will be
        copied.
    """
    source_document = event.documents[source_document_name]
    target_document = mtap.Document(target_document_name, text=source_document.text)
    event.add_document(target_document)
    if index_names is ...:
        index_names = list(source_document.labels)
    for index_name in index_names:
        index = source_document.labels[index_name]
        target_document.add_labels(index_name, index, distinct=index.distinct)


@mtap.processor('mtap-copy-processor')
class CopyDocument(mtap.EventProcessor):
    """Copies one document to another.

    Parameters
    ----------
    source_document_name: str
        The source document name.
    target_document_name: str
        The target document name.
    index_names: Sequence[str]
        If specified will only copy the specified label indices, by default all indices will be
        copied.
    """

    def __init__(self,
                 source_document_name: str,
                 target_document_name: str,
                 index_names: typing.Sequence[str] = ...):
        self.source_document_name = source_document_name
        self.target_document_name = target_document_name
        self.index_names = index_names

    def process(self, event: mtap.Event, params: typing.Dict[str, typing.Any]):
        copy_document(event, self.source_document_name, self.target_document_name, self.index_names)


def main(args=None):
    parser = argparse.ArgumentParser(
        description='Deploys a processor that copies one document to another.',
        parents=[mtap.processor_parser()]
    )
    parser.add_argument('--index-names', nargs='*', metavar='INDEX_NAME', default=...,
                        help='')
    parser.add_argument('source_document_name', metavar='SOURCE_NAME',
                        help='Name of source document.')
    parser.add_argument('target_document_name', metavar='TARGET_NAME',
                        help='Name of target document.')
    ns = parser.parse_args(args)
    p = CopyDocument(ns.source_document_name, ns.target_document_name, ns.index_names)
    mtap.run_processor(p, namespace=ns)


if __name__ == '__main__':
    main()
