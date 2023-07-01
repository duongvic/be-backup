from benji import grpc
from benji.logging import logger
from benji.taskmanager.grpc.build import mail_types_pb2 as mail_message
from benji.taskmanager.grpc.build import mails_pb2_grpc as mail_service


def alert_when_full_storage(config, user_name, email, disk_allowed):
    email_grpc_server_host = config.get('cas_mail_api_host')
    email_grpc_server_port = config.get('cas_mail_api_port')
    try:
        stub = grpc.get_client(email_grpc_server_host, email_grpc_server_port,
                               mail_service, 'MailServiceStub')
        user = mail_message.User(
            user_name=user_name,
            email=email
        )
        request = mail_message.FullStorageIssue(
            user=user,
            disk_allowed=str(disk_allowed),
        )
        response = stub.send_full_storage_issue(request)
        return response.status
    except Exception as e:
        logger.error('Error occurred while sending the email: ' + str(e))
        return False
