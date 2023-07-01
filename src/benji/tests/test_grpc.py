from benji import grpc
from benji.taskmanager.grpc.build import backup_type_pb2 as backup_message
from benji.taskmanager.grpc.build import backup_pb2_grpc as backup_service

# stub = grpc.get_client("0.0.0.0", 55051, backup_service, 'BackupServiceStub')
#
# backup = backup_message.BackupInput(id=1, volume_id="sdsads", source="dsda", hint=None, base_version_uid=None)
# ret = stub.create(backup)
from benji.helpers import utils

try:
    rs_size = utils.subprocess_run(['ls -a'], timeout=10)
    size = rs_size.split()[0]
    print(rs_size)
except Exception as e:
    print(e)
