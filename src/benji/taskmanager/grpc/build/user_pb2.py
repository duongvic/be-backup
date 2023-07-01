# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: user.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import base_type_pb2 as base__type__pb2
from . import user_type_pb2 as user__type__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='user.proto',
  package='grpc_user',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\nuser.proto\x12\tgrpc_user\x1a\x0f\x62\x61se_type.proto\x1a\x0fuser_type.proto2i\n\x0bUserService\x12,\n\x0b\x63reate_user\x12\x0f.grpc_user.User\x1a\x0c.base.Output\x12,\n\x0b\x64\x65lete_user\x12\x0f.grpc_user.User\x1a\x0c.base.Outputb\x06proto3'
  ,
  dependencies=[base__type__pb2.DESCRIPTOR,user__type__pb2.DESCRIPTOR,])



_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_USERSERVICE = _descriptor.ServiceDescriptor(
  name='UserService',
  full_name='grpc_user.UserService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=59,
  serialized_end=164,
  methods=[
  _descriptor.MethodDescriptor(
    name='create_user',
    full_name='grpc_user.UserService.create_user',
    index=0,
    containing_service=None,
    input_type=user__type__pb2._USER,
    output_type=base__type__pb2._OUTPUT,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='delete_user',
    full_name='grpc_user.UserService.delete_user',
    index=1,
    containing_service=None,
    input_type=user__type__pb2._USER,
    output_type=base__type__pb2._OUTPUT,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_USERSERVICE)

DESCRIPTOR.services_by_name['UserService'] = _USERSERVICE

# @@protoc_insertion_point(module_scope)