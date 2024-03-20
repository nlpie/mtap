# Copyright (c) Regents of the University of Minnesota.
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
from typing import Optional, Callable

import grpc
from grpc import Channel

from mtap import Config, constants
from mtap.api.v1 import events_pb2_grpc, events_pb2

from mtap._events_client import EventsClient
from mtap.api.v1.events_pb2 import GetLabelIndicesInfoResponse


class GrpcEventsClient(EventsClient):
    __slots__ = (
        '_address',
        '_channel_factory',
        '_channel',
        '_stub',
        '_instance_id',
        '_closed',
    )

    def __init__(self, address: str,
                 channel_factory: Callable[[str], Channel] = None,
                 channel: Optional[Channel] = None):
        if address is None:
            raise ValueError("Address cannot be None.")
        self._address = address
        self._channel_factory = channel_factory or create_channel
        self._channel = channel
        self._stub = None
        self._instance_id = None
        self._closed = False

    def __reduce__(self):
        return GrpcEventsClient, (self._address, self._channel_factory)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._closed = True
        if self._channel is not None:
            self._channel.close()

    @property
    def channel(self):
        if self._channel is None:
            self._channel = create_channel(self._address)
        return self._channel

    @property
    def stub(self):
        if self._stub is None:
            self._stub = events_pb2_grpc.EventsStub(self.channel)
        return self._stub

    @property
    def instance_id(self):
        if self._instance_id is None:
            if self._closed:
                raise ValueError("Client to events service is not open")
            req = events_pb2.GetEventsInstanceIdRequest()
            resp = self.stub.GetEventsInstanceId(req)
            self._instance_id = resp.instance_id
        return self._instance_id

    def _check_instance_id(self, instance_id):
        if instance_id != self.instance_id:
            raise ValueError(f"Event instance id: {instance_id} "
                             f"does not match client: {self.instance_id}")

    def ensure_open(self, instance_id):
        if self._closed:
            raise ValueError("Client to events service is not open")
        self._check_instance_id(instance_id)

    def open_event(self, instance_id, event_id, only_create_new):
        if instance_id is not None:
            self._check_instance_id(instance_id)
        request = events_pb2.OpenEventRequest(event_id=event_id,
                                              only_create_new=only_create_new)
        self.stub.OpenEvent(request)
        return self.instance_id

    def close_event(self, instance_id, event_id):
        self._check_instance_id(instance_id)

        request = events_pb2.CloseEventRequest(event_id=event_id)
        response = self.stub.CloseEvent(request)
        return response is not None

    def get_all_metadata(self, instance_id, event_id):
        self._check_instance_id(instance_id)

        request = events_pb2.GetAllMetadataRequest(event_id=event_id)
        response = self.stub.GetAllMetadata(request)
        return response.metadata

    def add_metadata(self, instance_id, event_id, key, value):
        self._check_instance_id(instance_id)

        request = events_pb2.AddMetadataRequest(event_id=event_id, key=key,
                                                value=value)
        response = self.stub.AddMetadata(request)
        return response is not None

    def get_all_binary_data_names(self, instance_id, event_id):
        self._check_instance_id(instance_id)

        request = events_pb2.GetAllBinaryDataNamesRequest(event_id=event_id)
        response = self.stub.GetAllBinaryDataNames(request)
        return list(response.binary_data_names)

    def add_binary_data(self, instance_id, event_id, binary_data_name,
                        binary_data):
        self._check_instance_id(instance_id)

        request = events_pb2.AddBinaryDataRequest(
            event_id=event_id,
            binary_data_name=binary_data_name,
            binary_data=binary_data
        )
        response = self.stub.AddBinaryData(request)
        return response is not None

    def get_binary_data(self, instance_id, event_id, binary_data_name):
        self._check_instance_id(instance_id)

        request = events_pb2.GetBinaryDataRequest(
            event_id=event_id,
            binary_data_name=binary_data_name
        )
        response = self.stub.GetBinaryData(request)
        return response.binary_data

    def get_all_document_names(self, instance_id, event_id):
        self._check_instance_id(instance_id)

        request = events_pb2.GetAllDocumentNamesRequest(event_id=event_id)
        response = self.stub.GetAllDocumentNames(request)
        return list(response.document_names)

    def add_document(self, instance_id, event_id, document_name, text):
        self._check_instance_id(instance_id)

        request = events_pb2.AddDocumentRequest(event_id=event_id,
                                                document_name=document_name,
                                                text=text)
        response = self.stub.AddDocument(request)
        return response is not None

    def get_document_text(self, instance_id, event_id, document_name):
        self._check_instance_id(instance_id)

        request = events_pb2.GetDocumentTextRequest(
            event_id=event_id,
            document_name=document_name
        )
        response = self.stub.GetDocumentText(request)
        return response.text

    def get_label_index_info(self, instance_id, event_id, document_name):
        self._check_instance_id(instance_id)
        from mtap._label_indices import LabelIndexInfo, LabelIndexType

        request = events_pb2.GetLabelIndicesInfoRequest(
            event_id=event_id,
            document_name=document_name
        )
        response = self.stub.GetLabelIndicesInfo(request)
        result = []
        proto_label_index_info = GetLabelIndicesInfoResponse.LabelIndexInfo
        for index in response.label_index_infos:
            if index.type == proto_label_index_info.GENERIC:
                index_type = LabelIndexType.GENERIC
            elif index.type == proto_label_index_info.CUSTOM:
                index_type = LabelIndexType.CUSTOM
            else:
                index_type = LabelIndexType.UNKNOWN
            result.append(LabelIndexInfo(index.index_name, index_type))
        return result

    def add_labels(self, instance_id, event_id, document_name, index_name,
                   labels, adapter):
        self._check_instance_id(instance_id)

        request = events_pb2.AddLabelsRequest(event_id=event_id,
                                              document_name=document_name,
                                              index_name=index_name,
                                              no_key_validation=True)
        adapter.add_to_message(labels, request)
        response = self.stub.AddLabels(request)
        return response is not None

    def get_labels(self, instance_id, event_id, document_name, index_name,
                   adapter):
        self._check_instance_id(instance_id)

        request = events_pb2.GetLabelsRequest(event_id=event_id,
                                              document_name=document_name,
                                              index_name=index_name)
        response = self.stub.GetLabels(request)
        return adapter.create_index_from_response(response)


def create_channel(address):
    config = Config()
    options = config.get('grpc.events_options', {})
    channel = grpc.insecure_channel(address, options=list(options.items()))

    from grpc_health.v1 import health_pb2_grpc, health_pb2
    health = health_pb2_grpc.HealthStub(channel)
    hcr = health_pb2.HealthCheckRequest(
        service=constants.EVENTS_SERVICE_NAME
    )
    health.Check(hcr,
                 metadata=[('service-name', constants.EVENTS_SERVICE_NAME)])
    return channel
