---
layout: doc
title: Introduction
description: Getting started with MTAP.
subpage: Documentation
permalink: /docs
---

About
=====

MTAP was developed at the University of Minnesota by the [NLP/IE Group in the
Institute for Health Informatics](https://healthinformatics.umn.edu/research/nlpie-group).
We develop a text analysis system for clinical text called BioMedICUS and were
running into issues when we wanted to use machine learning code developed in
Python with our existing components developed in Java. We process millions of
notes, so from the start we needed something that was deployable at scale.
Furthermore, we needed something that researchers and students with minimal
development experience could pick up and use, and then wouldn't hamper us from
using that work in a production environment. These requirements led us to
develop our own framework for text analysis based on the microservice
architecture pattern, which is how MTAP was created.
