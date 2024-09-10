<p align="center">
  <a href="https://pypi.org/project/mtap/">
    <img src="https://img.shields.io/pypi/v/mtap" /></a>
  <a href="https://mvnrepository.com/artifact/edu.umn.nlpie/mtap">
    <img src="https://img.shields.io/maven-central/v/edu.umn.nlpie/mtap" /></a>
  <a href='https://mtap.readthedocs.io/en/latest/?badge=latest'>
    <img src='https://readthedocs.org/projects/mtap/badge/?version=latest' alt='Documentation Status' /></a>
  <a href='https://github.com/nlpie/mtap/actions/workflows/ci.yml'>
    <img src='https://github.com/nlpie/mtap/actions/workflows/ci.yml/badge.svg?branch=main' /></a>
</p>

# MTAP

[nlpie.github.io/mtap](https://nlpie.github.io/mtap)

## Microservice Text Analysis Platform

MTAP is a framework for distributed text analysis using gRPC and microservices-based architecture. 
MTAP is used to create independent, scalable, interoperable text analysis pipeline 
components in either Python or Java. 

## Requirements
- Operating System: We test on Ubuntu 22.04 and MacOS Big Sur, but other UNIX-like distributions should work.
- [Python 3.9+](https://www.python.org/downloads/) We test on Python 3.9 and the latest stable version of Python. 
- Optional: [Java 11+](https://adoptium.net) (_If you want to create Java Processors_) We test on Java 11 and the latest stable version of Java.
- Optional: [Go 13+](https://golang.org) if you want to run the RESTful API Gateway.

## Features

### Ease of Use

MTAP takes care of all the communication between different components, and provides a distributed object model for text analysis artifacts. All you have to worry about is writing the text analysis code.

### Flexibility

By using the microservice pattern, text analysis components can be deployed once and then mixed and matched in different pipelines. Components written in different languages can interoperate without hassle. We also provide a RESTful API gateway that lets you call components using HTTP.

### Scalability

MTAP is designed to bridge the gap between prototyping new ideas and deploying them into a production environment. It supports calling components locally without using any network infastructure all the way up to deploying services and using service discovery via Consul to build pipelines.

## Instructions

We make getting started tutorials available on our project website for both [Python](https://nlpie.github.io/mtap/docs/tutorials/python.html) and [Java](https://nlpie.github.io/mtap/docs/tutorials/java.html).

## About Us

MTAP is developed at the University of Minnesota by the [NLP/IE Group in the Institute for Health Informatics](https://healthinformatics.umn.edu/research/nlpie-group).

## Acknowledgements
Funding for this work was provided by:

- 1 R01 LM011364-01 NIH-NLM
- 1 R01 GM102282-01A1 NIH-NIGMS
- U54 RR026066-01A2 NIH-NCRR
