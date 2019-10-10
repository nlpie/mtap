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

from typing import Dict, Any, Optional

import mtap
from mtap.events import Document
from mtap.processing import DocumentProcessor, run_processor
from mtap.processing.descriptions import label_index, label_property, parameter


@mtap.processor('mtap-example-processor-python',
                description='counts the number of times the letters a and b occur in a document',
                parameters=[
                       parameter('do_work', required=True, data_type='bool',
                                 description="Whether the processor should do anything.")
                   ],
                outputs=[
                       label_index('mtap.examples.letter_counts',
                                   properties=[label_property('letter', data_type='str'),
                                               label_property('count', data_type='int')])
                   ])
class ExampleProcessor(DocumentProcessor):
    """Does some labeling of the counts of the letter 'a' and 'b' in a document.
    """

    def process_document(self,
                         document: Document,
                         params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if params['do_work']:
            with self.started_stopwatch('fetch_time'):
                text = document.text

            a_count = text.count('a')
            b_count = text.count('b')

            with document.get_labeler('mtap.examples.letter_counts') as label_letter_count:
                label_letter_count(start_index=0, end_index=len(document.text), letter='a',
                                   count=a_count)
                label_letter_count(start_index=0, end_index=len(document.text), letter='b',
                                   count=b_count)

        return {'answer': 42}


if __name__ == '__main__':
    run_processor(ExampleProcessor())
