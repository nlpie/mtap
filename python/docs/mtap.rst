****
mtap
****
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
=================

Events service client, documents
--------------------------------
.. autoclass:: EventsClient
.. autoclass:: Event
   :members:
.. autoclass:: Document
   :members:
.. autoclass:: mtap.data.Labeler
   :members:
.. autoclass:: mtap.data.LabelIndexInfo
   :members:
.. autoclass:: mtap.data.LabelIndexType
   :members:

Labels
------
.. autoclass:: mtap.data.Label
   :members:
.. autoclass:: mtap.data.Location
   :members:
.. autofunction:: label
.. autoclass:: GenericLabel
   :members:
   :show-inheritance:

Label Indices
-------------
.. autofunction:: label_index
.. autoclass:: mtap.data.LabelIndex
   :members:

Custom Label Types
------------------
.. autoclass:: mtap.data.ProtoLabelAdapter
   :members:

Creating Processors
-------------------
.. autoclass:: mtap.processing.Processor
   :members:
.. autoclass:: EventProcessor
   :members:
   :show-inheritance:
.. autoclass:: DocumentProcessor
   :members:
   :show-inheritance:
.. autoclass:: mtap.processing.Stopwatch
   :members:

Processor Description Decorators
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: processor
.. automodule:: mtap.processing.descriptions
   :members:
   :no-inherited-members:
   :exclude-members: processor

Running Services
----------------
.. module:: mtap
   :noindex:
.. autofunction:: processor_parser
.. autofunction:: run_processor

Running a pipeline
------------------
.. autoclass:: Pipeline
   :members:
   :show-inheritance:
.. autoclass:: mtap.processing.MpConfig
   :members:
.. autoclass:: mtap.processing.ComponentDescriptor
.. autoclass:: RemoteProcessor
   :show-inheritance:
.. autoclass:: LocalProcessor
   :show-inheritance:

Pipeline Document Sources
^^^^^^^^^^^^^^^^^^^^^^^^^
.. module:: mtap.processing
   :noindex:
.. autoclass:: ProcessingSource
   :members:
.. autoclass:: FilesInDirectoryProcessingSource
   :members:
   :show-inheritance:

Pipeline Results
^^^^^^^^^^^^^^^^
.. autoclass:: BatchPipelineResult
.. autoclass:: PipelineResult
.. autoclass:: ComponentResult
.. autoclass:: TimerStats
.. autoclass:: AggregateTimingInfo
   :members:

Pipeline Error Handling
^^^^^^^^^^^^^^^^^^^^^^^
.. automodule:: mtap.processing._error_handling
   :no-members:
.. module:: mtap.processing
.. autoclass:: ProcessingErrorHandler
.. autoclass:: ErrorInfo
.. autoclass:: ErrorOrigin
   :members:
.. autoclass:: StopProcessing
.. autoclass:: SuppressError
.. autoclass:: ErrorHandlerRegistry
   :members:
.. autoclass:: SimpleErrorHandler
   :members:
   :show-inheritance:
.. autoclass:: TerminationErrorHandler
   :members:
   :show-inheritance:
.. autoclass:: LoggingErrorHandler
   :members:
   :show-inheritance:
.. autoclass:: ErrorsDirectoryErrorHandler
   :members:
   :show-inheritance:
.. autoclass:: SuppressAllErrorsHandler
   :members:
   :show-inheritance:

Configuration
-------------
.. module:: mtap
   :noindex:
.. autoclass:: Config
