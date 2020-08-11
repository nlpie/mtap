---
layout: doc
subpage: Documentation
title: Serializing MTAP Events
description: Build in functionality for saving documents as JSON.
---

MTAP has functionality for serializing events to and from JSON files.

## Serializing to JSON files

The code below shows how to run an MTAP pipeline of remote processors, then
serialize the results to a JSON file.

```python
from mtap import EventsClient, Event, Pipeline, RemoteProcessor, LocalProcessor
from mtap.io.serialization import JsonSerializer, SerializationProcessor

with EventsClient(address='localhost:10000') as client, Pipeline(
      RemoteProcessor('example-1', address='localhost:10001'),
      RemoteProcessor('example-2', address='localhost:10002'),
      LocalProcessor(SerializationProcessor(JsonSerializer,
                                            output_dir='path/to/output_dir'),
                     component_id='serialize',
                     client=client)
    ) as pipeline:
  with Event(event_id=path.stem, client=client) as event:
    doc = event.create_document('plaintext', document_text)
    pipeline.run(doc)
```


## Deserializing from JSON files

The code below shows how to deserialize a saved json event and then run a
pipeline on that event.

```python
from mtap import Pipeline, RemoteProcessor, EventsClient, LocalProcessor
from mtap.io.serialization import JsonSerializer

with EventsClient(address='localhost:10000') as client, Pipeline(
      RemoteProcessor('example-1', address='localhost:10001'),
      RemoteProcessor('example-2', address='localhost:10002')
    ) as pipeline:
  for test_file in input_dir.glob('**/*.json'):
    with JsonSerializer.file_to_event(test_file, client=client) as event:
        document = event.documents['plaintext']
        results = pipeline.run(document)

```
