*************
mtap.pipeline
*************
.. module:: mtap.pipeline


Running a pipeline
==================
.. autoclass:: Pipeline
   :members:
   :show-inheritance:
.. autoclass:: MpConfig
   :members:
.. autoclass:: ComponentDescriptor
.. autoclass:: RemoteProcessor
   :show-inheritance:
.. autoclass:: LocalProcessor
   :show-inheritance:
.. autoclass:: PipelineTerminated

Pipeline Document Sources
=========================
.. autoclass:: ProcessingSource
   :members:
.. autoclass:: FilesInDirectoryProcessingSource
   :members:
   :show-inheritance:

Pipeline Results
================
.. autoclass:: BatchPipelineResult
   :members:
.. autoclass:: PipelineResult
   :members:
.. autoclass:: mtap.processing.results.ComponentResult
   :members:
.. autoclass:: mtap.processing.results.TimerStats
   :members:
.. autoclass:: mtap.processing.results.AggregateTimingInfo
   :members:

Pipeline Error Handling
=======================
.. automodule:: mtap.pipeline._error_handling
   :no-members:
.. module:: mtap.pipeline
   :noindex:
.. autoclass:: ProcessingErrorHandler
   :members:
.. autoclass:: mtap.processing.ErrorInfo
   :members:
.. autoclass:: mtap.processing.ErrorOrigin
   :members:
.. autoclass:: StopProcessing
.. autoclass:: SuppressError
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