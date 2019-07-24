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
"""Hello world tutorial pipeline."""
import sys

if __name__ == '__main__':
    from nlpnewt import Document, Event, EventsClient, Pipeline, RemoteProcessor

    with EventsClient(address=sys.argv[1]) as client, \
            Pipeline(
                RemoteProcessor(processor_id='hello', address=sys.argv[2])
            ) as pipeline:
        with Event(event_id='1', client=client) as event:
            document = Document(document_name='name', text='YOUR NAME')
            event.add_document(document)
            pipeline.run(document)
            index = document.get_label_index('hello')
            for label in index:
                print(label.response)
