from benji.cmd.common import with_initialize


@with_initialize
def main(conf):
    from benji.helpers.grpc import service
    grpc_service = service.GRPCService(conf.get('bind_host', '0.0.0.0'),
                                       conf.get('bind_grpc_port', 55051),
                                       thread_workers=conf.get('thread_workers', 2),
                                       managers=conf.get('grpc_managers', None))
    grpc_service.start()


if __name__ == '__main__':
    main()
