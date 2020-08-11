---
layout: doc
title: Introduction
description: Getting started with MTAP.
subpage: Documentation
permalink: /docs
---

## NLP/IE Background

MTAP is developed at the University of Minnesota by the [NLP/IE Group in the Institute for Health Informatics](https://healthinformatics.umn.edu/research/nlpie-group).

## What is MTAP?

We develop and maintain a text analysis system for clinical text called BioMedICUS. As requirements changed, we wanted to support Python components interoperability with our existing components developed in Java. In order to process millions of notes, ability to deploy at scale is a requirement. Furthermore, MTAP facilitates users with minimal development experience, making creating components easier and allowing for deployment to a production environment.  These requirements led us to develop our own framework for text analysis based on the microservice architecture pattern.

## What is BioMedICUS?

[The BioMedical Information Collection and Understanding System (BioMedICUS)](https://nlpie.github.io/biomedicus) is a system for large-scale text analysis and processing of biomedical and clinical reports. It provides general NLP processing such as sentence detection, part of speech tagging, and acronym detection tailored for clinical text, as clinical-specific processing such as the detection of UMLS (Unified Medical Language System) concepts in text. We use BioMedICUS at the University of Minnesota to process millions of clinical notes for use by researchers, for example via our information extraction system [PIER (Patient Information Extraction for Research)](https://nlpie.github.io/pier).

#### How does BioMedICUS use MTAP?

BioMedICUS uses MTAP as a foundational framework and for running BioMedICUS processors. When we develop a component for BioMedICUS, we develop it using MTAP classes which are responsible for the lower level management of moving data around, horizontal scaling of components during deployment, and providing a data model for storing artifacts of clinical text processing. BioMedICUS handles the text processing algorithms, MTAP handles running the processes and moving data between those algorithms.

### What are microservices and how does that fit into MTAP?

Microservices are an architecture pattern in which services are broken into de-coupled, independently deployable components that communicate on a network using standardized protocols. In the case of text processing, there are many components that rely on the work of upstream components in the form of a processing pipeline. In MTAP, processing components in a pipeline are each deployed individually as "microservices". This enables a lot of flexibility in how the components are developed and deployed, they can be programmed in different languages, they can be on different machines, they can be scaled at different levels depending on need.
