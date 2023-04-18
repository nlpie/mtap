---
layout: default
title: "Getting Started - Java"
parent: Tutorials
nav_order: 2
---

## Requirements

- Python {{ site.min_python }}+
- Java JDK {{ site.min_java }}+

## Installing MTAP

To install mtap you will need to using something that supports Maven dependency
management. We use the [Gradle Build Tool](https://gradle.org/). See their
[getting started guide](https://docs.gradle.org/current/samples/sample_building_java_applications.html)
and [MTAP on Maven Central](https://mvnrepository.com/artifact/edu.umn.nlpie/mtap).

We will need to install the MTAP Python SDK, which includes the events
service and pipeline necessary to run our processor.

```bash
pip install mtap
```

## Creating a processor

We will be creating a document processor which simply writes a "hello world"
label to a document.

To start, create a file named ``Hello.java`` in the main source folder
(``src/main/java`` in gradle), thi file will contain our processor:

```java
import edu.umn.nlpie.mtap.common.*;
import edu.umn.nlpie.mtap.model.*;
import edu.umn.nlpie.mtap.processing.*;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;

import java.io.IOException;

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
    ProcessorServer.Builder options = new ProcessorServer.Builder();
    CmdLineParser parser = new CmdLineParser(options);
    try {
      parser.parseArgument(args);
      Server server = options.build(new HelloWorldExample());
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    } catch (CmdLineException e) {
      ProcessorServer.Builder.printHelp(parser, HelloWorldExample.class, e, null);
    }
  }
}
```

Note the use of the try-with-resources statement: ``try () {}``. This block will
cause the labeler to upload any added labels to the events service when exited.


## Compiling the processor

To compile the processor, check the documentation for your build system, in 
gradle it's:

```
gradle build
```

## Creating a task for running the processor

In gradle, a task for running the processor can be created by adding the 
following to the build.gradle file

```groovy
task runClass(type: JavaExec) {
  classpath = sourceSets.main.runtimeClasspath

  mainClass findProperty('mainClass')

  // arguments to pass to the application
  args findProperty('args')
}
```

## Running the processor

First, we will need to launch the python events service.

```bash
python -m mtap events -p 9090 &
gradle runClass -PmainClass=Hello -Pargs="-p 9091 -e localhost:9090
```

To perform processing you will either need to create a python pipeline file, or
use the [API Gateway]( api-gateway ).

### Creating python pipeline file

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
python pipeline.py
```

## Interacting with the events service

When you deploy the processor above, the MTAP framework wraps that processor
in a gRPC service and server. When it receives a request, it uses the request
parameters to instantiate the ``Document`` object that gets passed to your
processor. This ``Document`` object is your interface to the events service.

For more information about the methods that are available, see the
[API Documentation](https://mtap.readthedocs.io/en/stable/mtap.html#mtap.Document).
