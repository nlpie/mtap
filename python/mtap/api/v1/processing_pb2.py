# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: mtap/api/v1/processing.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.api import annotations_pb2 as google_dot_api_dot_annotations__pb2
from google.protobuf import duration_pb2 as google_dot_protobuf_dot_duration__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cmtap/api/v1/processing.proto\x12\x0bmtap.api.v1\x1a\x1cgoogle/api/annotations.proto\x1a\x1egoogle/protobuf/duration.proto\x1a\x1cgoogle/protobuf/struct.proto\"9\n\x0c\x43reatedIndex\x12\x15\n\rdocument_name\x18\x01 \x01(\t\x12\x12\n\nindex_name\x18\x02 \x01(\t\"\x84\x01\n\x0eProcessRequest\x12\x14\n\x0cprocessor_id\x18\x01 \x01(\t\x12\x10\n\x08\x65vent_id\x18\x02 \x01(\t\x12!\n\x19\x65vent_service_instance_id\x18\x04 \x01(\t\x12\'\n\x06params\x18\x03 \x01(\x0b\x32\x17.google.protobuf.Struct\"\xff\x01\n\x0fProcessResponse\x12\x41\n\x0btiming_info\x18\x01 \x03(\x0b\x32,.mtap.api.v1.ProcessResponse.TimingInfoEntry\x12\'\n\x06result\x18\x02 \x01(\x0b\x32\x17.google.protobuf.Struct\x12\x32\n\x0f\x63reated_indices\x18\x03 \x03(\x0b\x32\x19.mtap.api.v1.CreatedIndex\x1aL\n\x0fTimingInfoEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12(\n\x05value\x18\x02 \x01(\x0b\x32\x19.google.protobuf.Duration:\x02\x38\x01\"&\n\x0eGetInfoRequest\x12\x14\n\x0cprocessor_id\x18\x01 \x01(\t\"<\n\x0fGetInfoResponse\x12)\n\x08metadata\x18\x02 \x01(\x0b\x32\x17.google.protobuf.Struct\"\xd5\x01\n\nTimerStats\x12\'\n\x04mean\x18\x01 \x01(\x0b\x32\x19.google.protobuf.Duration\x12&\n\x03std\x18\x02 \x01(\x0b\x32\x19.google.protobuf.Duration\x12&\n\x03max\x18\x03 \x01(\x0b\x32\x19.google.protobuf.Duration\x12&\n\x03min\x18\x04 \x01(\x0b\x32\x19.google.protobuf.Duration\x12&\n\x03sum\x18\x05 \x01(\x0b\x32\x19.google.protobuf.Duration\"\'\n\x0fGetStatsRequest\x12\x14\n\x0cprocessor_id\x18\x01 \x01(\t\"\xca\x01\n\x10GetStatsResponse\x12\x11\n\tprocessed\x18\x01 \x01(\x05\x12\x10\n\x08\x66\x61ilures\x18\x02 \x01(\x05\x12\x44\n\x0ctiming_stats\x18\x03 \x03(\x0b\x32..mtap.api.v1.GetStatsResponse.TimingStatsEntry\x1aK\n\x10TimingStatsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12&\n\x05value\x18\x02 \x01(\x0b\x32\x17.mtap.api.v1.TimerStats:\x02\x38\x01\x32\xf7\x02\n\tProcessor\x12\x81\x01\n\x07Process\x12\x1b.mtap.api.v1.ProcessRequest\x1a\x1c.mtap.api.v1.ProcessResponse\";\x82\xd3\xe4\x93\x02\x35\"0/v1/processors/{processor_id}/process/{event_id}:\x01*\x12p\n\x07GetInfo\x12\x1b.mtap.api.v1.GetInfoRequest\x1a\x1c.mtap.api.v1.GetInfoResponse\"*\x82\xd3\xe4\x93\x02$\x12\"/v1/processors/{processor_id}/info\x12t\n\x08GetStats\x12\x1c.mtap.api.v1.GetStatsRequest\x1a\x1d.mtap.api.v1.GetStatsResponse\"+\x82\xd3\xe4\x93\x02%\x12#/v1/processors/{processor_id}/statsB\x1b\n\x19\x65\x64u.umn.nlpie.mtap.api.v1b\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'mtap.api.v1.processing_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\031edu.umn.nlpie.mtap.api.v1'
  _PROCESSRESPONSE_TIMINGINFOENTRY._options = None
  _PROCESSRESPONSE_TIMINGINFOENTRY._serialized_options = b'8\001'
  _GETSTATSRESPONSE_TIMINGSTATSENTRY._options = None
  _GETSTATSRESPONSE_TIMINGSTATSENTRY._serialized_options = b'8\001'
  _PROCESSOR.methods_by_name['Process']._options = None
  _PROCESSOR.methods_by_name['Process']._serialized_options = b'\202\323\344\223\0025\"0/v1/processors/{processor_id}/process/{event_id}:\001*'
  _PROCESSOR.methods_by_name['GetInfo']._options = None
  _PROCESSOR.methods_by_name['GetInfo']._serialized_options = b'\202\323\344\223\002$\022\"/v1/processors/{processor_id}/info'
  _PROCESSOR.methods_by_name['GetStats']._options = None
  _PROCESSOR.methods_by_name['GetStats']._serialized_options = b'\202\323\344\223\002%\022#/v1/processors/{processor_id}/stats'
  _CREATEDINDEX._serialized_start=137
  _CREATEDINDEX._serialized_end=194
  _PROCESSREQUEST._serialized_start=197
  _PROCESSREQUEST._serialized_end=329
  _PROCESSRESPONSE._serialized_start=332
  _PROCESSRESPONSE._serialized_end=587
  _PROCESSRESPONSE_TIMINGINFOENTRY._serialized_start=511
  _PROCESSRESPONSE_TIMINGINFOENTRY._serialized_end=587
  _GETINFOREQUEST._serialized_start=589
  _GETINFOREQUEST._serialized_end=627
  _GETINFORESPONSE._serialized_start=629
  _GETINFORESPONSE._serialized_end=689
  _TIMERSTATS._serialized_start=692
  _TIMERSTATS._serialized_end=905
  _GETSTATSREQUEST._serialized_start=907
  _GETSTATSREQUEST._serialized_end=946
  _GETSTATSRESPONSE._serialized_start=949
  _GETSTATSRESPONSE._serialized_end=1151
  _GETSTATSRESPONSE_TIMINGSTATSENTRY._serialized_start=1076
  _GETSTATSRESPONSE_TIMINGSTATSENTRY._serialized_end=1151
  _PROCESSOR._serialized_start=1154
  _PROCESSOR._serialized_end=1529
# @@protoc_insertion_point(module_scope)
