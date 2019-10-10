# MTAP

## Microservice Text Analysis Platform

MTAP is a framework for distributed text analysis using gRPC and microservices-based architecture. 
MTAP is used to create independent, scalable, interoperable text analysis pipeline 
components in either Python or Java. 

## Requirements
- Python 3.5+
- Java 8+ (for java framework, integration tests)
- Go 13+ (for gateway, integration tests)

# Developer stuff

## Building

### Building the generated Python protobuf files

```shell script
python setup.py clean build_py
```

### Building a python distributable

```shell script
python setup.py bdist_wheel
```

### Building the Java Framework

```shell script
cd java
./gradlew build fatJar
```

### Building the Go HTTP API Gateway distributables
First time setup, follow the instructions for 
[gRPC Gateway](https://github.com/grpc-ecosystem/grpc-gateway) requirements.

Build stuff:
```shell script
cd go
make proto release
```

### Installing the Go API Gateway

```shell script
cd go
go install mtap-gateway/mtap-gateway.go 
```

# Testing

## Running Python unit tests

The python unit tests run using the version of MTAP installed to the site-packages: 

```shell script
pip install .\[tests]
pytest python/tests
```

## Running the Java unit tests

```shell script
cd java
./gradlew test
```

## Running integration tests

First, the go gateway needs to be installed and ``$GOROOT/bin`` needs to be on your ``$PATH``. From 
the root directory:

```shell script
cd go
go install mtap-gateway/mtap-gateway.go
```

Second, the Java framework fat jar needs to be built. From the root directory:

```shell script
cd java
./gradlew build fatJar
``` 

If you want to test service discovery via consul, consul needs to be started. From another terminal:

```shell script
consul agent -dev -ui
```

Now we're ready to run the integration tests, from the root directory:
```shell script
pip install .\[tests]
MTAP_JAR=java/build/libs/mtap-all-[MTAP VERSION GOES HERE] pytest python/tests --consul --integration
```

