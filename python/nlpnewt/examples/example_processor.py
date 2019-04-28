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
"""An example document processor."""

import re

import nlpnewt
from nlpnewt.processing import DocumentProcessor

the = re.compile('the', flags=re.I)


@nlpnewt.processor('nlpnewt-example-processor-python')
class ExampleProcessor(DocumentProcessor):
    """Does some labeling of the counts of the letter 'a' and 'b' in a document, and all of the
    times the word 'the' occurs.
    """

    def __init__(self, context: ProcessorContext):
        self.context = context

    def process_document(self, document, params):
        if params['do_work']:
            with nlpnewt.stopwatch('fetch_time'):
                text = document.text

            a_count = text.count('a')
            b_count = text.count('b')

            with document.get_labeler('nlpnewt.examples.letter_counts') as label_letter_count:
                label_letter_count(start_index=0, end_index=len(document.text), letter='a',
                                   count=a_count)
                label_letter_count(start_index=0, end_index=len(document.text), letter='b',
                                   count=b_count)

        return {'answer': 42}
