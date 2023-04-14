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

from mtap.processing._base import (
    DocumentProcessor,
    EventProcessor,
    Processor,
    ProcessorContext,
    ProcessingComponent,
    Stopwatch,
)
from mtap.processing._exc import ProcessingError

from mtap.processing._error_handling import (
    StopProcessing,
    SuppressError,
    ErrorOrigin,
    ErrorInfo,
    ProcessingErrorHandler,
    SimpleErrorHandler,
    TerminationErrorHandler,
    LoggingErrorHandler,
    ErrorsDirectoryErrorHandler,
    SuppressAllErrorsHandler,
    ErrorHandlerFactory,
    ErrorHandlerRegistry,
)

from mtap.processing.descriptions import processor
from mtap.processing._pipeline import Pipeline
from mtap.processing._mp_config import MpConfig

from mtap.processing._pipeline_components import (
    RemoteProcessor,
    LocalProcessor,
    ComponentDescriptor,
)

from mtap.processing._pipeline_results import (
    AggregateTimingInfo,
    BatchPipelineResult,
    PipelineResult,
    ComponentResult,
    TimerStats,
)

from mtap.processing._sources import (
    FilesInDirectoryProcessingSource,
    ProcessingSource,
)

from mtap.processing._service import (
    processor_parser,
    ProcessorServer,
    run_processor,
)
