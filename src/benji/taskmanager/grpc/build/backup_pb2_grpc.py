# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import backup_type_pb2 as backup__type__pb2
from . import base_type_pb2 as base__type__pb2


class BackupServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ping = channel.unary_unary(
                '/backup.BackupService/ping',
                request_serializer=base__type__pb2.Empty.SerializeToString,
                response_deserializer=base__type__pb2.Health.FromString,
                )
        self.create = channel.unary_unary(
                '/backup.BackupService/create',
                request_serializer=backup__type__pb2.BackupInput.SerializeToString,
                response_deserializer=backup__type__pb2.BackupOutput.FromString,
                )
        self.delete = channel.unary_unary(
                '/backup.BackupService/delete',
                request_serializer=backup__type__pb2.BackupDeleteInput.SerializeToString,
                response_deserializer=backup__type__pb2.BackupOutput.FromString,
                )
        self.restore = channel.unary_unary(
                '/backup.BackupService/restore',
                request_serializer=backup__type__pb2.BackupRestoreInput.SerializeToString,
                response_deserializer=backup__type__pb2.BackupOutput.FromString,
                )
        self.map_storage = channel.unary_unary(
                '/backup.BackupService/map_storage',
                request_serializer=backup__type__pb2.StorageInput.SerializeToString,
                response_deserializer=base__type__pb2.Output.FromString,
                )
        self.update_storage = channel.unary_unary(
                '/backup.BackupService/update_storage',
                request_serializer=backup__type__pb2.StorageInput.SerializeToString,
                response_deserializer=base__type__pb2.Output.FromString,
                )
        self.delete_storage = channel.unary_unary(
                '/backup.BackupService/delete_storage',
                request_serializer=backup__type__pb2.StorageInput.SerializeToString,
                response_deserializer=base__type__pb2.Output.FromString,
                )
        self.get_node_disk_used_overcommit = channel.unary_unary(
                '/backup.BackupService/get_node_disk_used_overcommit',
                request_serializer=backup__type__pb2.NodeInput.SerializeToString,
                response_deserializer=backup__type__pb2.NodeOutput.FromString,
                )
        self.get_node_disk_used_percent = channel.unary_unary(
                '/backup.BackupService/get_node_disk_used_percent',
                request_serializer=backup__type__pb2.NodeInput.SerializeToString,
                response_deserializer=backup__type__pb2.NodeOutput.FromString,
                )


class BackupServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ping(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def create(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def delete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def restore(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def map_storage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def update_storage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def delete_storage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_node_disk_used_overcommit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_node_disk_used_percent(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BackupServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ping': grpc.unary_unary_rpc_method_handler(
                    servicer.ping,
                    request_deserializer=base__type__pb2.Empty.FromString,
                    response_serializer=base__type__pb2.Health.SerializeToString,
            ),
            'create': grpc.unary_unary_rpc_method_handler(
                    servicer.create,
                    request_deserializer=backup__type__pb2.BackupInput.FromString,
                    response_serializer=backup__type__pb2.BackupOutput.SerializeToString,
            ),
            'delete': grpc.unary_unary_rpc_method_handler(
                    servicer.delete,
                    request_deserializer=backup__type__pb2.BackupDeleteInput.FromString,
                    response_serializer=backup__type__pb2.BackupOutput.SerializeToString,
            ),
            'restore': grpc.unary_unary_rpc_method_handler(
                    servicer.restore,
                    request_deserializer=backup__type__pb2.BackupRestoreInput.FromString,
                    response_serializer=backup__type__pb2.BackupOutput.SerializeToString,
            ),
            'map_storage': grpc.unary_unary_rpc_method_handler(
                    servicer.map_storage,
                    request_deserializer=backup__type__pb2.StorageInput.FromString,
                    response_serializer=base__type__pb2.Output.SerializeToString,
            ),
            'update_storage': grpc.unary_unary_rpc_method_handler(
                    servicer.update_storage,
                    request_deserializer=backup__type__pb2.StorageInput.FromString,
                    response_serializer=base__type__pb2.Output.SerializeToString,
            ),
            'delete_storage': grpc.unary_unary_rpc_method_handler(
                    servicer.delete_storage,
                    request_deserializer=backup__type__pb2.StorageInput.FromString,
                    response_serializer=base__type__pb2.Output.SerializeToString,
            ),
            'get_node_disk_used_overcommit': grpc.unary_unary_rpc_method_handler(
                    servicer.get_node_disk_used_overcommit,
                    request_deserializer=backup__type__pb2.NodeInput.FromString,
                    response_serializer=backup__type__pb2.NodeOutput.SerializeToString,
            ),
            'get_node_disk_used_percent': grpc.unary_unary_rpc_method_handler(
                    servicer.get_node_disk_used_percent,
                    request_deserializer=backup__type__pb2.NodeInput.FromString,
                    response_serializer=backup__type__pb2.NodeOutput.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'backup.BackupService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class BackupService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ping(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/ping',
            base__type__pb2.Empty.SerializeToString,
            base__type__pb2.Health.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def create(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/create',
            backup__type__pb2.BackupInput.SerializeToString,
            backup__type__pb2.BackupOutput.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def delete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/delete',
            backup__type__pb2.BackupDeleteInput.SerializeToString,
            backup__type__pb2.BackupOutput.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def restore(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/restore',
            backup__type__pb2.BackupRestoreInput.SerializeToString,
            backup__type__pb2.BackupOutput.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def map_storage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/map_storage',
            backup__type__pb2.StorageInput.SerializeToString,
            base__type__pb2.Output.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def update_storage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/update_storage',
            backup__type__pb2.StorageInput.SerializeToString,
            base__type__pb2.Output.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def delete_storage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/delete_storage',
            backup__type__pb2.StorageInput.SerializeToString,
            base__type__pb2.Output.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def get_node_disk_used_overcommit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/get_node_disk_used_overcommit',
            backup__type__pb2.NodeInput.SerializeToString,
            backup__type__pb2.NodeOutput.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def get_node_disk_used_percent(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/backup.BackupService/get_node_disk_used_percent',
            backup__type__pb2.NodeInput.SerializeToString,
            backup__type__pb2.NodeOutput.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
