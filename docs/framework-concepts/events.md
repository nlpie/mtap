---
layout: default
title: Data Model
parent: Framework Concepts
nav_order: 1
---

# Data Model

The following article generally describes how documents and the 
artifacts created during processing are represented in the MTAP Framework.

## Event

The top level data object is an ``Event``. An event's primary function is to
store documents, it functions as a dictionary / mapping of names to documents.
Events are stored on a service called the "events service" which stores and
provides the data associated with an event for the lifetime of the event. The
event is primarily identified by a unique ``event_id``.

## Document

A ``Document`` is text and a mapping of names to ``LabelIndex`` objects.


## Label

A label is span of text that the system has assigned some kind of importance or
meaning. Examples could be sentences, part of speech tags, named entities,
sections, identified concepts, or higher level semantic structures.


## LabelIndex

A ``LabelIndex`` is a set of meaningful locations in text and associated
properties. It provides filtering and navigation of its labels, which are
stored as an array sorted by the label's location in text.

Using the event service, MTAP allows processors to retrieve and use labels
created by upstream components.

For concurrency reasons, label indices are immutable once added to a document
and a document's text cannot be modified.


#### Python

```python
for sentence in document.get_label_index('sentences'):
  # do work on the sentence
```

#### Java

```java
for (GenericLabel sentence : document.getLabelIndex("sentences")) {
  // do work on the sentence
}
```

## Labeler

The ``Labeler`` is an object or function that is used to create a new label index
on the document. It collects labels from the processing component and uploads
them to the events service.

#### Python

```python
with document.labeler('sentences') as sentence:
  for sentence in detect_sentences(document.text):
    sentence(sentence.start_index, sentence.end_index)
```

#### Java

```java
try (Labeler<GenericLabel> sentencesLabeler = document.getLabeler("sentences")) {
      for (Span span : SentenceDetector.detectSentences(document.getText())) {
        sentencesLabeler.add(
          GenericLabel.newBuilder(span.start(), span.end()).build()
        );
      }
    }
```

After their context manager (``with`` in Python) or try-with-resources 
(``try`` in Java) blocks are exited the labelers will automatically finalize
and upload the labels to the events service for usage in downstream components.


## Events Service

The events service is a gRPC service that provides the interface for
storing and retrieving events and their associated data during processing. The
events service is used between processors to share artifacts of text 
processing.

Most of the interaction with the events service is abstracted by 
implementations of the ``Document`` and ``Event`` classes by the respective 
Python and Java frameworks, but as a gRPC service the events service can be 
interacted with at a lower level from any language that has a gRPC 
implementation. MTAP also provides a RESTful API gateway that can be used to 
make REST requests against the Events Service.
