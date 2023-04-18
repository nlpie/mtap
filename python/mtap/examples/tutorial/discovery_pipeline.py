# Copyright 2023 Regents of the University of Minnesota.
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
"""Example of running a pipeline using service discovery.

This example is on the MTAP documentation website, if it stops working please update the associated documentation file
at ``docs/tutorials/service-discovery.md``.
"""

if __name__ == '__main__':
    from mtap import Document, Event, Pipeline, events_client
    from mtap import RemoteProcessor

    pipeline = Pipeline(
        RemoteProcessor(processor_name='helloprocessor'),
    )
    with events_client() as client:
        with Event(event_id='1', client=client) as event:
            document = Document(document_name='name', text='YOUR NAME')
            event.add_document(document)
            pipeline.run(document)
            index = document.labels['hello']
            for label in index:
                print(label.response)
