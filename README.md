# MTAP

## Microservice Text Analysis Platform

MTAP is a framework for distributed text analysis using gRPC and microservices-based architecture. 
MTAP is used to create independent, scalable, interoperable text analysis pipeline 
components in either Python or Java. 


## Running Python unit tests

The python unit tests run using the version of MTAP installed to the site-packages: 

```shell script
pip install .\[tests]
pytest python/tests
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

