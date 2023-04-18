---
layout: default
title: Service Discovery
parent: Tutorials
nav_order: 3
---
# Service Discovery

Using Consul service discovery to automatically register and discover
addresses and ports for MTAP services.

## Requirements

- [Consul](https://consul.io)

## Pre-requisites

Complement either the [Getting Started - Python]( python ) or 
[Getting Started - Java]( java ) tutorial.


## Starting Services using service discovery

Once consul is running, services can be started and registered to consul using
the following commands:

#### Events Service
```bash
python -m mtap events --register
```

#### Python Processor
```bash
python hello.py --register
```

#### Java Processor
```
gradle runClass -PmainClass=Hello -Pargs="--register"
```

## Running pipelines using service discovery

Taken from the
[Getting Started - Python tutorial]( python ), we can
run this pipeline using service discovery by removing the addresses:

```python
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
```
