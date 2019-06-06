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
"""Internal events service client"""

import logging
import os
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager, closing
from pathlib import Path

import grpc
from grpc_health.v1 import health
from grpc_health.v1 import health_pb2_grpc

from nlpnewt import constants
from nlpnewt._config import Config
from nlpnewt.api.v1 import events_pb2, events_pb2_grpc

LOGGER = logging.getLogger(__name__)


class EventsServer:
    """Server which hosts events.

    Parameters
    ----------
    address: str
        The address / hostname / IP to host the server on.
    port: int
        The port to host the server on.
    register: bool
        Whether to register the service with service discovery.
    workers: int, optional
        The number of workers that should handle requests.
    """

    def __init__(self, address, port, register=False, workers=10):
        prefix = constants.EVENTS_SERVICE_NAME + "-worker"
        thread_pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix=prefix)
        server = grpc.server(thread_pool)
        servicer = EventsServicer()
        events_pb2_grpc.add_EventsServicer_to_server(servicer, server)
        health_servicer = health.HealthServicer()
        health_servicer.set('', 'SERVING')
        health_servicer.set(constants.EVENTS_SERVICE_NAME, 'SERVING')
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        self._port = server.add_insecure_port(address + ':' + str(port))
        self._server = server
        self._address = address
        self._config = Config()
        self._register = register

    @property
    def port(self) -> int:
        """Returns the port that the server is listening on.

        Returns
        -------
        int
            Bound port.

        """
        return self._port

    def start(self):
        """Starts the service.
        """
        LOGGER.info("Starting events server on address: %s:%d", self._address, self._port)
        self._server.start()
        if self._register:
            from nlpnewt._discovery import Discovery
            service_registration = Discovery(config=self._config)
            self._deregister = service_registration.register_events_service(self._address,
                                                                            self._port,
                                                                            'v1')

    def stop(self, *, grace=None):
        """De-registers (if registered with service discovery) the service and immediately stops
        accepting requests, completely stopping the service after a specified `grace` time.

        During the grace period the server will continue to process existing requests, but it will
        not accept any new requests. This function is idempotent, multiple calls will shutdown
        the server after the soonest grace to expire, calling the shutdown event for all calls to
        this function.

        Parameters
        ----------
        grace: float, optional
            The grace period that the server should continue processing requests for shutdown.

        Returns
        -------
        threading.Event
            A shutdown event for the server.
        """
        LOGGER.info("Stopping events server on address: %s:%d", self._address, self._port)
        try:
            self._deregister()
        except AttributeError:
            pass
        shutdown_event = self._server.stop(grace=grace)
        shutdown_event.wait()


