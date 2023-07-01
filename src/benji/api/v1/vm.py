from flask_restful import Resource
from webargs import fields, validate
from webargs.flaskparser import use_args
from benji import context
from benji import config as cfg
from benji.api.v1 import base
from benji.services.vm.controller import VMController


vm = VMController(cfg.CONF)

auth = base.auth
LOCATION = 'default'


def do_list_vms(args):
    ctx = context.create_context(
        task='List vms',
        data=args)
    return base.exec_manager_func(vm.list_vms, ctx)


class VMs(Resource):

    get_vms_args = {
        **base.PAGING_ARGS,
        'name': fields.Str(required=False),
        'user_id': fields.Int(required=False)
    }

    @auth.login_required
    @use_args(get_vms_args, location=LOCATION)
    def get(self, args):
        return do_list_vms(args=args)


def do_create_backups(args):
    ctx = context.create_context(
        task='Create backups',
        data=args)
    return base.exec_manager_func(vm.create_backups, ctx)


class VM(Resource):

    create_backups_args = {
        'volumes': fields.List(fields.Dict(), required=True),
        'vm_id': fields.Int(required=True),
        'rbd_hints': fields.Str(missing=None),
        'base_version_uid': fields.Str(missing=None),
        'block_size': fields.Int(missing=None),
        'wait': fields.Bool(missing=False),
        'is_admin_backup': fields.Bool(required=False),
        'user_id': fields.Int(required=False)
    }

    @auth.login_required
    @use_args(create_backups_args, location=LOCATION)
    def post(self, args):
        return do_create_backups(args=args)


def do_list_vm_volumes(args):
    ctx = context.create_context(
        task='List vm volumes',
        data=args)
    return base.exec_manager_func(vm.list_vm_volumes, ctx)


class VmVolumes(Resource):

    get_vms_args = {
        **base.PAGING_ARGS,
    }

    @auth.login_required
    @use_args(get_vms_args, location=LOCATION)
    def get(self, args, id):
        args['id'] = id
        return do_list_vm_volumes(args=args)


def do_list_volume_groups(args):
    ctx = context.create_context(
        task='List volume groups',
        data=args)
    return base.exec_manager_func(vm.list_volume_groups, ctx)


def do_get_volume_group(args):
    ctx = context.create_context(
        task='Get volume group',
        data=args)
    return base.exec_manager_func(vm.get_volume_group, ctx)


def do_create_volume_group(args):
    ctx = context.create_context(
        task='Create volume group',
        data=args)
    return base.exec_manager_func(vm.create_volume_group, ctx)


def do_update_volume_group(args):
    ctx = context.create_context(
        task='Update volume group',
        data=args)
    return base.exec_manager_func(vm.update_volume_group, ctx)


def do_delete_volume_group(args):
    ctx = context.create_context(
        task='Delete volume group',
        data=args)
    return base.exec_manager_func(vm.delete_volume_group, ctx)


class VolumeGroups(Resource):

    get_volume_group_args = {
        **base.PAGING_ARGS,
        'user_name': fields.Str(required=False),
        'group_name': fields.Str(required=False),
        'user_id': fields.Int(required=False)
    }

    create_volume_group_args = {
        'name': fields.Str(required=True),
        'description': fields.Str(required=False),
        'volumes': fields.List(fields.Dict(), required=True),
        'user_id': fields.Int(required=False)
    }

    @auth.login_required
    @use_args(get_volume_group_args, location=LOCATION)
    def get(self, args):
        return do_list_volume_groups(args)

    @auth.login_required
    @use_args(create_volume_group_args, location=LOCATION)
    def post(self, args):
        return do_create_volume_group(args)


class VolumeGroup(Resource):

    get_volume_group_args = {
        **base.PAGING_ARGS
    }

    update_volume_group_args = {
        'name': fields.Str(required=False),
        'description': fields.Str(required=False),
        'volumes': fields.List(fields.Dict(), required=True),
    }

    delete_volume_group_args = {
        'force': fields.Bool(missing=False)
    }

    @auth.login_required
    @use_args(get_volume_group_args, location=LOCATION)
    def get(self, args, id):
        args['id'] = id
        return do_get_volume_group(args)

    @auth.login_required
    @use_args(update_volume_group_args)
    def put(self, args, id):
        args['id'] = id
        return do_update_volume_group(args)

    @auth.login_required
    @use_args(delete_volume_group_args)
    def delete(self, args, id):
        args['id'] = id
        return do_delete_volume_group(args)


def do_create_volume_backup_group(args):
    ctx = context.create_context(
        task='Create volume backup group',
        data=args)
    return base.exec_manager_func(vm.create_volume_backup_groups, ctx)


class VolumeBackupGroups(Resource):

    create_volume_backup_group_args = {
        'volume_groups': fields.List(fields.Integer(), required=True),
        'block_size': fields.Int(missing=None),
    }

    @auth.login_required
    @use_args(create_volume_backup_group_args, location=LOCATION)
    def post(self, args):
        return do_create_volume_backup_group(args)

