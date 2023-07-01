#
# Copyright (c) 2020 FTI-CAS
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import importlib
import multiprocessing
import time
import grpc

from benji import grpc as _grpc
from benji import config as cfg
from benji import exception as bj_exc
from benji.helpers.grpc import credentials


CONF = cfg.CONF
_ONE_DAY = datetime.timedelta(days=1)
_PROCESS_COUNT = multiprocessing.cpu_count()
_THREAD_CONCURRENCY = _PROCESS_COUNT
_LISTEN_ADDRESS_TEMPLATE = '%s:%d'


class GRPCService(object):
    def __init__(self, host=None, port=None, interceptors=None, thread_workers=None,
                 managers=None, **kwargs):
        self.host = host
        self.port = port
        self.grpc_server = None
        self.interceptors = interceptors
        self.thread_workers = thread_workers or _THREAD_CONCURRENCY
        self.options = kwargs
        self.managers = managers or []

    def parse_cfg(self):
        """
        Parse config
        :return:
        """
        def _parse(cfg_str):
            try:
                objs = cfg_str.split(".")
                obj_fnc = objs.pop(len(objs) - 1)
                obj_mod_uri = ".".join(s for s in objs)
                service_mod = importlib.import_module(obj_mod_uri)
                return getattr(service_mod, obj_fnc)
            except:
                return None

        for manager in self.managers:
            fnc = _parse(manager['service'])
            cls = _parse(manager['servicer'])
            if fnc and cls:
                yield fnc, cls

    def start(self):
        """
        Start GRPC server
        :return:
        """
        self.grpc_server = _grpc.get_server(self.interceptors, self.options, self.thread_workers)

        # Register servicers
        for fnc, cls in self.parse_cfg():
            fnc(cls(), self.grpc_server)

        # Loading credentials
        if CONF.get('enable_secure_grpc_messaging', False):
            server_credentials = grpc.ssl_server_credentials(((credentials.SERVER_CERTIFICATE_KEY,
                                                               credentials.SERVER_CERTIFICATE,),))
            # Pass down credentials
            self.grpc_server.add_secure_port(_LISTEN_ADDRESS_TEMPLATE % (self.host, self.port),
                                             server_credentials)
        else:
            self.grpc_server.add_insecure_port(_LISTEN_ADDRESS_TEMPLATE % (self.host, self.port))

        self.grpc_server.start()
        self._wait_forever()

    def _wait_forever(self):
        try:
            while True:
                time.sleep(_ONE_DAY.total_seconds())
        except KeyboardInterrupt:
            self.grpc_server.stop(None)

    def stop(self, graceful=False):
        """
        Stop GRPC server
        :param graceful:
        :return:
        """

        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.grpc_server.stop()
        except Exception as e:
            # LOG.info("Failed to stop gRPC server before shutdown. ")
            pass
