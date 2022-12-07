from google.api import annotations_pb2 as _annotations_pb2
from google.protobuf import duration_pb2 as _duration_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreatedIndex(_message.Message):
    __slots__ = ["document_name", "index_name"]
    DOCUMENT_NAME_FIELD_NUMBER: _ClassVar[int]
    INDEX_NAME_FIELD_NUMBER: _ClassVar[int]
    document_name: str
    index_name: str
    def __init__(self, document_name: _Optional[str] = ..., index_name: _Optional[str] = ...) -> None: ...

class GetInfoRequest(_message.Message):
    __slots__ = ["processor_id"]
    PROCESSOR_ID_FIELD_NUMBER: _ClassVar[int]
    processor_id: str
    def __init__(self, processor_id: _Optional[str] = ...) -> None: ...

class GetInfoResponse(_message.Message):
    __slots__ = ["metadata"]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    metadata: _struct_pb2.Struct
    def __init__(self, metadata: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class GetStatsRequest(_message.Message):
    __slots__ = ["processor_id"]
    PROCESSOR_ID_FIELD_NUMBER: _ClassVar[int]
    processor_id: str
    def __init__(self, processor_id: _Optional[str] = ...) -> None: ...

class GetStatsResponse(_message.Message):
    __slots__ = ["failures", "processed", "timing_stats"]
    class TimingStatsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: TimerStats
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[TimerStats, _Mapping]] = ...) -> None: ...
    FAILURES_FIELD_NUMBER: _ClassVar[int]
    PROCESSED_FIELD_NUMBER: _ClassVar[int]
    TIMING_STATS_FIELD_NUMBER: _ClassVar[int]
    failures: int
    processed: int
    timing_stats: _containers.MessageMap[str, TimerStats]
    def __init__(self, processed: _Optional[int] = ..., failures: _Optional[int] = ..., timing_stats: _Optional[_Mapping[str, TimerStats]] = ...) -> None: ...

class ProcessRequest(_message.Message):
    __slots__ = ["event_id", "event_service_instance_id", "params", "processor_id"]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_SERVICE_INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    PROCESSOR_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    event_service_instance_id: str
    params: _struct_pb2.Struct
    processor_id: str
    def __init__(self, processor_id: _Optional[str] = ..., event_id: _Optional[str] = ..., event_service_instance_id: _Optional[str] = ..., params: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...

class ProcessResponse(_message.Message):
    __slots__ = ["created_indices", "result", "timing_info"]
    class TimingInfoEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _duration_pb2.Duration
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...
    CREATED_INDICES_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    TIMING_INFO_FIELD_NUMBER: _ClassVar[int]
    created_indices: _containers.RepeatedCompositeFieldContainer[CreatedIndex]
    result: _struct_pb2.Struct
    timing_info: _containers.MessageMap[str, _duration_pb2.Duration]
    def __init__(self, timing_info: _Optional[_Mapping[str, _duration_pb2.Duration]] = ..., result: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., created_indices: _Optional[_Iterable[_Union[CreatedIndex, _Mapping]]] = ...) -> None: ...

class TimerStats(_message.Message):
    __slots__ = ["max", "mean", "min", "std", "sum"]
    MAX_FIELD_NUMBER: _ClassVar[int]
    MEAN_FIELD_NUMBER: _ClassVar[int]
    MIN_FIELD_NUMBER: _ClassVar[int]
    STD_FIELD_NUMBER: _ClassVar[int]
    SUM_FIELD_NUMBER: _ClassVar[int]
    max: _duration_pb2.Duration
    mean: _duration_pb2.Duration
    min: _duration_pb2.Duration
    std: _duration_pb2.Duration
    sum: _duration_pb2.Duration
    def __init__(self, mean: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., std: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., max: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., min: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ..., sum: _Optional[_Union[_duration_pb2.Duration, _Mapping]] = ...) -> None: ...
