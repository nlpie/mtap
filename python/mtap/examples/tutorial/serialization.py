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
"""Hello world tutorial pipeline.

This example is on the MTAP documentation website, if it stops working please update the associated documentation file
at ``docs/tutorials/serialization.md``.
"""


def serialize():
    from mtap import Event
    from mtap.serialization import JsonSerializer

    with Event(event_id="1") as event:
        event.create_document('plaintext', "The quick brown fox jumps over the lazy dog.")
        JsonSerializer.event_to_file(event, "/path/to/file.json")


def serialize_in_pipeline():
    from mtap import events_client, Event, Pipeline, RemoteProcessor, LocalProcessor
    from mtap.serialization import JsonSerializer, SerializationProcessor

    serialization_processor = SerializationProcessor(JsonSerializer, output_dir="/path/to/output")
    pipeline = Pipeline(
        RemoteProcessor('example-1', address='localhost:9091'),
        RemoteProcessor('example-2', address='localhost:9092'),
        LocalProcessor(serialization_processor),
        events_address='localhost:9090'
    )
    with events_client('localhost:9090') as events:
        with Event(event_id="1", client=events) as event:
            doc = event.create_document('plaintext', "The quick brown fox jumps over the lazy dog.")
            pipeline.run(doc)


def deserialize():
    from pathlib import Path

    from mtap.serialization import JsonSerializer

    for test_file in Path("/path/to/jsons").glob('**/*.json'):

        with JsonSerializer.file_to_event(test_file) as event:  # noqa: F841
            pass  # do what you need with the event
