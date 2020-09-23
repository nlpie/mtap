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
"""Tutorial hello world processor."""
import mtap


@mtap.processor('hello')
class HelloProcessor(mtap.DocumentProcessor):
    def process_document(self, document, params):
        with document.get_labeler('hello') as add_hello:
            text = document.text
            add_hello(0, len(text), response='Hello ' + text + '!')


if __name__ == '__main__':
    mtap.run_processor(HelloProcessor())
