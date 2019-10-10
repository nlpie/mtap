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
"""Converts brat .ann/.txt pairs into serialized events."""
from argparse import ArgumentParser, Namespace
from pathlib import Path

from mtap.io.brat import read_brat_documents
from mtap.io.serialization import get_serializer


class BratConverter(Namespace):
    """Reads brat documents and writes them to a file using a serializer.

    Attributes
    ----------
    input_dir: str
        The input directory
    output_dir: str
        The output directory.
    serializer: Serializer
        The serializer to use.
    events_address: str
        The address of the events service.
    document_name: str
        The document name to store the BRAT text and annotations.


    """
    def convert_files(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for event in read_brat_documents(self.input_dir, document_name=self.document_name,
                                         label_index_name_prefix=self.label_index_name_prefix,
                                         encoding=self.input_encoding,
                                         create_indices=self.create_indices):
            output_path = self.output_dir.joinpath(event.event_id + self.serializer.extension)
            self.serializer.event_to_file(event, output_path)


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument('input_dir', type=Path,
                        help="The input directory of BRAT .ann and .txt files")
    parser.add_argument('output_dir', type=Path,
                        help="The output directory of serialized files.")
    parser.add_argument('create_indices', nargs='*', default=[],
                        help='Indices to create, even if empty.')
    parser.add_argument('--serializer', type=get_serializer, default='json')
    parser.add_argument('--events-address', default=None,
                        help='Address of the events service to use.')
    parser.add_argument('--document-name', default='plaintext',
                        help='The document on the event to create and read brat documents into.')
    parser.add_argument('--label-index-name-prefix', default='',
                        help='A string to prefix the brat annotation types before creating label '
                             'indices.')
    parser.add_argument('--input-encoding', default=None,
                        help='The encoding of the input BRAT files.')

    converter = parser.parse_args(args=args, namespace=BratConverter())
    converter.convert_files()


if __name__ == '__main__':
    main()