class EventsServicer(events_pb2_grpc.EventsServicer):
    def __init__(self):
        self.lock = threading.RLock()
        self.events = {}

    def _get_event(self, request, context=None):
        event_id = request.event_id
        try:
            event = self.events[event_id]
        except KeyError as e:
            _set_error_context(context, grpc.StatusCode.NOT_FOUND,
                               "Did not find event_id: '{}'".format(event_id))
            raise e
        return event, event_id

    def _get_document(self, request, context=None):
        event, event_id = self._get_event(request, context)
        document_name = request.document_name
        try:
            document = event.documents[document_name]
        except KeyError as e:
            _set_error_context(context, grpc.StatusCode.NOT_FOUND,
                               "Event: '{}' does not have document: '{}'".format(event_id,
                                                                                 document_name))
            raise e
        return document

    def OpenEvent(self, request, context=None):
        event_id = request.event_id
        if event_id == '':
            msg = "event_id was not set."
            _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
            return
        created_event = False
        try:
            event = self.events[event_id]
        except KeyError:
            with self.lock:
                try:
                    event = self.events[event_id]
                except KeyError:
                    created_event = True
                    event = _Event()
                    self.events[event_id] = event

        if not created_event and request.only_create_new:
            msg = 'Event already exists: "{}"'.format(event_id)
            _set_error_context(context, grpc.StatusCode.ALREADY_EXISTS, msg)
            return
        event.clients += 1
        return events_pb2.OpenEventResponse(created=created_event)

    def CloseEvent(self, request, context=None):
        try:
            event, event_id = self._get_event(request, context)
        except KeyError:
            return
        deleted = False
        with event.c_lock:
            event.clients -= 1
            if event.clients == 0:
                del self.events[event_id]
                deleted = True
        return events_pb2.CloseEventResponse(deleted=deleted)

    def GetAllMetadata(self, request, context=None):
        event, _ = self._get_event(request, context)
        return events_pb2.GetAllMetadataResponse(metadata=event.metadata)

    def AddMetadata(self, request, context=None):
        try:
            event, _ = self._get_event(request, context)
        except KeyError:
            return
        key = request.key
        if key == '':
            msg = 'event_id cannot be null or empty'
            _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
            return
        event.metadata[key] = request.value
        return events_pb2.AddMetadataResponse()

    def AddDocument(self, request, context=None):
        try:
            event, event_id = self._get_event(request, context)
        except KeyError:
            return
        document_name = request.document_name
        if document_name == '':
            msg = 'document_name was not set.'
            _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
            return

        with event.d_lock:
            if document_name in event.documents:
                msg = "Document '{}' already exists.".format(document_name)
                _set_error_context(context, grpc.StatusCode.ALREADY_EXISTS, msg)
                return
            event.documents[document_name] = _Document(request.text)

        return events_pb2.AddDocumentResponse()

    def GetAllDocumentNames(self, request, context=None):
        try:
            event, event_id = self._get_event(request, context)
        except KeyError:
            return
        names = list(event.documents.keys())
        return events_pb2.GetAllDocumentNamesResponse(document_names=names)

    def GetDocumentText(self, request, context=None):
        try:
            document = self._get_document(request, context)
        except KeyError:
            return
        return events_pb2.GetDocumentTextResponse(text=document.text)

    def GetLabelIndicesInfo(self, request, context=None):
        try:
            document = self._get_document(request, context)
        except KeyError:
            return
        response = events_pb2.GetLabelIndicesInfoResponse()
        for k, v in document.labels.items():
            labels_type, _ = v
            info = response.label_index_infos.add()
            info.index_name = k
            if labels_type == 'json_labels':
                info.type = events_pb2.GetLabelIndicesInfoResponse.LabelIndexInfo.JSON
            elif labels_type == 'other_labels':
                info.type = 'OTHER'
        return response

    def AddLabels(self, request, context=None):
        try:
            document = self._get_document(request, context)
        except KeyError:
            return
        labels_field = request.WhichOneof('labels')
        if labels_field is None:
            labels = (None, None)
        else:
            index_name = request.index_name
            if index_name == '':
                msg = 'No index_name was set.'
                _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
                return
            labels = (labels_field, getattr(request, labels_field))
        document.labels[request.index_name] = labels
        return events_pb2.AddLabelsResponse()

    def GetLabels(self, request, context=None):
        try:
            document = self._get_document(request, context)
        except KeyError:
            return
        try:
            labels_type, labels = document.labels[request.index_name]
        except KeyError:
            msg = "Event: '{}' document: '{} does not have label index: {}'".format(
                request.event_id, request.document_name, request.index_name)
            _set_error_context(context, grpc.StatusCode.NOT_FOUND, msg)
            return
        response = events_pb2.GetLabelsResponse()
        if labels_type is not None:
            getattr(response, labels_type).CopyFrom(labels)
        return response


class _Event:
    def __init__(self):
        self.c_lock = threading.RLock()
        self.clients = 0
        self.metadata = {}
        self.documents = {}
        self.d_lock = threading.RLock()


class _Document:
    def __init__(self, text):
        self.text = text
        self.lock = {}
        self.labels = {}


def _set_error_context(context, status_code, msg):
    try:
        context.set_code(status_code)
        context.set_details(msg)
    except AttributeError:
        pass
