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
"""Internal events client."""

import collections
import contextlib
import threading
import typing
import typing as _typing
import uuid
from typing import Iterator

import grpc

from nlpnewt import _labels
from . import base
from . import constants
from . import _discovery
from .api.v1 import events_pb2_grpc, events_pb2


def get_events(config, *, address=None, stub=None):
    channel = None
    if stub is None:
        if address is None:
            discovery = _discovery.Discovery(config)
            address = discovery.discover_events_service('v1')

        channel = grpc.insecure_channel(address)
    return _EventsClient(channel)


class _EventsClient(base.Events):
    def __init__(self, channel):
        self.stub = events_pb2_grpc.EventsStub(channel)
        self._is_open = True
        self._channel = channel

    def __enter__(self):
        return self

    def open_event(self, event_id=None):
        event_id = event_id or uuid.uuid1()
        self._open_event(event_id, only_create_new=False)
        return _Event(self, event_id)

    def create_event(self, event_id=None):
        event_id = event_id or uuid.uuid1()
        self._open_event(event_id, only_create_new=True)
        return _Event(self, event_id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._is_open = False
        self._channel.close()

    def ensure_open(self):
        if not self._is_open:
            raise ValueError("Client to events service is not open")

    def _open_event(self, event_id, only_create_new):
        request = events_pb2.OpenEventRequest(event_id=event_id, only_create_new=only_create_new)
        try:
            self.stub.OpenEvent(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise ValueError("Event already exists")

    def close_event(self, event_id):
        request = events_pb2.CloseEventRequest(event_id=event_id)
        self.stub.CloseEvent.with_call(request)

    def get_all_metadata(self, event_id):
        request = events_pb2.GetAllMetadataRequest(event_id=event_id)
        response = self.stub.GetAllMetadata(request)
        return response.metadata

    def add_metadata(self, event_id, key, value):
        request = events_pb2.AddMetadataRequest(event_id=event_id, key=key, value=value)
        self.stub.AddMetadata(request)

    def get_all_document_names(self, event_id):
        request = events_pb2.GetAllDocumentNamesRequest(event_id=event_id)
        response = self.stub.GetAllDocumentNames(request)
        return list(response.document_names)

    def add_document(self, event_id, document_name, text):
        request = events_pb2.AddDocumentRequest(event_id=event_id,
                                                document_name=document_name,
                                                text=text)
        self.stub.AddDocument(request)

    def get_document_text(self, event_id, document_name):
        request = events_pb2.GetDocumentTextRequest(event_id=event_id,
                                                    document_name=document_name)
        response = self.stub.GetDocumentText(request)
        return response.text

    def add_labels(self, event_id, document_name, index_name, labels, adapter):
        request = events_pb2.AddLabelsRequest(event_id=event_id, document_name=document_name,
                                              index_name=index_name)
        adapter.add_to_message(labels, request)
        self.stub.AddLabels(request)

    def get_labels(self, event_id, document_name, index_name, adapter):
        request = events_pb2.GetLabelsRequest(event_id=event_id,
                                              document_name=document_name,
                                              index_name=index_name)
        response = self.stub.GetLabels(request)
        return adapter.create_index_from_response(response)


class _Event(base.Event):
    def __init__(self, client: _EventsClient, event_id):
        self._client = client
        self._event_id = event_id
        self._metadata = _Metadata(client, self)
        self._documents = {}
        self._open = True
        self._lock = threading.RLock()

    @property
    def event_id(self):
        return self._event_id

    @property
    def metadata(self):
        self.ensure_open()
        return self._metadata

    @property
    def created_indices(self) -> _typing.Dict[_typing.AnyStr, _typing.List[_typing.AnyStr]]:
        return {document_name: document.created_indices
                for document_name, document in self._documents.items()}

    def close(self):
        if self._open is True:
            with self._lock:
                # using double locking here to ensure that the event does not
                if self._open:
                    self._client.close_event(self._event_id)
                    self._open = False

    def add_document(self, document_name, text):
        self.ensure_open()
        if text is None:
            raise ValueError("Argument text cannot be None. "
                             "None maps to an empty string in protobuf.")
        self._client.add_document(self._event_id, document_name, text)
        document = _Document(self._client, self, document_name)
        self._documents[document_name] = document
        return document

    def __contains__(self, document_name):
        self.ensure_open()
        if document_name in self._documents:
            return True
        self._refresh_documents()

    def __getitem__(self, document_name):
        self.ensure_open()
        try:
            return self._documents[document_name]
        except KeyError:
            pass
        self._refresh_documents()
        return self._documents[document_name]

    def __len__(self) -> int:
        self.ensure_open()
        self._refresh_documents()
        return len(self._documents)

    def __iter__(self) -> Iterator[str]:
        self.ensure_open()
        self._refresh_documents()
        return iter(self._documents)

    def _refresh_documents(self):
        document_names = self._client.get_all_document_names(self._event_id)
        for name in document_names:
            if name not in self._documents:
                self._documents[name] = _Document(self._client, self, name)

    def ensure_open(self):
        self._client.ensure_open()
        if not self._open:
            raise ValueError("Event has been closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def add_created_indices(self, created_indices):
        for k, v in created_indices.items():
            try:
                doc = self._documents[k]
                doc.add_created_indices(v)
            except KeyError:
                pass


class _Metadata(collections.abc.MutableMapping):
    def __init__(self, client: _EventsClient, event):
        self._client = client
        self._event = event
        self._event_id = event.event_id
        self._metadata = {}

    def __contains__(self, key):
        self._event.ensure_open()
        if key in self._metadata:
            return True
        self._refresh_metadata()
        return key in self._metadata

    def __setitem__(self, key, value):
        self._event.ensure_open()
        if key in self:
            raise KeyError("Metadata already exists with key: " + key)
        self._metadata[key] = value
        self._client.add_metadata(self._event_id, key, value)

    def __getitem__(self, key):
        self._event.ensure_open()
        try:
            return self._metadata[key]
        except KeyError:
            self._refresh_metadata()
        return self._metadata[key]

    def __delitem__(self, v) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        self._event.ensure_open()
        self._refresh_metadata()
        return iter(self._metadata)

    def __len__(self) -> int:
        self._event.ensure_open()
        self._refresh_metadata()
        return len(self._metadata)

    def _refresh_metadata(self):
        self._event.ensure_open()
        response = self._client.get_all_metadata(self._event_id)
        self._metadata = response


class _Document(base.Document):
    def __init__(self, client: _EventsClient, event, document_name):
        self._client = client
        self._document_name = document_name
        self._event = event
        self._event_id = event.event_id

        self._text = None

        self._label_indices = {}
        self._labelers = []
        self._created_indices = []

    @property
    def event(self):
        return self._event

    @property
    def document_name(self) -> typing.AnyStr:
        self._event.ensure_open()
        return self._document_name

    @property
    def text(self):
        self._event.ensure_open()
        if self._text is None:
            self._text = self._client.get_document_text(self._event_id, self._document_name)
        return self._text

    @property
    def created_indices(self) -> _typing.List[_typing.AnyStr]:
        # create a copy so that the original is not modifiable.
        return list(self._created_indices)

    def get_label_index(self, label_index_name: str, *, label_type_id=None):
        self._event.ensure_open()
        if label_index_name in self._label_indices:
            return self._label_indices[label_index_name]

        if label_type_id is None:
            label_type_id = constants.GENERIC_LABEL_ID

        label_adapter = _labels.get_label_adapter(label_type_id)

        label_index = self._client.get_labels(self._event_id, self._document_name, label_index_name,
                                              adapter=label_adapter)
        self._label_indices[label_index_name] = label_index
        return label_index

    @contextlib.contextmanager
    def get_labeler(self, label_index_name: str, *, distinct: bool = None,
                    label_type=None):
        self._event.ensure_open()
        if label_index_name in self._labelers:
            raise KeyError("Labeler already in use: " + label_index_name)
        if label_type is not None and distinct is not None:
            raise ValueError("Either distinct or or label_type needs to be set, but not both.")
        if label_type is None:
            label_type = (constants.DISTINCT_GENERIC_LABEL_ID
                          if distinct
                          else constants.GENERIC_LABEL_ID)

        labeler = _Labeler(self._client, self, label_index_name, label_type)
        self._labelers.append(label_index_name)
        yield labeler
        # this isn't in a try-finally block because it is not cleanup, we do not want
        # the labeler to send labels after a processing failure.
        labeler.done()
        self._created_indices.append(label_index_name)

    def add_created_indices(self, created_indices):
        return self._created_indices.append(created_indices)


class _Labeler(base.Labeler):
    def __init__(self, client, document, label_index_name, label_type_id):
        self._client = client
        self._document = document
        self._label_index_name = label_index_name
        self._label_adapter: base.ProtoLabelAdapter = _labels.get_label_adapter(label_type_id)
        self.is_done = False
        self._current_labels = []

    def __call__(self, *args, **kwargs):
        self._document.event.ensure_open()
        label = self._label_adapter.create_label(*args, **kwargs)
        self._current_labels.append(label)
        return label

    def done(self):
        self._document.event.ensure_open()
        if self.is_done:
            return
        self._client.add_labels(event_id=self._document.event.event_id,
                                document_name=self._document.document_name,
                                index_name=self._label_index_name,
                                labels=self._current_labels,
                                adapter=self._label_adapter)
        self.is_done = True
