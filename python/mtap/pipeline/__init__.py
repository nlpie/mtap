# Copyright 2023 Regents of the University of Minnesota.
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
