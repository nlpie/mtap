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

from pathlib import Path

from mtap import GenericLabel
from mtap.io.brat import read_brat_documents


def test_read_brat_documents():
    d = Path(__file__).parent / 'brat'
    for event in read_brat_documents(d, document_name='the_gold',
                                     label_index_name_prefix='brat-',
                                     encoding='utf8'):
        doc = event.documents['the_gold']
        assert doc.document_name == 'the_gold'
        sentences = doc.labels['brat-Sentence']
        assert sentences == [
            GenericLabel(2, 26),
            GenericLabel(29, 67),
            GenericLabel(73, 97),
            GenericLabel(100, 138),
            GenericLabel(144, 217),
            GenericLabel(223, 269)
        ]
        unsures = doc.labels['brat-Unsure']
        assert unsures == [
            GenericLabel(2348, 2397)
        ]
