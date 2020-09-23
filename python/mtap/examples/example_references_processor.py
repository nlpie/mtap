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
from typing import Dict, Any

import mtap
from mtap.processing.descriptions import labels


@mtap.processor(
    'mtap-python-references-example',
    human_name='Python References Examples',
    description='Shows use of referential fields on labels.',
    outputs=[
        labels('referenced'),
        labels('map_references'),
        labels('list_references'),
        labels('references')
    ]
)
class ReferencesExampleProcessor(mtap.DocumentProcessor):
    def process_document(self, document: mtap.Document, params: Dict[str, Any]):
        referenced = [
            mtap.GenericLabel(0, 1),
            mtap.GenericLabel(1, 2),
            mtap.GenericLabel(2, 3),
            mtap.GenericLabel(3, 4)
        ]

        # references can be a map of strings to labels
        with document.get_labeler('map_references') as label_map_references:
            label_map_references(0, 4, ref={
                'a': referenced[0],
                'b': referenced[1],
                'c': referenced[2],
                'd': referenced[3]
            })

        # references can be a list of labels
        with document.get_labeler('list_references') as label_list_references:
            label_list_references(0, 2, ref=[referenced[0], referenced[1]])
            label_list_references(2, 3, ref=[referenced[2], referenced[3]])

        # references can be direct
        with document.get_labeler('references') as label_references:
            label_references(0, 2, a=referenced[0], b=referenced[1])
            label_references(2, 3, a=referenced[2], b=referenced[3])

        # referenced labels don't need to be added via "addLabels" or "Labeler.close" before label
        # indices that reference them.
        # The Document will delay uploading any label indices to the server until they are.
        document.add_labels('referenced', referenced)


if __name__ == '__main__':
    mtap.run_processor(ReferencesExampleProcessor())
