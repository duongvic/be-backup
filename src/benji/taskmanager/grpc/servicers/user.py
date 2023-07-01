from benji import config as cfg
from benji.database import Database, User
from benji.helpers import types
from benji.taskmanager.grpc.build import base_type_pb2 as base_message
from benji.taskmanager.grpc.build import user_pb2_grpc as user_service


class UserServicer(user_service.UserServiceServicer):

    def create_user(self, request, context):
        """
        Override this function
        :param request:
        :param context:
        :return:
        """
        Database.configure(cfg.CONF)
        Database.open()
        resp = base_message.Output(status=True, message="SUCCESS")
        role = types.UserRole.parse(request.role)
        user = User.raw_query().filter(User.user_name == request.userid).one_or_none()
        if user:
            resp = base_message.Output(status=False, message="User existed")
            return resp

        user = User(miq_id=request.id, user_name=request.userid, password=request.password_digest,
                    email=request.email, fullname=request.name, status=request.status,
                    enable_two_factors=request.enable_two_factors, user_role=role)
        _, err = user.create()
        if err:
            resp = base_message.Output(status=False, message="Internal Server Error")
        Database.close()
        return resp

    def delete_user(self, request, context):
        """
         Override this function
        :param request:
        :param context:
        :return:
        """
        Database.configure(cfg.CONF)
        Database.open()
        resp = base_message.Output(status=True, message="SUCCESS")

        user = User.raw_query().filter(User.user_name == request.userid).one_or_none()
        if not user:
            resp = base_message.Output(status=False, message="User not found")
            return resp

        user.update(status=False)
        Database.close()
        return resp
