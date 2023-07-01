#
# Copyright (c) 2020 FTI-CAS
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from concurrent import futures
from functools import partial

import grpc

from benji import exception as benji_ecx


def get_server(interceptors=None, options=None, workers=4):
    """
    Create a gRPC server
    :return:
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=workers),
                         interceptors=interceptors, options=options)

    return server


class AuthGateway(grpc.AuthMetadataPlugin):

    def __call__(self, context, callback):
        pass


class GRPCClient:
    def __init__(self, host, port, service_module, stub_name, timeout=3600, **kwargs):
        root_certificate = kwargs.get('root_certificate')
        if root_certificate:
            call_credentials = kwargs.get('call_credentials')
            # Call credential object will be invoked for every single RPC
            # Combining channel credentials and call credentials together
            channel_credential = grpc.ssl_channel_credentials(root_certificate)
            credentials = grpc.composite_channel_credentials(channel_credential,
                                                             call_credentials) \
                if call_credentials else channel_credential
            channel = grpc.secure_channel('{0}:{1}'.format(host, port), credentials)
        else:
            channel = grpc.insecure_channel('{0}:{1}'.format(host, port))
        try:
            grpc.channel_ready_future(channel).result(timeout=timeout)
        except grpc.FutureTimeoutError:
            raise benji_ecx.GRCPTimeoutError()

        self.stub = getattr(service_module, stub_name)(channel)
        self.timeout = timeout

    def __getattr__(self, attr):
        return partial(self._wrapped_call, self.stub, attr)

    def _wrapped_call(self, *args, **kwargs):
        try:
            return getattr(args[0], args[1])(args[2], timeout=self.timeout, **kwargs)
        except grpc.RpcError as e:
            message = 'Call {0} failed with {1}'.format(args[1], e.code())
            raise benji_ecx.GRCPError(message)


def get_client(host, port, service_module, stub_name, timeout=3600, **kwargs):
    """
    Get
    :return:
    """
    return GRPCClient(host, port, service_module, stub_name, timeout, **kwargs)

