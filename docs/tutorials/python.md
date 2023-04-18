---
layout: default
title: "Getting Started - Python"
parent: Tutorials
nav_order: 1
---

# Getting Started - Python
How to use Python to create a DocumentProcessor.

## Requirements

- Python {{ site.min_python }}+

## Installing mtap

To install mtap run the following:

```bash
pip install mtap
```

## Creating a processor


We will be creating a document processor which simply writes a hello world 
label to a document.

To start, create a file named ``hello.py``, this file will contain our 
processor:

```python
from mtap import DocumentProcessor, run_processor


class HelloProcessor(DocumentProcessor):
    def process_document(self, document, params):
        with document.get_labeler('hello') as add_hello:
            text = document.text
            add_hello(0, len(text), response='Hello ' + text + '!')


if __name__ == '__main__':
    run_processor(HelloProcessor())
```

This file receives a request to process a document, and then labels that 
document's text with a hello response.

## Running the processor

To host the processor, run the following commands in terminal windows.

```bash
python -m mtap events -p 9090 &
python hello.py -p 9091 -e localhost:9090 &
```

To perform processing, create another file ``pipeline.py``:

```python
import sys

if __name__ == '__main__':
    from mtap import Document, Event, Pipeline, events_client
    from mtap import RemoteProcessor

    pipeline = Pipeline(
        RemoteProcessor(processor_name='helloprocessor', address=sys.argv[2]),
    )
    with events_client(sys.argv[1]) as client:
        with Event(event_id='1', client=client) as event:
            document = Document(document_name='name', text='YOUR NAME')
            event.add_document(document)
            pipeline.run(document)
            index = document.labels['hello']
            for label in index:
                print(label.response)
```

To run this pipeline type

```bash
python pipeline.py localhost:9090 localhost:9091
```

## Interacting with the Events Service

When you deploy the processor above, the MTAP framework hosts the processor as
a gRPC service that can be contacted to process documents. When it receives a
request, it uses the request parameters to instantiate the ``Document`` object
that gets passed to your processor. This ``Document`` object is your interface
to the events service.

For more information about the methods that are available, see the
[API Documentation](https://mtap.readthedocs.io/en/stable/mtap.html#mtap.Document).

## Cleaning up

When you launched the events service and the processor above in the background
it should have gave you a job number and pid (process id) ``[<job_no>] <pid>``. Example:

```bash
$ python -m mtap events -p 9090 &
[1] 75106
$ python hello.py -p 9091 -e localhost:9090 &
[2] 75214
```

You can close those background jobs like this:

```bash
kill %1 %2
```
