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
"""Functionality for handling errors during pipeline processing.

Errors are handled by instances of the :class:`ProcessingErrorHandler`
class. To set up error handlers, the pipeline has an
:attr:`~mtap.processing.Pipeline.error_handlers` attribute. The
error handlers in this attribute will be called sequentially when an
error occurs during processing.

The default error handlers list is:

#. :class:`SimpleErrorHandler` (name ``simple``).
#. :class:`TerminationErrorHandler` with
   :attr:`~TerminationErrorHandler.max_failures` set to 0
   (name ``termination``).

There are an additional number of built-in error handlers that can be used
including:

* :class:`LoggingErrorHandler` which logs to a specified
  :class:`logging.Logger` object (name ``logging``).
* :class:`ErrorsDirectoryErrorHandler` which for all errors that occur
  writes a set of files to disk containing the serialized event, the stack
  trace, and the error information (name ``directory``).
* :class:`SuppressAllErrorsHandler` which suppresses all errors
  (name ``suppress``).

In yaml pipeline configurations, error handlers can be specified using
their registered name (shown above) and a dictionary of parameters that
will be passed to the registered factory method (usually the constructor).
An example of error_handlers configuration in the pipeline file is shown
below.

.. code-block:: text

  error_handlers:
  - name: logging
  - name: directory
    params:
      output_directory: '/path/to/'
  - name: termination
    params:
      max_failures: 0
  components:
    ...

New error handlers can be registered to be loaded in this fashion using
:meth:`~mtap.processing.ErrorHandlerRegistry.register`

"""
import abc
import dataclasses
import logging
import os.path
import traceback
from enum import Enum, auto
from os import PathLike
from typing import (
    Any,
    TYPE_CHECKING,
    Callable,
    Final,
    Dict,
    Optional,
    Union,
    List
)

import grpc
from google.rpc import error_details_pb2, status_pb2
from grpc_status import rpc_status

if TYPE_CHECKING:
    import mtap
    from mtap import Event
    from mtap.serialization import Serializer

LOGGER = logging.getLogger('mtap.processing')


class ProcessingException(Exception):
    """An exception that occurred in a processing component.

    Attributes
        error_info (ErrorInfo): Information about the error.

    """

    def __init__(self, error_info: 'ErrorInfo'):
        self.error_info = error_info

    def to_rpc_status(self):
        info = self.error_info
        status = status_pb2.Status()
        status.code = grpc.StatusCode.UNKNOWN.value[0]

        error_info = error_details_pb2.ErrorInfo()
        error_info.reason = "PROCESSING_FAILURE"
        error_info.domain = "mtap.nlpie.umn.edu"
        error_info.metadata['lang'] = info.lang
        error_info.metadata['errorType'] = info.error_type
        error_info.metadata['errorRepr'] = info.error_repr
        error_info_any = status.details.add()
        error_info_any.Pack(error_info)

        debug_info = error_details_pb2.DebugInfo()
        debug_info.stack_entries.extend(info.stack_trace)
        debug_info_any = status.details.add()
        debug_info_any.Pack(debug_info)

        localized_message = error_details_pb2.LocalizedMessage()
        localized_message.locale = info.locale
        localized_message.message = info.localized_msg
        localized_message_any = status.details.add()
        localized_message_any.Pack(localized_message)
        return status

    @staticmethod
    def from_local_exception(exc, component_id, message=None):
        error_info = ErrorInfo(
            origin=ErrorOrigin.LOCAL,
            component_id=component_id,
            lang='python',
            error_type=str(type(exc)),
            error_repr=repr(exc),
            localized_msg=message or "An internal error occurred while "
                                     "attempting to process an Event. "
                                     "This is potentially a bug, contact the "
                                     "developer of the component.",
            locale="en-US",
            stack_trace=list(traceback.format_exception(exc))
        )
        return ProcessingException(error_info)

    @staticmethod
    def from_rpc_error(rpc_error, component_id, address):

        status = rpc_status.from_call(rpc_error)
        if status is None:
            return ProcessingException.from_local_exception(rpc_error,
                                                            component_id)
        info = error_details_pb2.ErrorInfo()
        debug_info = error_details_pb2.DebugInfo()
        localized_message = error_details_pb2.LocalizedMessage()
        for detail in status.details:
            for target in [info, debug_info, localized_message]:
                if detail.Is(target.DESCRIPTOR):
                    detail.Unpack(target)
        error_info = ErrorInfo(
            origin=ErrorOrigin.REMOTE,
            component_id=component_id,
            lang=info.metadata['lang'],
            error_type=info.metadata['errorType'],
            error_repr=info.metadata['errorRepr'],
            localized_msg=localized_message.message,
            locale=localized_message.locale,
            stack_trace=list(debug_info.stack_entries),
            address=address,
        )
        return ProcessingException(error_info)


