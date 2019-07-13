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
from nlpnewt.events import Event, Document

from nlpnewt.labels import GenericLabel

from nlpnewt.processors.copy_document import CopyDocument


def test_copy_document():
    e = Event()
    doc = Document(document_name='first', text='The quick brown fox jumped over the lazy dog.')
    e.add_document(doc)
    with doc.get_labeler('some_index') as label:
        label(0, 3, word='The')
        label(4, 9, word='quick')
        label(10, 15, word='brown')
    processor = CopyDocument('first', 'second')
    processor.process(e, {})
    second = e['second']
    assert second is not None
    assert second.get_label_index('some_index') == [
        GenericLabel(0, 3, word='The'),
        GenericLabel(4, 9, word='quick'),
        GenericLabel(10, 15, word='brown')
    ]
