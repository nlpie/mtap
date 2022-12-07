from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddBinaryDataRequest(_message.Message):
    __slots__ = ["binary_data", "binary_data_name", "event_id"]
    BINARY_DATA_FIELD_NUMBER: _ClassVar[int]
    BINARY_DATA_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    binary_data: bytes
    binary_data_name: str
    event_id: str
    def __init__(self, event_id: _Optional[str] = ..., binary_data_name: _Optional[str] = ..., binary_data: _Optional[bytes] = ...) -> None: ...

class AddBinaryDataResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AddDocumentRequest(_message.Message):
    __slots__ = ["document_name", "event_id", "text"]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    document_name: str
    event_id: str
    text: str
    def __init__(self, event_id: _Optional[str] = ..., document_name: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class AddDocumentResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AddLabelsRequest(_message.Message):
    __slots__ = ["custom_labels", "document_name", "event_id", "generic_labels", "index_name", "no_key_validation"]
    CUSTOM_LABELS_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    GENERIC_LABELS_FIELD_NUMBER: _ClassVar[int]
    INDEX_NAME_FIELD_NUMBER: _ClassVar[int]
    NO_KEY_VALIDATION_FIELD_NUMBER: _ClassVar[int]
    custom_labels: _any_pb2.Any
    document_name: str
    event_id: str
    generic_labels: GenericLabels
    index_name: str
    no_key_validation: bool
    def __init__(self, event_id: _Optional[str] = ..., document_name: _Optional[str] = ..., index_name: _Optional[str] = ..., generic_labels: _Optional[_Union[GenericLabels, _Mapping]] = ..., custom_labels: _Optional[_Union[_any_pb2.Any, _Mapping]] = ..., no_key_validation: bool = ...) -> None: ...

class AddLabelsResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class AddMetadataRequest(_message.Message):
    __slots__ = ["event_id", "key", "value"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    key: str
    value: str
    def __init__(self, event_id: _Optional[str] = ..., key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class AddMetadataResponse(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class CloseEventRequest(_message.Message):
    __slots__ = ["event_id", "lease_id"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    LEASE_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    lease_id: int
    def __init__(self, event_id: _Optional[str] = ..., lease_id: _Optional[int] = ...) -> None: ...

class CloseEventResponse(_message.Message):
    __slots__ = ["deleted"]
    DELETED_FIELD_NUMBER: _ClassVar[int]
    deleted: bool
    def __init__(self, deleted: bool = ...) -> None: ...

class GenericLabel(_message.Message):
    __slots__ = ["end_index", "fields", "identifier", "reference_ids", "start_index"]
    END_INDEX_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    IDENTIFIER_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_IDS_FIELD_NUMBER: _ClassVar[int]
    START_INDEX_FIELD_NUMBER: _ClassVar[int]
    end_index: int
    fields: _struct_pb2.Struct
    identifier: int
    reference_ids: _struct_pb2.Struct
    start_index: int
    def __init__(self, identifier: _Optional[int] = ..., start_index: _Optional[int] = ..., end_index: _Optional[int] = ..., fields: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., reference_ids: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GenericLabels(_message.Message):
    __slots__ = ["is_distinct", "labels"]
    IS_DISTINCT_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    is_distinct: bool
    labels: _containers.RepeatedCompositeFieldContainer[GenericLabel]
    def __init__(self, is_distinct: bool = ..., labels: _Optional[_Iterable[_Union[GenericLabel, _Mapping]]] = ...) -> None: ...

class GetAllBinaryDataNamesRequest(_message.Message):
    __slots__ = ["event_id"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    def __init__(self, event_id: _Optional[str] = ...) -> None: ...

class GetAllBinaryDataNamesResponse(_message.Message):
    __slots__ = ["binary_data_names"]
    BINARY_DATA_NAMES_FIELD_NUMBER: _ClassVar[int]
    binary_data_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, binary_data_names: _Optional[_Iterable[str]] = ...) -> None: ...

class GetAllDocumentNamesRequest(_message.Message):
    __slots__ = ["event_id"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    def __init__(self, event_id: _Optional[str] = ...) -> None: ...

class GetAllDocumentNamesResponse(_message.Message):
    __slots__ = ["document_names"]
    DOCUMENT_NAMES_FIELD_NUMBER: _ClassVar[int]
    document_names: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, document_names: _Optional[_Iterable[str]] = ...) -> None: ...

class GetAllMetadataRequest(_message.Message):
    __slots__ = ["event_id"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    def __init__(self, event_id: _Optional[str] = ...) -> None: ...

class GetAllMetadataResponse(_message.Message):
    __slots__ = ["metadata"]
    class MetadataEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    METADATA_FIELD_NUMBER: _ClassVar[int]
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class GetBinaryDataRequest(_message.Message):
    __slots__ = ["binary_data_name", "event_id"]
    BINARY_DATA_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    binary_data_name: str
    event_id: str
    def __init__(self, event_id: _Optional[str] = ..., binary_data_name: _Optional[str] = ...) -> None: ...

class GetBinaryDataResponse(_message.Message):
    __slots__ = ["binary_data"]
    BINARY_DATA_FIELD_NUMBER: _ClassVar[int]
    binary_data: bytes
    def __init__(self, binary_data: _Optional[bytes] = ...) -> None: ...

class GetDocumentTextRequest(_message.Message):
    __slots__ = ["document_name", "event_id"]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    document_name: str
    event_id: str
    def __init__(self, event_id: _Optional[str] = ..., document_name: _Optional[str] = ...) -> None: ...

class GetDocumentTextResponse(_message.Message):
    __slots__ = ["text"]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class GetEventsInstanceIdRequest(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GetEventsInstanceIdResponse(_message.Message):
    __slots__ = ["instance_id"]
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: str
    def __init__(self, instance_id: _Optional[str] = ...) -> None: ...

class GetLabelIndicesInfoRequest(_message.Message):
    __slots__ = ["document_name", "event_id"]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    document_name: str
    event_id: str
    def __init__(self, event_id: _Optional[str] = ..., document_name: _Optional[str] = ...) -> None: ...

class GetLabelIndicesInfoResponse(_message.Message):
    __slots__ = ["label_index_infos"]
    class LabelIndexInfo(_message.Message):
        __slots__ = ["index_name", "type"]
        class LabelIndexType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        CUSTOM: GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType
        GENERIC: GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType
        INDEX_NAME_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        UNKNOWN: GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType
        index_name: str
        type: GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType
        def __init__(self, index_name: _Optional[str] = ..., type: _Optional[_Union[GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType, str]] = ...) -> None: ...
    LABEL_INDEX_INFOS_FIELD_NUMBER: _ClassVar[int]
    label_index_infos: _containers.RepeatedCompositeFieldContainer[GetLabelIndicesInfoResponse.LabelIndexInfo]
    def __init__(self, label_index_infos: _Optional[_Iterable[_Union[GetLabelIndicesInfoResponse.LabelIndexInfo, _Mapping]]] = ...) -> None: ...

class GetLabelsRequest(_message.Message):
    __slots__ = ["document_name", "event_id", "index_name"]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    INDEX_NAME_FIELD_NUMBER: _ClassVar[int]
    document_name: str
    event_id: str
    index_name: str
    def __init__(self, event_id: _Optional[str] = ..., document_name: _Optional[str] = ..., index_name: _Optional[str] = ...) -> None: ...

class GetLabelsResponse(_message.Message):
    __slots__ = ["custom_labels", "generic_labels"]
    CUSTOM_LABELS_FIELD_NUMBER: _ClassVar[int]
    GENERIC_LABELS_FIELD_NUMBER: _ClassVar[int]
    custom_labels: _any_pb2.Any
    generic_labels: GenericLabels
    def __init__(self, generic_labels: _Optional[_Union[GenericLabels, _Mapping]] = ..., custom_labels: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class OpenEventRequest(_message.Message):
    __slots__ = ["event_id", "lease_duration", "only_create_new"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    LEASE_DURATION_FIELD_NUMBER: _ClassVar[int]
    ONLY_CREATE_NEW_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    lease_duration: _duration_pb2.Duration
    only_create_new: bool
    def __init__(self, event_id: _Optional[str] = ..., only_create_new: bool = ..., lease_duration: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...

class OpenEventResponse(_message.Message):
    __slots__ = ["created", "lease_id"]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    LEASE_ID_FIELD_NUMBER: _ClassVar[int]
    created: bool
    lease_id: int
    def __init__(self, created: bool = ..., lease_id: _Optional[int] = ...) -> None: ...
