---
layout: doc
title: Processing
subpage: Documentation
description: How processing documents works using MTAP.
---

## Introduction

In MTAP there are two types of processing components:

- EventProcessor
- DocumentProcessor

Event processors perform processing on ``Event`` objects, uploading the results
to the event service using Labelers.

Document processors perform processing on a specific ``Document`` object on an
``Event``, which is specified through a ``document_name`` processing parameter.

Either a ``Pipeline`` object or the API gateway can be used to trigger
processing. MTAP handles retrieving a reference to the ``Event`` or ``Document``
from an identifier, and passes that object to the processor.

## Details

The MTAP framework provides functionality that takes processors classes,
instantiates them, and then wraps them in a gRPC service that respond to
specific processing endpoints. After this deployment, when the processor is
called, MTAP adapts the processing arguments from the gRPC request object
into objects that the processor can use.
