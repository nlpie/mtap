#  Copyright 2026 Regents of the University of Minnesota.
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
import grpc

from mtap.processing._runners import RemoteRunner, _group_created_indices


class _Error:
    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code


class _Index:
    def __init__(self, document_name, index_name):
        self.document_name = document_name
        self.index_name = index_name


def _message_for(code):
    runner = RemoteRunner.__new__(RemoteRunner)
    runner._processor_name = 'example-processor'
    return runner._rpc_error_message(_Error(code))


def test_deadline_exceeded_message_names_the_processor():
    message = _message_for(grpc.StatusCode.DEADLINE_EXCEEDED)
    assert message == ('Deadline exceeded waiting for "example-processor" '
                       'to process an event.')


def test_unavailable_message_is_a_complete_sentence():
    # The advice used to be written as bare string literals following the
    # assignment, so it was discarded and the message stopped after "check ".
    message = _message_for(grpc.StatusCode.UNAVAILABLE)
    assert message == ('Failed to connect to "example-processor", check that '
                       'the service is running and the address is correctly '
                       'configured.')


def test_other_codes_have_no_specific_message():
    assert _message_for(grpc.StatusCode.INTERNAL) is None


def test_created_indices_are_grouped_by_document():
    grouped = _group_created_indices([
        _Index('plaintext', 'sentences'),
        _Index('plaintext', 'tokens'),
        _Index('other', 'sentences'),
    ])
    assert grouped == {
        'plaintext': ['sentences', 'tokens'],
        'other': ['sentences'],
    }


def test_created_indices_of_an_empty_response_is_empty():
    assert _group_created_indices([]) == {}
