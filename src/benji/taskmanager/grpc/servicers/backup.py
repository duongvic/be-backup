import grpc

from benji import config as cfg
from benji import exception as benji_exc
from benji.benji import Benji
from benji.database import VersionUid, Version, Node, Storage, VersionStatus
from benji.helpers import ceph
from benji.logging import logger
from benji.services.version.model import VersionModel
from benji.taskmanager.grpc.build import base_type_pb2 as base_message
from benji.taskmanager.grpc.build import backup_type_pb2 as backup_message
from benji.taskmanager.grpc.build import backup_pb2_grpc as backup_service
from benji.notification.telegram import services as telegram_service
from benji.notification.email import services as email_service


class BackupServicer(backup_service.BackupServiceServicer):

    def ping(self, request, context):
        reply = base_message.Health(status=True, message="pong")
        return reply

    def create(self, request, context):
        with Benji(cfg.CONF) as benji_obj:
            try:
                version = Version.find_by_id(request.id)
                if version is None:
                    logger.error("Not found version of the identifier {}".format(request.id))
                    return

                base_version_uid = None
                logger.info("Start backing up data of volume of the identifier {}".format(request.source))
                if request.base_version_uid:
                    base_version_uid = VersionUid(request.base_version_uid)
                hints = request.hint
                if hints == '':
                    hints = None

                try:
                    benji_obj.backup(version=version, source=request.source,
                                     hints=hints, base_version_uid=base_version_uid)
                except Exception as e:
                    version.set(status=VersionStatus.invalid)
                    logger.error(e)
                    update_statistic(version, ceph, cfg, logger)
                    if version.storage.disk_used >= version.storage.disk_allowed:
                        telegram_service.alert_failed_to_create_version_when_full_storage(cfg.CONF, version)
                        email_service.alert_when_full_storage(cfg.CONF, version.storage.user.user_name,
                                                              version.storage.user.email,
                                                              int(version.storage.disk_allowed)/(1024**3))
                    reply = backup_message.BackupOutput(id=request.id, status=False)
                    return reply

                update_statistic(version, ceph, cfg, logger)

                reply = backup_message.BackupOutput(id=version.id, status=True)
                logger.info("Backup data of volume of the identifier {} successfully".format(request.source))
                return reply
            except Exception as e:
                version.set(status=VersionStatus.invalid)
                logger.error("Failed to backup volume of the identifier {}. Error: {}".format(request.source, e))
                reply = backup_message.BackupOutput(id=request.id, status=False)
                return reply

    def restore(self, request, context):
        with Benji(cfg.CONF) as benji_obj:
            try:
                version = VersionModel.get(request.id)
                if version is None:
                    logger.error("Not found version of the identifier {}".format(request.id))
                    return

                version_uid_obj = VersionUid(version.uid)
                if request.database_backend_less:
                    benji_obj.metadata_restore([version_uid_obj])

                target = 'rbd:volumes/volume-{}'.format(request.volume_id)
                benji_obj.restore(version_uid_obj, target, request.sparse, request.force)

                reply = backup_message.BackupOutput(id=version.id, status=True)
                return reply
            except Exception as e:
                logger.error("Failed to restore volume of the identifier {}. Error: {}".format(request.volume_id, e))
                reply = backup_message.BackupOutput(id=request.id, status=False)
                return reply

    def delete(self, request, context):
        with Benji(cfg.CONF) as benji_obj:
            try:
                version = VersionModel.get(request.id)
                if version is None:
                    logger.error("Not found version of the identifier {}".format(request.id))
                    return

                version_uid_obj = VersionUid(version.uid)

                benji_obj.rm(version_uid_obj, force=request.force,
                             keep_metadata_backup=request.keep_metadata_backup,
                             override_lock=request.override_lock)

                benji_obj.clean(version.storage)

                try:
                    path = version.storage.configuration['path']
                    storage_size = version.storage.disk_allowed - int(ceph.do_get_storage_disk_available(path))
                    version.storage.update(disk_used=storage_size)

                    lv_thinpool = cfg.CONF.get('lvm_lvthinpool')
                    disk_used_percent = ceph.do_get_node_disk_used_percent(lv_thinpool)
                    version.storage.node.update(disk_used_percent=disk_used_percent)
                except benji_exc.BenjiError as e:
                    logger.error("Failed to delete volume of the identifier {}. Error: {}".format(request.id, e))

                reply = backup_message.BackupOutput(id=version.id, status=True)
                return reply
            except Exception as e:
                logger.error("Failed to delete volume of the identifier {}. Error: {}".format(request.id, e))
                reply = backup_message.BackupOutput(id=request.id, status=False)
                return reply

    def map_storage(self, request, context):
        try:
            with Benji(cfg.CONF) as benji_obj:
                ceph.do_mapping_create_storage_name(request.name, request.vg_name, request.lv_thinpool,
                                                    request.path, request.disk_allowed)
                disk_used_over_commit = ceph.do_get_node_disk_overcommit(request.vg_name, request.lv_thinpool)
                node = Node.find_by_id(request.node_id)
                if node:
                    node.update(disk_used_overcommit=disk_used_over_commit)

                reply = base_message.Output(status=True, message="Success")
                return reply
        except Exception as e:
            logger.error("Failed to map storage. Error: {}".format(e))
            reply = base_message.Output(status=False, message="Failed")
            return reply

    def update_storage(self, request, context):
        try:
            ceph.do_mapping_update_storage_name(request.name, request.vg_name, request.disk_allowed)
            reply = base_message.Output(status=True, message="Success")
            return reply
        except Exception as e:
            logger.error("Failed to update storage. Error: {}".format(e))
            reply = base_message.Output(status=False, message="Failed")
            return reply

    def delete_storage(self, request, context):
        try:
            with Benji(cfg.CONF) as benji_obj:
                ceph.do_mapping_delete_storage_name(request.name, request.vg_name, request.path)
                disk_used_overcommit = ceph.do_get_node_disk_overcommit(request.vg_name, request.lv_thinpool)
                storage = Storage.raw_query().filter(Storage.name == request.name).one_or_none()
                if storage:
                    storage.node.update(disk_used_overcommit=disk_used_overcommit)

                reply = base_message.Output(status=True, message="Success")
                return reply
        except Exception as e:
            logger.error("Failed to delete storage. Error: {}".format(e))
            reply = base_message.Output(status=False, message="Failed")
            return reply

    def get_node_disk_used_overcommit(self, request, context):
        try:
            node_disk_used_overcommit = ceph.do_get_node_disk_overcommit(request.vg_name, request.lv_thinpool)
            reply = backup_message.NodeOutput(overcommit=node_disk_used_overcommit, status=True)
            return reply
        except Exception as e:
            logger.error(e)
            context.set_details("An error occurred when getting node disk.")
            context.set_code(grpc.StatusCode.INTERNAL)
            reply = backup_message.NodeOutput(size=0, status=False)
            return reply

    def get_node_disk_used_percent(self, request, context):
        try:
            node_disk_used_percent = ceph.do_get_node_disk_used_percent(request.lv_thinpool)
            reply = backup_message.NodeOutput(percent=node_disk_used_percent, status=True)
            return reply
        except Exception as e:
            logger.error(e)
            context.set_details("An error occurred when getting node disk.")
            context.set_code(grpc.StatusCode.INTERNAL)
            reply = backup_message.NodeOutput(size=0, status=False)
            return reply


def update_statistic(version, ceph, benji_config, logger):
    logger.info("Updating statistic resource for {}".format(version.storage.configuration['path']))
    try:
        path = version.storage.configuration['path']
        storage_size = version.storage.disk_allowed - int(ceph.do_get_storage_disk_available(path))
        version.storage.update(disk_used=storage_size)

        lv_thinpool = benji_config.CONF.get('lvm_lvthinpool')
        disk_used_percent = ceph.do_get_node_disk_used_percent(lv_thinpool)
        version.storage.node.update(disk_used_percent=disk_used_percent)
    except benji_exc.BenjiError as e:
        logger.error("Fail to update statistic resource {}. Reason: {}".format(
            version.storage.configuration['path'], e.message))

