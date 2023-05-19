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
import enum
import traceback
from dataclasses import dataclass
from typing import List, Optional


class ProcessingException(Exception):
    """An exception that occurred in a processing component.

    Attributes
        error_info (ErrorInfo): Information about the error.

    """

    def __init__(self, error_info: 'ErrorInfo'):
        self.error_info = error_info

    def to_rpc_status(self):
        from grpc import StatusCode
        from google.rpc import error_details_pb2, status_pb2

        info = self.error_info
        status = status_pb2.Status()
        status.code = StatusCode.UNKNOWN.value[0]

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
        from grpc_status import rpc_status
        from google.rpc import error_details_pb2

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


class ErrorOrigin(enum.Enum):
    """Where the error occurred.
    """
    #: Error occurred locally to this process.
    LOCAL = enum.auto()
    #: Error occurred on a remote component.
    REMOTE = enum.auto()


@dataclass
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
    origin: ErrorOrigin
    component_id: str
    lang: str
    error_type: str
    error_repr: str
    localized_msg: str
    locale: str
    stack_trace: List[str]
    address: Optional[str] = None
