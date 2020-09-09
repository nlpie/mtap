mtap
====
.. module:: mtap

.. contents::

Command-Line Utility
--------------------

Running Events Service
^^^^^^^^^^^^^^^^^^^^^^

usage:

.. code-block:: text

 python -m mtap events [-h] [--address ADDRESS] [--port PORT]
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

API Documentation
-----------------

Events service client, documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: EventsClient
.. autoclass:: Event
.. autoclass:: Document
.. autoclass:: mtap.events.Labeler
.. autoclass:: mtap.events.LabelIndexInfo
   :exclude-members: __getnewargs__, __new__, __repr__
.. autoclass:: mtap.events.LabelIndexType

Labels
^^^^^^
.. autoclass:: mtap.labels.Label
.. autoclass:: Location
.. autofunction:: label
.. autoclass:: GenericLabel

Label Indices
^^^^^^^^^^^^^
.. autofunction:: label_index
.. autoclass:: mtap.label_indices.LabelIndex

Custom Label Types
^^^^^^^^^^^^^^^^^^
.. autoclass:: mtap.events.ProtoLabelAdapter

Creating Processors
^^^^^^^^^^^^^^^^^^^
.. autoclass:: mtap.processing.base.Processor
.. autoclass:: mtap.processing.EventProcessor
.. autoclass:: mtap.processing.DocumentProcessor
   :exclude-members: process
.. autoclass:: mtap.processing.base.Stopwatch

Processor Description Decorators
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: processor
.. autofunction:: mtap.processing.descriptions.parameter
.. autofunction:: mtap.processing.descriptions.label_index
.. autofunction:: mtap.processing.descriptions.label_property

Running Services
^^^^^^^^^^^^^^^^
.. autofunction:: processor_parser
.. autofunction:: run_processor
.. autoclass:: EventsServer
.. autoclass:: ProcessorServer

Running a pipeline
^^^^^^^^^^^^^^^^^^
.. autoclass:: Pipeline
   :exclude-members: insert
.. autoclass:: mtap.processing.pipeline.ComponentDescriptor
.. autoclass:: RemoteProcessor
.. autoclass:: LocalProcessor
.. autoclass:: mtap.processing.ProcessingSource
.. autoclass:: mtap.processing.PipelineResult
   :exclude-members: __getnewargs__, __new__, __repr__
.. autoclass:: mtap.processing.TimerStats
   :exclude-members: __getnewargs__, __new__, __repr__
.. autoclass:: mtap.processing.AggregateTimingInfo
   :exclude-members: __getnewargs__, __new__, __repr__

Configuration
^^^^^^^^^^^^^
.. autoclass:: Config
