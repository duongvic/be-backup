from benji import errors, config as cfg, utils
from benji import exception as bj_exc
from benji.helpers import ops_utils
from benji.services import base
from benji.database import VM, VolumeGroup, Version, Storage, VersionStatus, User, ScheduleJob
from benji.services.version.model import VersionModel
from benji.services.vm.model import VMModel, VolumeGroupModel, VolumeBackupGroup
from benji.tasks import backup
from benji.utils import hints_from_rbd_diff, InputValidation


class VMController(base.BaseService):
    def __init__(self, config):
        super(VMController, self).__init__(config)

    def list_vms(self, ctx):
        response = {}
        with VMModel(self._config) as model:
            condition = self.build_condition(ctx)
            vms, objects, prev_page = model.dump_raw_object(ctx, VM, condition)
            result = []

            if not vms:
                return None

            try:
                ops_handler = ops_utils.OpsHandler(cfg.CONF.get('ops_auth', None))
            except bj_exc.BenjiException as e:
                return None

            for vm in vms:
                data = ops_handler.list_volumes(vm.ems_ref)
                vm_dict = vm.to_dict() if ctx.is_admin() else vm.to_user_dict()
                vm_dict['volumes'] = data
                if data is not None:
                    for dat in data:
                        volumebackupgroup = VolumeBackupGroup.raw_query().filter(VolumeBackupGroup.vm_id == vm.id, VolumeBackupGroup.volume_id == dat['id']).one_or_none()
                        if volumebackupgroup:
                            dat.update(in_group=True)
                        else:
                            dat.update(in_group=False)
                result.append(vm_dict)

            response = {
                'data': result,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
            }

            ctx.response = response

    def build_condition(self, ctx):
        data = ctx.data
        condition = ''
        name = data.get('name', None)
        if name:
            condition += " name == '{}' and ".format(name)

        user_id = data.get('user_id', None)
        if ctx.is_admin() and (user_id is not None):
            user = User.raw_query().filter(User.id == user_id).one_or_none()
            if user is None:
                ctx.set_error(errors.USER_NOT_FOUND, status=404)
                return
            condition += " user_id == '{}' and ".format(user_id)

        if condition != '':
            condition = '({})'.format(condition[:-5].strip())
            return condition
        return None

    def list_vm_volumes(self, ctx):
        try:
            ops_handler = ops_utils.OpsHandler(cfg.CONF.get('ops_auth', None))
        except bj_exc.BenjiException as e:
            ctx.set_error(str(e), status=400)
            return

        with VMModel(self._config) as model:
            vm = model.get(ctx.data['id'])
            if vm is None:
                ctx.set_error('Not found item', status=404)
                return

            if not ctx.is_admin():
                if vm.user_id != ctx.target_user.id:
                    ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=400)
                    return
            data = ops_handler.list_volumes(vm.ems_ref)

            ctx.response = data

    def list_volume_groups(self, ctx):
        """

        :param ctx:
        :return:
        """
        result = []
        with VolumeGroupModel(self._config) as model:
            condition = self.build_condition_list_groups(ctx)
            groups, objects, prev_page = model.dump_raw_object(ctx, VolumeGroup, condition)
            for group in groups:
                group_dict = group.to_user_dict()
                if ctx.is_admin():
                    group_dict.update(user_name=group.user.user_name, created_at=group.created_at, updated_at=group.updated_at)
                job = ScheduleJob.raw_query().filter(ScheduleJob.group_id == group.id).one_or_none()
                if job:
                    group_dict.update(in_job=True)
                else:
                    group_dict.update(in_job=False)
                result.append(group_dict)

            ctx.response = {
                'data': result,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
            }


    def build_condition_list_groups(self, ctx):
        data = ctx.data
        condition = ''
        group_name = data.get('group_name', None)

        if ctx.is_admin():
            user_name = data.get('user_name', None)
            user_id = data.get('user_id', None)
            user = User.get_by_username(user_name)
            if user_id is not None:
                condition += " user_id == '{}' and ".format(user_id)
            elif user is not None:
                condition += " user_id == '{}' and ".format(user.id)

        if group_name:
            condition += " name == '{}' and ".format(group_name)

        if condition != '':
            condition = '({})'.format(condition[:-5].strip())
            return condition
        return None

    def get_volume_group(self, ctx):
        """

        :param ctx:
        :return:
        """
        with VolumeGroupModel(self._config) as model:
            group = model.get(ctx.data['id'])
            if not ctx.is_admin() and (group is None or group.user_id != ctx.target_user.id):
                ctx.set_error("Not found item", status=404)
                return

            ctx.response = group.to_dict()

    def create_volume_group(self, ctx):
        """

        :param ctx:
        :return:
        """
        with VolumeGroupModel(self._config) as model:
            data = ctx.data
            if not ctx.is_admin():
                data['user_id'] = ctx.target_user.id
            volumes = data['volumes']

            try:
                ops_handler = ops_utils.OpsHandler(cfg.CONF.get('ops_auth', None))
            except bj_exc.BenjiException as e:
                return None
            for volume in volumes:
                volume_group = VolumeBackupGroup.raw_query().filter(VolumeBackupGroup.volume_id == volume['id']).one_or_none()
                if volume_group is not None:
                    ctx.set_error('{} already exist in volumebackupgroup'.format(volume_group.volume_id), status=400)
                    return
                volume_ops = ops_handler.get_volume_by_id(volume['id'])
                if volume_ops is None:
                    ctx.set_error('volume id {} is invalid'.format(volume['id']), status=400)
                    return
                valid_volume = False
                for attachment in volume_ops['attachments']:
                    vm = VM.raw_query().filter(VM.ems_ref == attachment['server_id'], VM.user_id == data['user_id']).one_or_none()
                    if vm:
                        valid_volume = True
                        break

                if not valid_volume:
                    ctx.set_error('volume id {} is invalid'.format(volume['id']), status=400)
                    return

            obj, err = model.create(**data)
            if err:
                ctx.set_error('Failed to create backup group', status=400)
                return

            ctx.response = obj.to_dict()
            ctx.status = 201

    def update_volume_group(self, ctx):
        """

        :param ctx:
        :return:
        """
        data = ctx.data
        with VolumeGroupModel(self._config) as model:
            group = model.get(data.pop('id', None))

            if not ctx.is_admin() and (group is None or group.user_id != ctx.target_user.id):
                ctx.set_error("Not found item", status=404)
                return

            obj, err = model.update(group.id, **ctx.data)
            if err:
                ctx.set_error('Failed to update backup group', status=400)
                return

            ctx.response = obj.to_dict()

    def delete_volume_group(self, ctx):
        """

        :param ctx:
        :return:
        """
        data = ctx.data
        group_id = data.pop('id', None)
        with VolumeGroupModel(self._config) as model:
            group = model.get(group_id)
            if group is None:
                ctx.set_error("Not found item", status=404)
                return

            if not ctx.is_admin() and (group.user_id != ctx.target_user.id):
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return

            _, err = model.delete(group_id, data['force'])
            if err:
                ctx.set_error(err, status=400)
                return

            return

    def create_volume_backup_groups(self, ctx):
        """

        :param ctx:
        :return:
        """
        volume_groups = ctx.data['volume_groups']
        block_size = ctx.data['block_size']
        versions = []
        with VolumeGroupModel(self._config) as model:
            storage = Storage.get_by_name(ctx.target_user.user_name)
            if not storage:
                ctx.set_error("Not found storage", status=400)

            for group_id in volume_groups:
                vol_bk_groups = VolumeBackupGroup.raw_query().filter(VolumeBackupGroup.group_id == group_id).all()
                if vol_bk_groups:
                    _versions = self.create_backup(storage, vol_bk_groups, block_size)
                    versions.extend(_versions)
        response = []
        for version in versions:
            response.append(version.to_dict())
        ctx.response = response

    def create_backup(self, storage, vol_bk_groups, block_size=None):
        versions = []
        for vol_bk in vol_bk_groups:
            volume_id = vol_bk.volume_id
            version_uid = '{}-{}'.format(utils.generate_uuid(), utils.random_string(6))
            source = 'rbd:volumes/volume-{}'.format(volume_id)
            version, err = Version(uid=version_uid, volume=volume_id, snapshot='', size=0,
                                   block_size=block_size or 0, storage_id=storage.id,
                                   status=VersionStatus.incomplete, protected=False).create()
            if err:
                continue

            node = dict(host=storage.node.host, port=storage.node.port)
            backup.create.apply_async(args=[node, version.id, source, None])
            versions.append(version)
        return versions

    def create_backups(self, ctx):
        data = ctx.data
        volumes = data['volumes']
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

        hints = None
        if rbd_hints:
            with open(rbd_hints, 'r') as f:
                hints = hints_from_rbd_diff(f.read())

        storage = Storage.get_by_name(storage_name)
        if not storage:
            ctx.set_error('user does not have a storage', status=400)
            return

        if storage.disk_used >= storage.disk_allowed:
            ctx.set_error('Backup quota exceeded')
            return

        response = []
        try:
            ops_handler = ops_utils.OpsHandler(cfg.CONF.get('ops_auth', None))
        except bj_exc.BenjiException as e:
            return None
        for volume in volumes:
            volume_ops = ops_handler.get_volume_by_id(volume['id'])
            if volume_ops is None:
                ctx.set_error('volume id {} is invalid'.format(volume['id']), status=400)
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
                ctx.set_error('volume id {} is invalid'.format(volume['id']), status=400)
                return

        for volume in volumes:
            version_uid = '{}-{}'.format(utils.generate_uuid(), utils.random_string(6))
            source = 'rbd:volumes/volume-{}'.format(volume['id'])

            with VersionModel(self._config) as model:
                version, err = model.create(uid=version_uid, volume=volume['id'], vm_id=vm_id, volume_name=volume['name'] or None,
                                            snapshot='', size=0, block_size=block_size or 0,
                                            storage_id=storage.id, status=VersionStatus.incomplete, protected=False)

                if err:
                    continue

                node = dict(host=storage.node.host, port=storage.node.port)
                backup.create.apply_async(args=[node, version.id, source, None])
                response.append(version.to_dict())

        ctx.response = response
        ctx.status = 201

