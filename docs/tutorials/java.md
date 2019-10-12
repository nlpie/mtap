---
layout: doc
subpage: Documentation
title: Java Tutorial
description: Getting started using the MTAP Java SDK.
---

## Requirements

- Python 3.5 or later
- Oracle or OpenJDK JDK 8

## Installing MTAP

The Java SDK for MTAP does not need to be installed, it is distributed as
a Jar. Eventually a distribution will be made public on Maven Central for
inclusion in Maven and Gradle projects.

We will need to install the MTAP Python SDK, which includes the events
service necessary to run our processor.

```bash
pip install mtap-{{ site.python_version }}.tar.gz
```


## Creating a processor

We will be creating a document processor which simply writes a hello world
label to a document.

To start, create a file named ``Hello.java``, this file will contain our
processor:

```java
import edu.umn.nlpie.mtap.common.*;
import edu.umn.nlpie.mtap.model.*;
import edu.umn.nlpie.mtap.processing.*;

import org.kohsuke.args4j.*;

@Processor("hello")
public class Hello extends DocumentProcessor {
  @Override
  protected void process(Document document, JsonObject params, JsonObjectBuilder result) {
    try (Labeler<GenericLabel> labeler = document.getLabeler("hello")) {
      String text = document.getText();
      labeler.add(
          GenericLabel.withSpan(0, text.length()).setProperty("response", "Hello " + text + "!")
      );
    }
  }

  public static void main(String[] args) {
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    try {
      parser.parseArgument(args);
      Server server = ProcessorServerBuilder.forProcessor(new HelloWorldExample(), options).build();
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

Note use of the try-with-resources statement: ``try () {}``. This block will
cause the labeler to upload any added labels to the events service when exited.


## Compiling the processor

To compile the processor, run:

```bash
javac -cp mtap-all-{{ site.version }}.jar Hello.java
```


## Running the processor

First, we will need to launch the python events service.

```bash
python -m mtap events -p 9090
```

Now we can deploy our Java processor. In another terminal run:

```bash
java -cp .:mtap-all-{{ site.version }}.jar Hello -p 9092 -e localhost:9090
```

To perform processing you will either need to create a python pipeline file, or
use the [API Gateway]({{ '/docs/tutorials/api-gateway.html' | relative_url }})

### Creating python pipeline file

To perform processing, create another file ``pipeline.py``:

```python
from mtap import Document, Event, EventsClient, Pipeline, RemoteProcessor

with EventsClient(address='localhost:9090') as client, \
     Pipeline(
         RemoteProcessor(processor_id='hello', address='localhost:9092')
     ) as pipeline:
  with Event(event_id='1', client=client) as event:
    document = Document(document_name='name', text='YOUR NAME')
    event.add_document(document)
    pipeline.run(document)
    index = document.get_label_index('hello')
    for label in index:
      print(label.response)
```

To run this pipeline type

```bash
python pipeline.py
```

## Interacting with the events service

When you deploy the processor above, the MTAP framework wraps that processor
in a gRPC service and server. When it receives a request, it uses the request
parameters to instantiate the ``Document`` object that gets passed to your
processor. This ``Document`` object is your interface to the events service.

For more information about the methods that are available, see the
[API Documentation]({{'/api/javadoc/edu/umn/nlpie/mtap/Document.html' | relative_url }}).
