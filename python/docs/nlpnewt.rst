.. Copyright 2018 Regents of the University of Minnesota.

.. Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

..     http://www.apache.org/licenses/LICENSE-2.0

.. Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

nlpnewt
=======
.. module:: nlpnewt

Command-Line Utility
--------------------

Running Events Service
^^^^^^^^^^^^^^^^^^^^^^

usage:

.. code-block:: text

 python -m nlpnewt events [-h] [--address ADDRESS] [--port PORT]
                          [--workers WORKERS] [--register] [--config CONFIG]

 optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, -a ADDRESS
                        the address to serve the service on
  --port PORT, -p PORT  the port to serve the service on
  --workers WORKERS, -w WORKERS
                        number of worker threads to handle requests
  --register, -r        whether to register the service with the configured
                        service discovery
  --config CONFIG, -c CONFIG
                        path to config file


Running Processors
^^^^^^^^^^^^^^^^^^

usage:

.. code-block:: text

 python -m nlpnewt processor [-h] [--address ADDRESS] [--port PORT]
                             [--workers WORKERS] [--register]
                             [--config CONFIG]
                             [--events-address EVENTS_ADDRESS] --name NAME
                             [--module MODULE]
                             [args [args ...]]

 positional arguments:
  args                  args that will be passed to the processor

 optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, -a ADDRESS
                        the address to serve the service on
  --port PORT, -p PORT  the port to serve the service on
  --workers WORKERS, -w WORKERS
                        number of worker threads to handle requests
  --register, -r        whether to register the service with the configured
                        service discovery
  --config CONFIG, -c CONFIG
                        path to config file
  --events-address EVENTS_ADDRESS, --events EVENTS_ADDRESS, -e EVENTS_ADDRESS
                        address of the events service to use, omit to use
                        discovery
  --name NAME, -n NAME  The name the processor is registered under using
                        the processor decorator.
  --module MODULE, -m MODULE
                        A python module to load to trigger the
                        processor decorator

API Documentation
-----------------

Events service client, documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: Events
.. autoclass:: nlpnewt.events.Event
.. autoclass:: nlpnewt.events.Document

Labels on text
^^^^^^^^^^^^^^
.. autoclass:: nlpnewt.labels.Label
.. autoclass:: nlpnewt.labels.Location
.. autoclass:: nlpnewt.events.Labeler
.. autoclass:: GenericLabel
.. autoclass:: nlpnewt.label_indices.LabelIndex

Custom Label Types
^^^^^^^^^^^^^^^^^^
.. autofunction:: proto_label_adapter
.. autoclass:: nlpnewt.events.ProtoLabelAdapter

Creating Processors
^^^^^^^^^^^^^^^^^^^
.. autofunction:: processor
.. autoclass:: nlpnewt.processing.EventProcessor
.. autoclass:: nlpnewt.processing.DocumentProcessor
.. autoclass:: nlpnewt.processing.ProcessorContext

Running Services
^^^^^^^^^^^^^^^^
.. autoclass:: EventsServer
.. autoclass:: ProcessorServer

Running a pipeline
^^^^^^^^^^^^^^^^^^
.. autoclass:: Pipeline
.. autoclass:: nlpnewt.processing.ProcessingResult
.. autoclass:: nlpnewt.processing.TimerStats
.. autoclass:: nlpnewt.processing.AggregateTimingInfo

Configuration
^^^^^^^^^^^^^
.. autoclass:: Config
