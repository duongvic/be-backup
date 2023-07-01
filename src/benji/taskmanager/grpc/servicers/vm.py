from benji import config as cfg
from benji.database import Database, VM, User
from benji.taskmanager.grpc.build import base_type_pb2 as base_message
from benji.taskmanager.grpc.build import vm_pb2_grpc as vm_service


class VMServicer(vm_service.VMServiceServicer):

    def create_vm(self, request, context):
        """
        Override this function
        :param request:
        :param context:
        :return:
        """
        Database.configure(cfg.CONF)
        Database.open()
        resp = base_message.Output(status=True, message="SUCCESS")

        user = User.raw_query().filter(User.miq_id == request.user_id).one_or_none()
        if not user:
            resp = base_message.Output(status=False, message="Not found user")
            return resp

        vm = VM(name=request.name, ems_ref=request.ems_ref, user_id=user.id)
        _, err = vm.create()
        if err:
            resp = base_message.Output(status=True, message="Internal Server Error")

        return resp

    def delete_vm(self, request, context):
        """
         Override this function
        :param request:
        :param context:
        :return:
        """
        resp = base_message.Output(status=True, message="SUCCESS")
        # TODO(khanhct)

        return resp
