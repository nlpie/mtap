# MTAP

[nlpie.github.io/mtap](https://nlpie.github.io/mtap)

## Microservice Text Analysis Platform

MTAP is a framework for distributed text analysis using gRPC and microservices-based architecture. 
MTAP is used to create independent, scalable, interoperable text analysis pipeline 
components in either Python or Java. 

## Requirements
- Operating System: Ubuntu 18.04 or MacOS Catalina (other operating systems may work, but are not tested).
- [Python 3.5+](https://www.python.org/downloads/)
- Optional: [Java JDK 9, 11, or 13](https://adoptopenjdk.net) if you want to create Java Processors.
- Optional: [Go 13+](https://golang.org) if you want to run the RESTful API Gateway.

## Features

### Ease of Use

MTAP takes care of all the communication between different components, and provides a distributed object model for text analysis artifacts. All you have to worry about is writing the text analysis code.

### Flexibility

By using the microservice pattern, text analysis components can be deployed once and then mixed and matched in different pipelines. Components written in different languages can interoperate without hassle. We also provide a RESTful API gateway that lets you call components using HTTP.

### Scalability

MTAP is designed to bridge the gap between prototyping new ideas and deploying them into a production environment. It supports calling components locally without using any network infastructure all the way up to deploying services and using service discovery via Consul to build pipelines.

## Getting started

### Installation

#### Python
```bash
pip install mtap
```

#### Java

Gradle:
```groovy
repositories {
    maven { 
        url "https://maven.pkg.github.com/nlpie/mtap" 
    }
}
```

```groovy
implementation 'edu.umn.nlpie:mtap:0.8.0'
```

Maven:

```xml
<repositories>
    <repository>
        <id>mtap-github</id>
        <name>MTAP GitHub Maven Packages</name>
        <url>https://maven.pkg.github.com/nlpie/mtap</url>
        <releases>
            <enabled>true</enabled>
        </releases>
    </repository>
</repositories>
```

```xml
<dependency>
  <groupId>edu.umn.nlpie</groupId>
  <artifactId>mtap</artifactId>
  <version>0.8.0</version>
</dependency>
```

### Instructions

We make getting started tutorials available on our project website for both [Python](https://nlpie.github.io/mtap/docs/tutorials/python.html) and [Java](https://nlpie.github.io/mtap/docs/tutorials/java.html).

### About Us

MTAP is developed at the University of Minnesota by the [NLP/IE Group in the Institute for Health Informatics](https://healthinformatics.umn.edu/research/nlpie-group).

### Acknowledgements
Funding for this work was provided by:

- 1 R01 LM011364-01 NIH-NLM
- 1 R01 GM102282-01A1 NIH-NIGMS
- U54 RR026066-01A2 NIH-NCRR
