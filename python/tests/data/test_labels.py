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

from mtap import Location, Document, GenericLabel


def test_location_equals():
    assert Location(1, 3) == Location(1, 3)


def test_text_from_document():
    d = Document('plaintext', text='This is text.')
    assert GenericLabel(5, 7, document=d).text == 'is'


def test_label_location():
    label = GenericLabel(0, 10)
    assert label.location == Location(0, 10)


def test_location_relative_to():
    first = Location(10, 20)
    assert first.relative_to(5) == Location(5, 15)
    assert first.relative_to(GenericLabel(5, 25)) == Location(5, 15)
    assert first.relative_to(Location(5, 25)) == Location(5, 15)


def test_location_offset_by():
    first = Location(0, 5)
    assert first.offset_by(10) == Location(10, 15)
    assert first.offset_by(Location(10, 25)) == Location(10, 15)
    assert first.offset_by(GenericLabel(10, 25)) == Location(10, 15)
