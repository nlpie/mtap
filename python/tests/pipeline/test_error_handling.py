#  Copyright (c) Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

from mtap import Event
from mtap.pipeline import ProcessingErrorHandler, SimpleErrorHandler, TerminationErrorHandler, LoggingErrorHandler, \
    ErrorsDirectoryErrorHandler, SuppressAllErrorsHandler
from mtap.pipeline._error_handling import handle_error, StopProcessing
from mtap.processing import ErrorInfo, ErrorOrigin


def test_registry():
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'simple'}), SimpleErrorHandler)
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'termination'}), TerminationErrorHandler)
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'logging'}), LoggingErrorHandler)
    directory = ProcessingErrorHandler.from_dict({'name': 'to_directory', 'params': {'output_directory': "."}})
    assert isinstance(directory, ErrorsDirectoryErrorHandler)
    assert isinstance(ProcessingErrorHandler.from_dict({'name': 'suppress'}), SuppressAllErrorsHandler)


event = Event(event_id='1')
ei = ErrorInfo(
    origin=ErrorOrigin.LOCAL,
    component_id='test',
    lang='py',
    error_type='blaherror',
    error_repr='blah',
    localized_msg='',
    locale='en_US',
    stack_trace=["a", "b"]
)


def test_error_thrown_by_handler():
    class First(ProcessingErrorHandler):
        def handle_error(self, event: Event, error_info: ErrorInfo, state: Dict[Any, Any]):
            raise ValueError()

    class Second(ProcessingErrorHandler):
        def handle_error(self, event: Event, error_info: ErrorInfo, state: Dict[Any, Any]):
            self.seen = True

    handlers = [(First(), {}), (Second, {})]
    with pytest.raises(ValueError):
        handle_error(handlers, event, ei)


def test_multiple_error_handlers():
    class First(ProcessingErrorHandler):
        def handle_error(self, e: Event, error_info: ErrorInfo, state: Dict[Any, Any]):
            pass

    class Second(ProcessingErrorHandler):
        def handle_error(self, e: Event, error_info: ErrorInfo, state: Dict[Any, Any]):
            self.seen = True

    second = Second()
    handlers = [(First(), {}), (second, {})]
    handle_error(handlers, event, ei)
    assert second.seen


def test_termination_error_handler():
    handlers = [((TerminationErrorHandler(max_failures=1)), {})]

    handle_error(handlers, event, ei)
    with pytest.raises(StopProcessing):
        handle_error(handlers, event, ei)


def test_logging_handler():
    class FakeLogger:
        def error(self, *values):
            self.msg = ''.join(values)

    logger = FakeLogger()
    handler = LoggingErrorHandler(logger)

    handlers = [(handler, {})]
    handle_error(handlers, event, ei)
    assert logger.msg.startswith("An error occurred while ")


def test_errors_directory_handler():
    with tempfile.TemporaryDirectory() as errors_dir:
        handler = ErrorsDirectoryErrorHandler(output_directory=errors_dir)
        handlers = [(handler, {})]
        handle_error(handlers, event, ei)
        p = Path(errors_dir) / '1'
        assert p.exists()
        assert (p / 'info.json').exists()
        assert (p / 'event.json').exists()
        assert (p / 'trace.txt').exists()


def test_suppress_error_handler():
    handlers = [(SuppressAllErrorsHandler(), {}), (TerminationErrorHandler(), {})]
    handle_error(handlers, event, ei)
    assert True
