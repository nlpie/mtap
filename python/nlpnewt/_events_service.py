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
import threading
from concurrent import futures

import grpc

from . import base
from . import constants
from .api.v1 import health_pb2, health_pb2_grpc, events_pb2, events_pb2_grpc


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


class _EventsServicer(events_pb2_grpc.EventsServicer, health_pb2_grpc.HealthServicer):
    def __init__(self):
        self.lock = threading.RLock()
        self.events = {}

    def _get_event(self, request, context):
        event_id = request.event_id
        try:
            event = self.events[event_id]
        except KeyError as e:
            _set_error_context(context, grpc.StatusCode.NOT_FOUND,
                               f"Did not find event_id: '{event_id}'")
            raise e
        return event, event_id

    def _get_document(self, request, context):
        event, event_id = self._get_event(request, context)
        document_name = request.document_name
        try:
            document = event.documents[document_name]
        except KeyError as e:
            _set_error_context(context, grpc.StatusCode.NOT_FOUND,
                               f"Event: '{event_id}' does not have document: '{document_name}'")
            raise e
        return document

    def OpenEvent(self, request, context=None):
        event_id = request.event_id
        if event_id == '':
            msg = "event_id was not set."
            _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
            raise ValueError(msg)
        create_event = False
        try:
            event = self.events[event_id]
        except KeyError:
            with self.lock:
                try:
                    event = self.events[event_id]
                except KeyError:
                    create_event = True
                if create_event:
                    event = _Event()
                    self.events[event_id] = event

        if not create_event and request.only_create_new:
            msg = f'Event already exists: "{event_id}"'
            _set_error_context(context, grpc.StatusCode.ALREADY_EXISTS, msg)
            raise ValueError(msg)
        event.clients += 1
        return events_pb2.OpenEventResponse(created=create_event)

    def CloseEvent(self, request, context=None):
        event, event_id = self._get_event(request, context)
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
        event, _ = self._get_event(request, context)
        key = request.key
        if key == '':
            msg = f'event_id cannot be null or empty'
            _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
            raise ValueError(msg)
        event.metadata[key] = request.value
        return events_pb2.AddMetadataResponse()

    def AddDocument(self, request, context=None):
        event, _ = self._get_event(request, context)
        document_name = request.document_name
        if document_name == '':
            msg = 'document_name was not set.'
            _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
            raise ValueError(msg)

        with event.d_lock:
            if document_name in event.documents:
                msg = f"Document '{document_name}' already exists."
                _set_error_context(context, grpc.StatusCode.ALREADY_EXISTS, msg)
                raise ValueError(msg)
            event.documents[document_name] = _Document(request.text)

        return events_pb2.AddDocumentResponse()

    def GetAllDocumentNames(self, request, context=None):
        event, _ = self._get_event(request, context)
        names = list(event.documents.keys())
        return events_pb2.GetAllDocumentNamesResponse(document_names=names)

    def GetDocumentText(self, request, context=None):
        document = self._get_document(request, context)
        return events_pb2.GetDocumentTextResponse(text=document.text)

    def AddLabels(self, request, context=None):
        document = self._get_document(request, context)
        labels_field = request.WhichOneof('labels')
        if labels_field is None:
            labels = (None, None)
        else:
            index_name = request.index_name
            if index_name == '':
                msg = 'No index_name was set.'
                _set_error_context(context, grpc.StatusCode.INVALID_ARGUMENT, msg)
                raise ValueError(msg)
            labels = (labels_field, getattr(request, labels_field))
        document.labels[request.index_name] = labels
        return events_pb2.AddLabelsResponse()

    def GetLabels(self, request, context=None):
        document = self._get_document(request, context)
        try:
            labels_type, labels = document.labels[request.index_name]
        except KeyError:
            msg = f"Event: '{request.event_id}' document: '{request.document_name} " \
                f"does not have label index: {request.index_name}'"
            _set_error_context(context, grpc.StatusCode.NOT_FOUND, msg)
            raise ValueError(msg)
        response = events_pb2.GetLabelsResponse()
        if labels_type is not None:
            getattr(response, labels_type).CopyFrom(labels)
        return response

    def Check(self, request, context=None):
        if request.service == '' or request.service == constants.PROCESSING_SERVICE_TAG:
            return health_pb2.HealthCheckResponse(status='SERVING')
        else:
            return health_pb2.HealthCheckResponse(status='NOT_SERVING')


class _EventsServer(base.Server):
    def __init__(self, config, thread_pool, address, port):
        server = grpc.server(thread_pool)
        servicer = _EventsServicer()
        events_pb2_grpc.add_EventsServicer_to_server(servicer, server)
        health_pb2_grpc.add_HealthServicer_to_server(servicer, server)
        self._port = server.add_insecure_port(f'{address}:{port}')
        self._server = server
        self._address = address
        self._config = config

    def start(self, *, register):
        logging.info("Starting events server on address: {}:{}", self._address, self._port)
        self._server.start()
        if register:
            from nlpnewt._discovery import Discovery
            service_registration = Discovery(config=self._config)
            self._deregister = service_registration.register_events_service(self._address,
                                                                            self._port,
                                                                            'v1')

    def stop(self, *, grace=None):
        try:
            self._deregister()
        except AttributeError:
            pass
        shutdown_event = self._server.stop(grace=grace)
        return shutdown_event


def create_server(config, address, port, workers):
    prefix = constants.EVENTS_SERVICE_NAME + "-"
    return _EventsServer(config,
                         futures.ThreadPoolExecutor(max_workers=workers,
                                                    thread_name_prefix=prefix),
                         address,
                         port)
