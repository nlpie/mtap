#  Copyright 2019 Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from mtap import Event, label
from mtap.io.serialization import event_to_dict

text = "It seems that perfection is attained not when there is nothing more to add, but when " \
       "there is nothing more to remove."

tokens = [(0, 2), (3, 8), (9, 13), (14, 24), (25, 27), (28, 36), (37, 40), (41, 45), (46, 51),
          (52, 54), (55, 62), (63, 67), (68, 70), (71, 74), (76, 79), (80, 84), (85, 90), (91, 93),
          (94, 101), (102, 106), (107, 109), (110, 116)]


def test_event_to_dict_include_label_text():
    event = Event()
    doc = event.create_document('plaintext', text)
    doc.add_labels('sentences', [label(0, 117)])
    doc.add_labels('tokens', [label(start, end) for start, end in tokens])

    d_event = event_to_dict(event, include_label_text=True)
    d_doc = d_event['documents']['plaintext']
    d_sentences = d_doc['label_indices']['sentences']
    assert d_sentences['json_labels'][0]['_text'] == text
    d_tokens = d_doc['label_indices']['tokens']['json_labels']
    for i, token in enumerate(d_tokens):
        assert token['_text'] == text[tokens[i][0]:tokens[i][1]]
