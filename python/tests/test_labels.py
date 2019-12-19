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
import pytest

from mtap import Location, Document, GenericLabel


def test_location_equals():
    assert Location(1, 3) == Location(1, 3)


def test_text_from_document():
    d = Document('plaintext', text='This is text.')
    assert GenericLabel(5, 7, document=d).text == 'is'


def test_label_location():
    l = GenericLabel(0, 10)
    assert l.location == Location(0, 10)
