---
layout: doc
title: Components
subpage: Documentation
description: The principal components of the MTAP Framework.
---

## Events Service

The events service is a gRPC service and server that provides the interface for
storing and retrieving events and their associated data during processing. The
events service is how processors share artifacts of text processing with
each-other.

The events service is currently a processing cache and not a permanent store.
It is implemented in Python using an in-memory store.

## Processor

A processor is a component which performs some kind of task on the data in an
 ``Event`` or a ``Document``. MTAP provides functionality for deploying and
 running these processors.
