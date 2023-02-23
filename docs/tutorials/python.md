---
layout: doc
subpage: Documentation
title: Python Tutorial
description: Getting started using the MTAP Python SDK.
---

## Requirements


- Python 3.5 or later

## Installing mtap

To install mtap run the following:

```bash
pip install mtap
```

## Creating a processor


We will be creating a document processor which simply writes a hello world label to a document.

To start, create a file named ``hello.py``, this file will contain our processor:

```python
import mtap


@mtap.processor('hello')
class HelloProcessor(mtap.DocumentProcessor):
    def process_document(self, document, params):
        with document.get_labeler('hello') as add_hello:
            text = document.text
            add_hello(0, len(text), response='Hello ' + text + '!')


if __name__ == '__main__':
    mtap.run_processor(HelloProcessor())
```

This file receives a request to process a document, and then labels that document's text with
a hello response.

## Running the processor

To host the processor, run the following commands in terminal windows (they run in the foreground)

```bash
python -m mtap events -p 9090

python hello.py -p 9091 -e localhost:9090
```

To perform processing, create another file ``pipeline.py``:

```python
from mtap import Document, Event, EventsClient, Pipeline, RemoteProcessor

with Pipeline(
        RemoteProcessor(processor_name='hello', address=sys.argv[2]),
        events_address=sys.argv[1]
) as pipeline:
    with Event(event_id='1', client=pipeline.events_client) as event:
        document = Document(document_name='name', text='YOUR NAME')
        event.add_document(document)
        pipeline.run(document)
        index = document.get_label_index('hello')
        for label in index:
            print(label.response)
```

To run this pipeline type

```bash
python pipeline.py localhost:9090 localhost:9091
```

## Interacting with the Events Service

When you deploy the processor above, the MTAP framework hosts the processor as a gRPC service that can be contacted to process documents. When it receives a request, it uses the request
parameters to instantiate the ``Document`` object that gets passed to your
processor. This ``Document`` object is your interface to the events service.

For more information about the methods that are available, see the
[API Documentation](https://nlpie.github.io/mtap-python-api/mtap.html#mtap.Document).
