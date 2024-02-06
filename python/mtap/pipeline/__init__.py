"""Functionality for creating and running pipelines."""

from mtap.pipeline._exc import PipelineTerminated
from mtap.pipeline._error_handling import (
    ProcessingErrorHandler,
    StopProcessing,
    SuppressError,
    SimpleErrorHandler,
    TerminationErrorHandler,
    LoggingErrorHandler,
    ErrorsDirectoryErrorHandler,
    SuppressAllErrorsHandler,
)
from mtap.pipeline._mp_config import (
    MpConfig,
)
from mtap.pipeline._pipeline import (
    Pipeline,
)
from mtap.pipeline._pipeline_components import (
    ComponentDescriptor,
    LocalProcessor,
    RemoteProcessor,
)
from mtap.pipeline._sources import (
    ProcessingSource,
    FilesInDirectoryProcessingSource,
    IterableProcessingSource,
)
from mtap.pipeline._results import (
    PipelineResult,
    PipelineTimes,
)
from mtap.pipeline._hosting import (
    run_pipeline_server
)
