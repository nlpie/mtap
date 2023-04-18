---
layout: default
title: Serialization
parent: Tutorials
nav_order: 4
---
# Serialization
Built-in functionality for saving documents as JSON.

MTAP has functionality for serializing events to and from JSON files.

## Serializing to JSON files

The code below shows how to serialize an individual event to a file using a 
Serializer class.

```python
from mtap import Event
from mtap.serialization import JsonSerializer

with Event(event_id="1") as event:
    event.create_document(
      'plaintext', 
      "The quick brown fox jumps over the lazy dog."
    )
    JsonSerializer.event_to_file(event, "/path/to/file.json")
```

In addition to the json serializer, there are also serializers for yaml and 
pickle built in to MTAP.

## Serializing in a pipeline

The code below shows how to run an MTAP pipeline of remote processors, then
serialize the results to a JSON file.

```python
from mtap import events_client, Event, Pipeline, RemoteProcessor, LocalProcessor
from mtap.serialization import JsonSerializer, SerializationProcessor

serialization_processor = SerializationProcessor(
  JsonSerializer, 
  output_dir="/path/to/output"
)
pipeline = Pipeline(
    RemoteProcessor('example-1', address='localhost:9091'),
    RemoteProcessor('example-2', address='localhost:9092'),
    LocalProcessor(serialization_processor),
    events_address='localhost:9090'
)
with events_client('localhost:9090') as events:
    with Event(event_id="1", client=events) as event:
        doc = event.create_document(
          'plaintext', 
          "The quick brown fox jumps over the lazy dog."
        )
        pipeline.run(doc)
```


## Deserializing from JSON files

The code below shows how to deserialize a saved json event and then run a
pipeline on that event.

```python
from mtap import Pipeline, RemoteProcessor, EventsClient, LocalProcessor
from mtap.io.serialization import JsonSerializer

with Pipeline(
      RemoteProcessor('example-1', address='localhost:10001'),
      RemoteProcessor('example-2', address='localhost:10002'),
      events_address='localhost:10000'
    ) as pipeline:
  for test_file in input_dir.glob('**/*.json'):
    with JsonSerializer.file_to_event(test_file, 
                                      client=pipeline.events_client) as event:
        document = event.documents['plaintext']
        results = pipeline.run(document)

```

## More info

For more information on serialization in mtap, including how to write your own
serializers, see the 
[API Docs on the subject](https://mtap.readthedocs.io/en/stable/serialization.html).
