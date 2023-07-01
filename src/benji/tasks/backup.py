from benji import grpc, config as cfg
from benji.celery import app
from benji.database import VersionUid
from benji.logging import logger
from benji.taskmanager.grpc.build import base_type_pb2 as base_message
from benji.taskmanager.grpc.build import backup_type_pb2 as backup_message
from benji.taskmanager.grpc.build import backup_pb2_grpc as backup_service
from benji.services.node.model import NodeModel


@app.task()
def monitor_nodes():
    with NodeModel(cfg.CONF) as model:
        nodes = model.list()
        for node in nodes:
            try:
                logger.debug("Check health node {}".format(node.name))
                stub = grpc.get_client(node.host, node.port, backup_service, 'BackupServiceStub', timeout=10)
                backup = base_message.Empty()
                stub.ping(backup)
                node.update(deleted=False)
            except Exception as e:
                node.update(deleted=True)
                logger.error('Error occurred during check health node {}. Reason: {}'.format(node.host, e))


@app.task()
def create(node, version_id, source: str, base_version_uid: VersionUid = None):
    try:
        stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
        backup = backup_message.BackupInput(id=version_id, source=source, hint=None, base_version_uid=base_version_uid)
        stub.create(backup)
    except Exception as e:
        logger.error(e)


@app.task()
def restore(node, version_id, volume_id, sparse, force, database_backend_less):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    backup = backup_message.BackupRestoreInput(id=version_id, volume_id=volume_id,
                                               sparse=sparse, force=force, database_backend_less=database_backend_less)
    stub.restore(backup)


@app.task()
def delete(node, version_id, force, keep_metadata_backup, override_lock):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    backup = backup_message.BackupDeleteInput(id=version_id, force=force, keep_metadata_backup=keep_metadata_backup,
                                              override_lock=override_lock)
    stub.delete(backup)


def map_create_storage(node, name, vg_name, lv_thinpool, path, disk_allowed):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    storage = backup_message.StorageInput(node_id=node['id'], name=name, vg_name=vg_name, lv_thinpool=lv_thinpool,
                                          path=path, disk_allowed=disk_allowed)
    return stub.map_storage(storage)


def update_storage(node, name, vg_name, disk_allowed):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    storage = backup_message.StorageInput(node_id=node.id, name=name, vg_name=vg_name, disk_allowed=disk_allowed)
    return stub.update_storage(storage)


def delete_storage(node, name, vg_name, lv_thinpool, path):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    storage = backup_message.StorageInput(node_id=node.id, name=name, vg_name=vg_name,
                                          lv_thinpool=lv_thinpool, path=path)
    return stub.delete_storage(storage)


def get_node_disk_used_overcommit(node, vg_name, lv_thinpool):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    storage = backup_message.NodeInput(vg_name=vg_name, lv_thinpool=lv_thinpool)
    return stub.get_node_disk_used_overcommit(storage)


def get_node_disk_used_percent(node, lv_thinpool):
    stub = grpc.get_client(node['host'], node['port'], backup_service, 'BackupServiceStub')
    storage = backup_message.NodeInput(lv_thinpool=lv_thinpool)
    return stub.get_node_disk_used_percent(storage)
