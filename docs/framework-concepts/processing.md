---
layout: default
title: Processing
parent: Framework Concepts
nav_order: 2
---

# Processing

The patterns for implementing and running text analysis in the MTAP Framework.

## Processor

A processor is a component which performs some kind of task on the data in an
 ``Event`` or a ``Document``. MTAP provides functionality for deploying and
 running these processors.

In MTAP there are two types of processors:

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
    for sentence in document.labels['sentences']:
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

### Hosting Processors

In order to facilitate interoperability between components of different 
languages, as well as scalability and flexibility of the how components are 
deployed, MTAP uses a distributed system, microservice-inspired approach for
processing.

Each component is wrapped by the MTAP framework and hosted using a 
standardized gRPC service definition.

#### Python
```python
from mtap import run_processor

processor = ExampleProcessor()
run_processor(processor)
```

#### Java
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

In both of these languages a standardized argument parser is provided which 
allows customization of how the processors are hosted, for example the 
hostname and port of the processor service.

## Pipelines

A pipeline is a class for calling one or more processors in succession. The 
pipeline handles all of the communication with the pipeline 
components.

#### Python
```python
pipeline = Pipeline(
    RemoteProcessor('processor1', address='localhost:10001'),
    RemoteProcessor('processor2', address='localhost:10002')
)
with events_client(address='localhost:10000') as client:
  with Event(event_id='1', client=client) as event:
    document = Document(document_name='plaintext', text=document_text)
    event.add_document(document)
    pipeline.run(document)
```

The pipeline also has a dictionary-based specification, so a pipeline can be 
created by loading a serialized file. This allows sharing and customization of 
pipelines via configuration.

```yaml
name: example-pipeline
components:
    - name: processor1
      address: 'localhost:10001'
    - name: processor2
      address: 'localhost:10002'
```

```python
pipeline = Pipeline.from_yaml("/path/to")
with events_client(address='localhost:10000') as client:
  with Event(event_id='1', client=client) as event:
    document = Document(document_name='plaintext', text=document_text)
    event.add_document(document)
    pipeline.run(document)
```
