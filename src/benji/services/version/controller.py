from itertools import groupby

from benji import config as cfg
from benji import exception as bj_exc
from benji import utils, errors
from benji.services import base
from benji.benji import Benji
from benji.helpers import ops_utils
from benji.database import Version, VersionUid, Storage, VersionStatus, VM, User
from benji.services.user.model import UserModel
from benji.utils import hints_from_rbd_diff, InputValidation
from benji.services.version.model import VersionModel
from benji.tasks import backup


class VersionController(base.BaseService):
    def __init__(self, config):
        super(VersionController, self).__init__(config)

    def get_version(self, ctx):
        with VersionModel(self._config) as model:
            version_id = ctx.data['id']
            version = model.get(version_id)
            if version is None:
                ctx.set_error(f'Version {version_id} not found.', status=404)
                return

            ctx.response = version.to_dict()

    def list_versions(self, ctx):
        data = ctx.data
        condition = ''
        with UserModel(self._config) as model:
            if not ctx.is_admin():
                user_name = ctx.target_user.user_name
            else:
                user_name = data.get('user_name', None)

            if user_name is not None:
                condition = "(user_name == '{}')".format(user_name)

            users, objects, prev_page = model.dump_raw_object(ctx, User, condition)
            if users is None or len(users) == 0:
                return

            volume_id = data.get('volume_id', None)
            if volume_id:
                resp = []
                versions = Version.raw_query().filter_by(volume=volume_id).all()
                if len(versions) > 0:
                    volume_dict = {
                        "id": versions[0].volume or volume_id,
                        "name": versions[0].volume_name or None,
                        "versions": [],
                    }
                    for version in versions:
                        volume_dict['versions'].append(version.to_dict())
                    resp.append(volume_dict)
            else:
                storages_dict = {}
                for user in users:
                    storages_dict[user.user_name] = dict(user_name=user.user_name, storage_name=user.user_name, vms=[])

                storage_name = [user.user_name for user in users]
                storages = Storage.raw_query().filter(Storage.name.in_(storage_name)).all()
                storage_ids = [storage.id for storage in storages]

                raw_data = Version.raw_query().filter(Version.storage_id.in_(storage_ids)).all()
                raw_data.sort(key=lambda e: e.storage_id)
                storage_version_group = [list(val) for key, val in groupby(raw_data, lambda x: x.storage_id)]

                for storage_versions in storage_version_group:
                    storage_versions.sort(key=lambda e: e.vm_id)
                    vm_version_group = [list(val) for key, val in groupby(storage_versions, lambda x: x.vm_id)]
                    vms = []
                    storage_id, storage_name, user_name = None, None, None
                    for vm_versions in vm_version_group:
                        volume_version_group = [list(val) for key, val in groupby(vm_versions, lambda x: x.volume)]
                        vm_id, vm_name, volumes = None, None, []
                        for versions in volume_version_group:
                            volume_versions = {
                                "id": versions[0].volume,
                                "name": versions[0].volume_name,
                                "size": None,
                                "versions": [],
                            }

                            for version in versions:
                                storage_id = version.storage_id
                                storage_name = version.storage.name
                                user_name = version.storage.user.user_name
                                volume_versions['versions'].append(version.to_dict())
                            volumes.append(volume_versions)
                        vm = volume_version_group[0][0].vm
                        vms.append(dict(vm_id=vm.id, vm_name=vm.name, volumes=volumes))
                    if storage_id is None:
                        continue
                    storages_dict[storage_name] = dict(user_name=user_name, storage_name=storage_name, vms=vms)

                if ctx.is_admin():
                    resp = list(storages_dict.values())
                else:
                    resp = storages_dict[ctx.target_user.user_name]['vms']

            ctx.response = {
                'data': resp,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
            }

    def build_condition(self, ctx):
        data = ctx.data
        condition = ''
        storages = []
        if ctx.is_admin():
            with UserModel(self._config) as model:
                user_name = data.get('user_name', None)
                users = []
                if user_name is None:
                    users = User.raw_query().limit()
                    users.extend(User.list())
                else:
                    users.append(user_name)
                storages.append(Storage.raw_query().filter(Storage.name.in_(users)).all())
            # storage = Storage.raw_query().filter(Storage.name == user_name).one_or_none()
        else:
            storage = Storage.raw_query().filter(Storage.name == ctx.target_user.user_name).one_or_none()
            if storage is None:
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return
            storages.append(storage)

        if storage:
            condition += " storage_id in '({})' and ".format(",")

        from_date = data.get('from', None)

        if from_date:
            condition += " created_at >= '{}' and ".format(from_date)

        condition += " deleted == '{}' and ".format(False)

        vm_name = data.get('vm_name', None)
        vm = VM.raw_query().filter(VM.name == vm_name).one_or_none()
        if vm:
            condition += " vm_id == '{}' and ".format(vm.id)

        volume_id = data.get('volume_id', None)
        if volume_id:
            condition += " volume == '{}' and ".format(volume_id)

        if condition != '':
            condition = '({})'.format(condition[:-5].strip())
            return condition
        return None

    # def build_new_storage(self, ctx):
    #     data = ctx.data
    #     nodes = Node.raw_query().filter(Node.deleted == False).all()
    #     selected_node = min(nodes, key=lambda x: len(x.storages))
    #     if selected_node is None:
    #         ctx.set_error('Internal Server Error')
    #         return
    #
    #     storage, err = Storage(name=data['storage_name'], module='file', node_id=selected_node.id,
    #                            configuration=dict(path='{}/{}'.format(self._config.get('defaultPath') or "/tmp",
    #                                                                   data['storage_name']))).create()
    #     if err:
    #         ctx.set_error('Internal Server Error')
    #         return
    #
    #     # mapping lvm create storage name
    #     name = storage.name
    #     vg_name = self._config.get('lvm_vg')
    #     lv_thinpool = self._config.get('lvm_lvthinpool')
    #     path = storage.configuration['path']
    #     disk_allowed = storage.disk_allowed
    #
    #     result = backup.map_create_storage(storage.node, name, vg_name, lv_thinpool, path, disk_allowed)
    #     if not result.status:
    #         storage.delete(force=True)
    #         backup.delete_storage(storage.node, name, vg_name, path)
    #         ctx.set_error('Failed to create storage {}'.format(name), status=400)
    #         return
    #     return storage

    def create_version(self, ctx):
        data = ctx.data
        volume_id = data['volume_id']
        volume_name = data.get('volume_name')
        vm_id = data['vm_id']
        rbd_hints = data.get('rbd_hints')
        base_version_uid = data.get('base_version_uid')
        block_size = data.get('block_size')
        is_admin_backup = data.get('is_admin_backup', None)
        wait = data.get('wait') or False

        if ctx.is_admin():
            if is_admin_backup:
                storage_name = ctx.request_user.user_name
            else:
                user_id = data.get('user_id', None)
                storage = Storage.raw_query().filter(Storage.user_id == user_id).one_or_none()
                if storage is None:
                    ctx.set_error('user does not have a storage', status=400)
                    return
                storage_name = storage.name
        else:
            user_id = ctx.target_user.id
            storage_name = ctx.target_user.user_name

        try:
            ops_handler = ops_utils.OpsHandler(cfg.CONF.get('ops_auth', None))
        except bj_exc.BenjiException as e:
            return None
        volume_ops = ops_handler.get_volume_by_id(volume_id)
        if volume_ops is None:
            ctx.set_error('volume id {} is invalid'.format(volume_id), status=400)
            return
        valid_volume = False
        for attachment in volume_ops['attachments']:
            if is_admin_backup:
                vm = VM.raw_query().filter(VM.ems_ref == attachment['server_id']).one_or_none()
            else:
                vm = VM.raw_query().filter(VM.ems_ref == attachment['server_id'], VM.user_id == user_id).one_or_none()
            if vm:
                valid_volume = True
                break

        if not valid_volume:
            ctx.set_error('volume id {} is invalid'.format(volume_id), status=400)
            return

        version_uid = '{}-{}'.format(utils.generate_uuid(), utils.random_string(6))
        source = 'rbd:volumes/volume-{}'.format(volume_id)

        if not InputValidation.is_volume_name(version_uid):
            ctx.set_error('Version name {} is invalid.'.format(version_uid))
            return

        with VersionModel(self._config) as model:
            hints = None
            if rbd_hints:
                with open(rbd_hints, 'r') as f:
                    hints = hints_from_rbd_diff(f.read())

            storage = Storage.get_by_name(storage_name)
            if not storage:
                # storage = self.build_new_storage(ctx)
                # if ctx.failed:
                #     return
                ctx.set_error('user does not have a storage', status=400)
                return

            if storage.disk_used >= storage.disk_allowed:
                ctx.set_error('Backup quota exceeded')
                return

            version, err = model.create(uid=version_uid, volume=volume_id, vm_id=vm_id, volume_name=volume_name,
                                        snapshot='', size=0, block_size=block_size or 0,
                                        storage_id=storage.id, status=VersionStatus.incomplete, protected=False)
            node = dict(host=storage.node.host, port=storage.node.port)
            if wait:
                version_id = backup.create.delay(node, version.id, source, hints, base_version_uid)
                if not version_id:
                    version.delete(True)
                    ctx.set_error('Failed to create backup')
                    return

                version = Version.find_by_id(version_id)
            else:
                backup.create.apply_async(args=[node, version.id, source, base_version_uid])

            ctx.response = version.to_dict()
            ctx.status = 201

    def restore_version(self, ctx):
        data = ctx.data
        wait = data['wait']
        with VersionModel(self._config) as model:
            version = model.get(data['id'])
            if (not version) or (version.status_name == 'incomplete'):
                ctx.set_error('Version id {} is invalid.'.format(data['id']), status=400)
                return

            if not ctx.is_admin() and version.vm.user_id != ctx.target_user.id:
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return

            if version.storage.node.deleted:
                ctx.set_error('Node name {} is not active.'.format(version.storage.node.name), status=400)
                return

            try:
                ops_handler = ops_utils.OpsHandler(cfg.CONF.get('ops_auth', None))
            except bj_exc.BenjiException as e:
                return None

            volume = ops_handler.get_volume_by_id(version.volume)
            if volume is not None:
                if volume['size'] != version.size/(1024**3):
                    ctx.set_error('Allocated size must be equal to Volume size', status=400)
                    return

            node = dict(host=version.storage.node.host, port=version.storage.node.port)
            if wait:
                result = backup.restore.delay(node, data.id, version.volume,
                                              data['sparse'], data['force'], data['database_backend_less'])

                if result:
                    ctx.set_error("Failed")
                    return
                return True
            else:
                backup.restore.apply_async(args=[node, data['id'], version.volume,
                                                 data['sparse'], data['force'], data['database_backend_less']])
            return dict(status=True)

    # def restore_versions(self, ctx):
    #     data = ctx.data
    #     versions = data['versions']
    #
    #     if not versions:
    #         with VersionModel() as model:
    #             for v_id in versions:
    #                 version = model.get(v_id)
    #                 if not version or version.storage.node.deleted:
    #                     continue
    #
    #                 node = dict(host=version.storage.node.host, port=version.storage.node.port)
    #                 backup.restore.apply_async(args=[node, data['id'], version.volume,
    #                                                  data['sparse'], data['force'], data['database_backend_less']])
    #
    #     ctx.set_error(error="Not found versions", status=400)

    def patch_version(self, ctx):
        data = ctx.data

        labels = data['labels']
        protected = data['protected']
        if labels is not None:
            label_add, label_remove = InputValidation.parse_and_validate_labels(labels)
        else:
            label_add, label_remove = [], []
        version_id = data['id']
        with Benji(self._config) as benji_obj:
            version = VersionModel.get(version_id)
            if version is None:
                ctx.set_error(f'Version {version_id} not found.', status=404)
                return
            version_uid_obj = VersionUid(version.uid)
            try:
                if protected is not None:
                    benji_obj.protect(version_uid_obj, protected=protected)

                for name, value in label_add:
                    benji_obj.add_label(version_uid_obj, name, value)
                for name in label_remove:
                    benji_obj.rm_label(version_uid_obj, name)

                ctx.response = version.to_dict()
                ctx.status = 200
            except KeyError:
                ctx.set_error(f'Version {version_id} not found.', status=404)

    def delete_version(self, ctx):
        data = ctx.data
        force = data['force']
        keep_metadata_backup = data['keep_metadata_backup']
        override_lock = data['override_lock']
        version_id = data['id']
        wait = data['wait']
        with VersionModel(self._config) as model:
            version = model.get(data['id'])
            if not version:
                ctx.set_error('Version name {} is invalid.'.format(data['id']))
                return

            if version.storage.node.deleted:
                ctx.set_error('Node name {} is not active.'.format(version.storage.node.name))
                return

            node = dict(host=version.storage.node.host, port=version.storage.node.port)
            if wait:
                version, err = backup.delete.delay(node, version_id, force, keep_metadata_backup, override_lock)
                if err:
                    ctx.set_error(err)
                    return
                return True
            else:
                backup.delete.apply_async(args=[node, version_id, force, keep_metadata_backup, override_lock])

            return True
