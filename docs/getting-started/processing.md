---
layout: doc
title: Processing
subpage: Documentation
description: How processing documents works using MTAP.
---

## Processor

A processor is a component which performs some kind of task on the data in an
 ``Event`` or a ``Document``. MTAP provides functionality for deploying and
 running these processors.

## Introduction

In MTAP there are two types of processing components:

- EventProcessor
- DocumentProcessor

### EventProcessor

Event processors perform processing on ``Event`` objects, potentially using
multiple ``Document`` objects on that ``Event``. Examples would be translating
one language ``Document`` into another, cross-analyzing or creating references
between more than one document, or summarizing a document.

#### Python

```python
from mtap import processor, EventProcessor

@processor('example-event-processor')
class ExampleProcessor(EventProcessor):
  def process(self, event, params):
    doc1 = event.documents['english']
    doc2 = event.create_document('spanish', translate(doc1.text))
```

#### Java

```java
import edu.umn.nlpie.mtap.common.*;
import edu.umn.nlpie.mtap.model.*;
import edu.umn.nlpie.mtap.processing.*;

@Processor("example-event-processor")
public class ExampleProcessor extends EventProcessor {
  public void process(Event event,
                      JsonObject params,
                      JsonObjectBuilder result) {
    Document doc1 = event.getDocuments().get("english");
    Document doc2 = event.addDocument("spanish", translate(doc1.getText()));
  }
}
```

### DocumentProcessor

Document processors perform processing on a specific ``Document`` object on an
``Event``. Examples would be most standard NLP tasks like sentence segmentation,
part of speech tagging, parsing, normalization, negation, or entity detection.

In this example, assuming that the "sentences" label index has been created by
another processor, we can then access the sentences even running this processor
on a different machine:

#### Python

```python
from mtap import DocumentProcessor, processor

@processor('example-document-processor')
class ExampleProcessor(DocumentProcessor):
  def process_document(self, document, params):
    for sentence in document.get_label_index('sentences'):
      # do processing on sentence
```

#### Java

```java
import edu.umn.nlpie.mtap.common.*;
import edu.umn.nlpie.mtap.model.*;
import edu.umn.nlpie.mtap.processing.*;

@Processor("example-document-processor")
public class ExampleProcessor extends EventProcessor {
  public void process(Document document,
                      JsonObject params,
                      JsonObjectBuilder result) {
    for (GenericLabel label : document.getLabelIndex("sentences")) {

    }
  }
}
```

### Running

Either a ``Pipeline`` object or the API gateway can be used to trigger
processing. MTAP handles creating a ``Event`` or ``Document`` object
from the ``event_id`` and ``document_name`` identifiers in a gRPC processing
request, and then calling the processor with that object as a parameter.

The MTAP framework provides functionality that takes a processor object and
wraps it in a gRPC service that responds to specific processing end-points.
When the processing end-point is called, MTAP adapts the processing
arguments.

#### Python
Pipeline:
```python

with EventsClient(address='localhost:10000') as client, \
     Pipeline(
       RemoteProcessor('example-document-processor', address='localhost:10001')
     ) as pipeline:
  with Event(event_id='1', client=client) as event:
    document = Document(document_name='plaintext', text=document_text)
    event.add_document(document)
    pipeline.run(document)
```

Hosting a processor:
```python
from mtap import run_processor

processor = ExampleProcessor()
run_processor(processor)
```

#### Java
Hosting a processor:
```java
import edu.umn.nlpie.mtap.processing.ProcessorServerBuilder;
import edu.umn.nlpie.mtap.processing.ProcessorServerOptions;
import edu.umn.nlpie.mtap.common.Server;

import org.kohsuke.args4j.*;

import java.io.IOException;

...

class ExampleProcessor ... {
  ...
  public static void main(String[] args) {
    ProcessorServer.Builder builder = new ProcessorServer.Builder();
    CmdLineParser parser = new CmdLineParser(builder);
    try {
      parser.parseArgument(args);
      Server server = builder.build(new ExampleProcessor());
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    } catch (CmdLineException e) {
      ProcessorServerOptions.printHelp(parser, HelloWorldExample.class, e, null);
    }
  }
}

```