class StopProcessing(Exception):
    """Thrown by error handlers when the pipeline should immediately
    terminate."""
    pass


class SuppressError(Exception):
    """Thrown by error handlers when the error should be suppressed
    and not handled by any downstream error handlers (later in the pipeline's
    list of error handlers) ."""
    pass


class ErrorOrigin(Enum):
    """Where the error occurred.
    """
    #: Error occurred locally to this process.
    LOCAL = auto()
    #: Error occurred on a remote component.
    REMOTE = auto()


@dataclasses.dataclass
class ErrorInfo:
    """Information about an error.

    Attributes:
        origin: The source of the error.
        component_id: The id of the processing component that
            the error occurred in.
        lang: What language did the error occur in?
        error_type: The type of the error.
        error_repr: The string representation of the error.
        localized_msg: A localized, user-friendly message.
        locale: The locale of the message.
        stack_trace: The stack trace of the message.
        address: The remote address.
    """
    origin: 'mtap.processing.ErrorOrigin'
    component_id: str
    lang: str
    error_type: str
    error_repr: str
    localized_msg: str
    locale: str
    stack_trace: List[str]
    address: Optional[str] = None


class ProcessingErrorHandler(abc.ABC):
    """Base class for an error handler that is included in a pipeline to
    report and decide action for errors / exceptions that occur during
    processing."""

    @abc.abstractmethod
    def handle_error(
            self,
            event: 'Event',
            error_info: 'ErrorInfo',
            state: Dict[Any, Any]
    ):
        """Handles an error that was caught by processing logic and
        transformed into a :class:`~mtap.processing.ProcessingException`.

        Args:
            event:
                The event that was being processed when the error was thrown.
            error_info:
                The information about the error.
            state:
                A dictionary that is preserved in-between calls to the
                error handler that the handler can use to store state local
                to the current run of processing.

        Raises:
            StopProcessing: if the pipeline should immediately stop processing.
            SuppressError: if the error should be suppressed and not passed to
                any downstream error handlers (later in the pipeline's list of
                error handlers).
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def handle_exception(
            self,
            event: 'Event',
            exc: 'Exception',
            state: Dict[Any, Any]
    ):
        """Handles an exception that was not caught by the processing logic,
        for example one that occurred in the MTAP pipeline or component logic.

        Args:
            event:
                The event that was being processed when the exception was
                thrown.
            exc: The exception thrown.
            state:
                A dictionary that is preserved in-between calls to the
                error handler that the handler can use to store state local
                to the current run of processing.

        Raises:
            StopProcessing: The pipeline should immediately stop processing.
            SuppressError: The error should be suppressed and not passed to
                any downstream error handlers (later in the pipeline's list of
                error handlers).
        """
        raise NotImplementedError()


ErrorHandlerFactory = Callable[[Dict[str, Any]], ProcessingErrorHandler]

registry: Final[Dict[str, ErrorHandlerFactory]] = {}


class ErrorHandlerRegistry:
    """Registry for error handlers so that they can be instantiated from
    configuration.
    """

    @staticmethod
    def register(
            name: str
    ) -> Callable[[ErrorHandlerFactory], ErrorHandlerFactory]:
        """Registers an error handler.

        Args:
            name: The unique identifier

        Returns:
            A decorator that adds the factory to the registry.

        """
        def decorate(f: ErrorHandlerFactory) -> ErrorHandlerFactory:
            if name in registry:
                raise ValueError('Duplicate name for ErrorHandler: ' + name)
            registry[name] = f
            return f

        return decorate

    @staticmethod
    def from_dict(conf: Optional[Dict[str, Any]]) -> ProcessingErrorHandler:
        """Creates an error handler from its dictionary representation.

        Args:
            conf: The dictionary representation of the error handler.

        Returns:
            The instantiated error handler.

        """
        return registry[conf['name']](**conf.get('params', {}))


@ErrorHandlerRegistry.register('simple')
class SimpleErrorHandler(ProcessingErrorHandler):
    """Prints a simple helpful explanation of the error info.
    """

    def __init__(self, more_help: Optional[str] = None):
        #: Additional help to be printed after every error.
        self.more_help: str = (
                more_help or
                "Check the configuration settings to enable enhanced "
                "debug behavior."
        )

    def handle_error(self, event, error_info, state):
        if error_info.origin == ErrorOrigin.REMOTE:
            print(
                f"An error occurred while processing an event with id "
                f"'{event.event_id}' through the remote component "
                f"'{error_info.component_id}' at address "
                f"'{error_info.address}': {error_info.error_repr}\n"
                f"It had the following message: {error_info.localized_msg}\n"
                f"{self.more_help}")
        else:
            print(
                f"An error occurred while processing an event with id "
                f"'{event.event_id}' through the component "
                f"'{error_info.component_id}': '{error_info.error_repr}'\n"
                f"It had the following message: {error_info.localized_msg}\n"
                f"{self.more_help}")

    def handle_exception(self, event, exc, state):
        print(
            f"An error occurred while processing an event with id "
            f"'{event.event_id}': '{repr(exc)}'\n"
            f"{self.more_help}")


@ErrorHandlerRegistry.register('termination')
class TerminationErrorHandler(ProcessingErrorHandler):
    """Terminates the pipeline after more than :attr:`max_failures`
    number of errors occurs.

    Attributes:
        max_failures: The maximum number of errors to allow before
            immediately terminating the pipeline.

    """
    max_failures: int

    def __init__(self, max_failures: int = 0):
        self.max_failures = max_failures

    def _increment_and_check(self, state):
        try:
            state['failures'] += 1
        except KeyError:
            state['failures'] = 1
        if state['failures'] >= self.max_failures:
            print(f"Pipeline exceeded the maximum number "
                  f"of allowed failures ({self.max_failures}) "
                  f"and is terminating.")
            raise StopProcessing()

    def handle_error(self, _1, _2, state):
        self._increment_and_check(state)

    def handle_exception(self, _1, _2, state):
        self._increment_and_check(state)


@ErrorHandlerRegistry.register('logging')
class LoggingErrorHandler(ProcessingErrorHandler):
    """Logs errors to a specified :class:`logging.Logger` object.

    Args:
        logger: Either the logger itself, the logger name, or none to use
            ``mtap.processing``.

    Attributes:
        logger: The logger to use.

    """
    logger: logging.Logger

    def __init__(self, logger: Union[str, logging.Logger, None] = None):
        if isinstance(logger, str):
            logger = logging.getLogger(logger)
        self.logger = (logger or logging.getLogger('mtap.processing'))

    def handle_error(self, event, error_info, state):
        self.logger.error(
            f"An error occurred while processing an event with id "
            f"'{event.event_id}' through the remote component "
            f"'{error_info.component_id}' at address "
            f"'{error_info.address}': {error_info.error_repr}\n"
            f"It had the following message: {error_info.localized_msg}\n"
            + ''.join(error_info.stack_trace)
        )

    def handle_exception(self, event, exc, state):
        self.logger.error(
            f"An error occurred while processing an event with id "
            f"'{event.event_id}': {exc}\n"
            + ''.join(traceback.format_exception(exc))
        )


@ErrorHandlerRegistry.register('directory')
class ErrorsDirectoryErrorHandler(ProcessingErrorHandler):
    """Built-in Error Handler which handles failures in pipeline processing by 
    writing files containing the error info, stack trace, and serialized event.

    Args:
        serializer: Either a serializer, a configuration dictionary that can
            be used to instantiate a serializer, or ``None`` to use the
            default json serializer.

    Attributes:
        output_directory: The directory to write the files to.
        serializer: The serializer to use to serialize the event.

    """
    output_directory: Union[str, bytes, PathLike]
    serializer: 'Serializer'

    def __init__(self,
                 output_directory: 'Union[str, bytes, PathLike]',
                 serializer: 'Union[Serializer, Dict[str, Any], None]' = None):
        self.output_directory = output_directory
        if serializer is None:
            from mtap.serialization import SerializerRegistry
            serializer = SerializerRegistry.create('json')
        if not isinstance(serializer, Serializer):
            from mtap.serialization import SerializerRegistry
            serializer = SerializerRegistry.from_dict(serializer)
        self.serializer = serializer

    def _write_out(self, event, error_info):
        d = os.path.join(self.output_directory, event.event_id)
        os.makedirs(d, exist_ok=True)
        print(f"Writing error information to: "
              f"'{os.path.abspath(os.fspath(d))}'")
        import json
        with open(os.path.join(d, 'info.json'), 'w') as f:
            json.dump(dataclasses.asdict(error_info), f, default=str)
        ser_path = os.path.join(d, 'event' + self.serializer.extension)
        self.serializer.event_to_file(event, ser_path)
        with open(os.path.join(d, 'trace.txt'), 'w') as f:
            for line in error_info.stack_trace:
                f.write(line)  # The lines already have builtin line breaks

    def handle_error(self, event, error_info, _):
        self._write_out(event, error_info)

    def handle_exception(self, event, exc, _):
        error_info = ErrorInfo(
            ErrorOrigin.LOCAL,
            'pipeline',
            'python',
            str(type(exc)),
            repr(exc),
            'en-US',
            'An exception occurred in the pipeline.',
            traceback.format_exception(exc),
        )
        self._write_out(event, error_info)


@ErrorHandlerRegistry.register('suppress')
class SuppressAllErrorsHandler(ProcessingErrorHandler):
    def handle_error(self, *_args, **_kwargs):
        raise SuppressError()

    def handle_exception(self, *_args, **_kwargs):
        raise SuppressError()
