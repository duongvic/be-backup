from benji import errors
from benji.database import Storage, User
from benji.services import base
from benji.services.storage.model import StorageModel
from benji.tasks import backup


class StorageController(base.BaseService):
    def __init__(self, config):
        super(StorageController, self).__init__(config)

    def get_storage(self, ctx):
        with StorageModel(self._config) as model:
            storage = model.get(ctx.data['id'])
            if (storage is None) or (not ctx.is_admin()):
                ctx.set_error("Not found item", status=404)
                return

            ctx.response = storage.to_dict()

    def list_storages(self, ctx):
        condition = ''
        data = ctx.data
        storage_name = data.get('storage_name', None)
        if storage_name:
            condition = " name == '{}' and ".format(storage_name)
        if condition != '':
            condition = '{}'.format(condition[:-5].strip())

        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with StorageModel(self._config) as model:
            model.dump_object(ctx, Storage, condition)

    def create_storage(self, ctx):
        with StorageModel(self._config) as model:
            data = ctx.data
            data['module'] = 'file'
            user = ctx.target_user

            if not ctx.is_admin():
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return

            user_id = data.pop('user_id', None)
            if user_id:
                user = User.find_by_id(user_id)
                if not user:
                    ctx.set_error(errors.USER_NOT_FOUND, status=404)
                    return
                else:
                    storage = Storage.raw_query().filter(Storage.user_id == user_id).one_or_none()
                    if storage is not None:
                        ctx.set_error('User already have a storage', status=400)
                        return

            data['user_id'] = user.id
            data['name'] = user.user_name
            data['configuration'] = dict(path='{}/{}'.format(self._config.get('defaultPath') or "/tmp", user.user_name))
            data['disk_allowed'] = data['disk_allowed'] * (1024 ** 3)

            obj, err = model.create(**data)
            if err:
                ctx.set_error(err, status=400)
                return

            # mapping lvm create storage name
            vg_name = self._config.get('lvm_vg')
            lv_thinpool = self._config.get('lvm_lvthinpool')
            path = obj.configuration['path']
            disk_allowed = obj.disk_allowed

            result = backup.map_create_storage(obj.node, obj.name, vg_name, lv_thinpool, path, disk_allowed)
            if not result.status:
                obj.delete(force=True)
                ctx.set_error('Failed to create storage {}'.format(obj.name), status=400)
                return

            ctx.response = obj.to_dict()
            ctx.status = 201

    def update_storage(self, ctx):
        data = ctx.data
        with StorageModel(self._config) as model:
            storage = model.get(data.pop('id', None))
            if (storage is None) or (not ctx.is_admin()):
                ctx.set_error("Not found item", status=404)
                return

            # mapping lvm update storage name
            if data['disk_allowed']:
                data['disk_allowed'] = data['disk_allowed'] * (1024 ** 3)
                if data['disk_allowed'] <= storage.disk_allowed:
                    ctx.set_error('disk_allowed must be greater than {}'.format(storage.disk_allowed/(1024**3)), status=400)
                    return
                name = storage.name
                vg_name = self._config.get('lvm_vg')
                result = backup.update_storage(storage.node, name, vg_name, data['disk_allowed'])
                if not result.status:
                    ctx.set_error('Failed to update storage {}'.format(name), status=400)
                    return

            obj, err = model.update(storage.id, **ctx.data)
            if err:
                ctx.set_error('Failed to update storage', status=400)
                return

            ctx.response = obj.to_dict()

    def delete_storage(self, ctx):
        data = ctx.data
        with StorageModel(self._config) as model:
            storage = model.get(data.pop('id', None))
            if (storage is None) or (not ctx.is_admin()):
                ctx.set_error("Not found item", status=404)
                return

            # mapping lvm delete storage name
            name = storage.name
            vg_name = self._config.get('lvm_vg')
            lv_thinpool = self._config.get('lvm_lvthinpool')
            path = storage.configuration['path']
            result = backup.delete_storage(storage.node, name, vg_name, lv_thinpool, path)
            if not result.status:
                ctx.set_error('Failed to delete storage {}'.format(name), status=400)
                return

            obj, err = model.delete(storage.id, data['force'])
            if err:
                ctx.set_error('Failed to delete storage', status=400)
                return

            return dict(status=True)
