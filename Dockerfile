# Copyright 2019 Regents of the University of Minnesota.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# multi-stage dockerfile for nlp-newt
#
# NB: Build the source first!!!!!!!
#
# To build docker images:
#
# DOCKER_BUILDKIT=1 docker build -t <image name> --target <target> .

# To run examples:
#
# start event processor ->
#(base) D20181472:mtap gms$ docker run  --net=host gms/processor
#INFO:mtap._events_service:Starting events server on address: localhost:9090

# host processor
#(base) D20181472:mtap gms$ docker run   --net=host gms/hello

# run pipeline
#(base) D20181472:mtap gms$ docker run   --net=host gms/pipeline
#Hello YOUR NAME!

# NB: For all tutorials, you will need to have this Dockerfile in the same directory as a the clone of mtap (under the directory src)
#
#
# Tutorial: https://nlpie.github.io/mtap/docs/tutorials/python.html

#=============================================================
# Python events processor
# 
# build:  DOCKER_BUILDKIT=1 docker build -t gms/events:latest --target events . 
#
# run: docker run  --net=host gms/events
# -----------------------------------
FROM continuumio/miniconda3 AS events

COPY ./ /usr/share/mtap
RUN pip install /usr/share/mtap

WORKDIR /usr/share/mtap/python/mtap/examples

ENTRYPOINT [ "python", "-m",  "mtap", "events", "--address", "localhost", "--port", "9090"]


#===================================================================
# Python processor
# 
# build: DOCKER_BUILDKIT=1 docker build -t gms/processor:latest --target processor .  
#
# run: docker run  --net=host gms/processor
# ---------------------------------------
FROM continuumio/miniconda3 AS processor

COPY ./ /usr/share/mtap
RUN pip install /usr/share/mtap

WORKDIR /usr/share/mtap/python/mtap/examples

ENTRYPOINT [ "python", "hello.py",  "--address", "localhost", "--port", "9091", "--events", "localhost:9090"]

#================================================================
# Python pipeline
# 
# build: DOCKER_BUILDKIT=1 docker build -t gms/pipeline:latest --target pipeline . 
#
# run: docker run  --net=host gms/pipeline
# -------------------------------------
FROM continuumio/miniconda3 AS pipeline

COPY ./ /usr/share/mtap
RUN pip install /usr/share/mtap

WORKDIR /usr/share/mtap/python/mtap/examples

ENTRYPOINT [ "python", "pipeline.py"]

# Tutorial: https://nlpie.github.io/mtap/docs/tutorials/java.html

#=============================================================================
# Java processor
# 
# build: DOCKER_BUILDKIT=1 docker build -t gms/java-processor:latest --target java-processor . 
#
# run: docker run  --net=host gms/java-processor
#
# ----------------------------------
FROM openjdk:8-jre AS java-processor

# see https://github.com/puckel/docker-airflow/issues/182
RUN mkdir -p /usr/share/man/man1
################################

RUN apt-get update
RUN apt-get install openjdk-8-jdk -y

COPY java/build/libs /usr/share/python/mtap/examples

WORKDIR /usr/share/mtap/python/mtap/examples

ENTRYPOINT ["sh", "-c", "java -cp .:mtap-all-0.1.0-beta.4+18-gd272362.jar Hello -p 9092 -e localhost:9090"]

#====================================================================
# Python pipeline to work with Java processor
# 
# build:  docker build --target pipeline  -t gms/java-pipeline:latest .
#
# run: docker run  --net=host gms/java-pipeline
# ------------------------------------------
FROM continuumio/miniconda3 AS java-pipeline

COPY ./ /usr/share/mtap
RUN pip install /usr/share/mtap

WORKDIR /usr/share/mtap/python/mtap/examples

ENTRYPOINT [ "python", "pipeline2.py"]
