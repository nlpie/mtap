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

New error handlers can be registered to be loaded in this fashion by overriding the ``name`` method or using the
module-qualified full class name.
"""
import dataclasses
import logging
import os.path
from abc import abstractmethod
from os import PathLike
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Union,
    ClassVar, Type
)

from mtap._event import Event
from mtap.processing import ErrorInfo
from mtap.serialization import Serializer

LOGGER = logging.getLogger('mtap.processing')

ErrorHandlerFactory = Callable[..., 'ProcessingErrorHandler']


class StopProcessing(Exception):
    """Thrown by error handlers when the pipeline should immediately
    terminate."""
    pass


class SuppressError(Exception):
    """Thrown by error handlers when the error should be suppressed
    and not handled by any downstream error handlers (later in the pipeline's
    list of error handlers) ."""
    pass


class ProcessingErrorHandler:
    """Base class for an error handler that is included in a pipeline to
    report and decide action for errors / exceptions that occur during
    processing.

    Note that you should not store any state on the error handler since it may
    be reused across multiple runs of the same pipeline, instead store stateful
    information in the state dictionary.
    """
    _REGISTRY: ClassVar[Dict[str, ErrorHandlerFactory]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ProcessingErrorHandler._REGISTRY[cls.name()] = cls

    @staticmethod
    def from_dict(conf: Optional[Dict[str, Any]]) -> 'ProcessingErrorHandler':
        """Creates an error handler from its dictionary representation.

        Args:
            conf: The dictionary representation of the error handler. Should have at minimum a ``name`` key with
                ``str`` value, can also have a dictionary of params that will be passed to the constructor of the
                 serializer.

        Returns:
            The instantiated error handler.
        """
        return ProcessingErrorHandler._REGISTRY[conf['name']](**conf.get('params', {}))

    @classmethod
    def name(cls):
        """Optional method that returns the name the error handler should be
        loaded into the registry with, by default will just use the full path
        name.
        """
        return '.'.join([cls.__module__, cls.__name__])

    @abstractmethod
    def handle_error(
            self,
            event: Event,
            error_info: ErrorInfo,
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

    @classmethod
    def name(cls):
        return 'simple'

    def handle_error(self, event, error_info, state):
        from mtap.processing import ErrorOrigin
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

    @classmethod
    def name(cls):
        return 'termination'

    def handle_error(self, _1, _2, state):
        try:
            state['failures'] += 1
        except KeyError:
            state['failures'] = 1
        if state['failures'] >= self.max_failures:
            print(f"Pipeline exceeded the maximum number "
                  f"of allowed failures ({self.max_failures}) "
                  f"and is terminating.")
            raise StopProcessing()


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

    @classmethod
    def name(cls):
        return 'logging'

    def handle_error(self, event, error_info, state):
        self.logger.error(
            f"An error occurred while processing an event with id "
            f"'{event.event_id}' through the remote component "
            f"'{error_info.component_id}' at address "
            f"'{error_info.address}': {error_info.error_repr}\n"
            f"It had the following message: {error_info.localized_msg}\n"
            + ''.join(error_info.stack_trace)
        )


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
    serializer: Type[Serializer]

    def __init__(self,
                 output_directory: Union[str, bytes, PathLike, None] = None,
                 serializer: Union[Type[Serializer], str, None] = None):
        self.output_directory = 'errors' if output_directory is None else output_directory
        if serializer is None:
            serializer = Serializer.get('json')
        if not issubclass(serializer, Serializer):
            serializer = Serializer.get(serializer)
        self.serializer = serializer

    @classmethod
    def name(cls):
        return 'to_directory'

    def handle_error(self, event, error_info, _):
        d = os.path.join(self.output_directory, event.event_id)
        os.makedirs(d, exist_ok=True)
        print(f"Writing error information to: "
              f"'{os.path.abspath(os.fspath(d))}'")
        import json
        with open(os.path.join(d, 'info.json'), 'w') as f:
            json.dump(dataclasses.asdict(error_info), f, default=str)
        ser_path = os.path.join(d, 'event' + self.serializer.extension())
        self.serializer.event_to_file(event, ser_path)
        with open(os.path.join(d, 'trace.txt'), 'w') as f:
            for line in error_info.stack_trace:
                f.write(line)  # The lines already have builtin line breaks


class SuppressAllErrorsHandler(ProcessingErrorHandler):
    @classmethod
    def name(cls):
        return 'suppress'

    def handle_error(self, *_args, **_kwargs):
        raise SuppressError()
