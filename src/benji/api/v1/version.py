#
# Copyright (c) 2020 FTI-CAS
#
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from benji import context
from benji.api.v1 import base
from benji import config as cfg
from benji.services.version.controller import VersionController

version = VersionController(cfg.CONF)

auth = base.auth
LOCATION = 'default'


def do_get_version(args):
    """
    Get existed version
    Args:
        args:

    Returns:
    """
    ctx = context.create_context(
        task='Get version',
        data=args)
    return base.exec_manager_func(version.get_version, ctx)


def do_get_versions(args):
    ctx = context.create_context(
        task='Get versions',
        data=args)
    return base.exec_manager_func(version.list_versions, ctx)


def do_create_version(args):
    """
    Create new version
    Args:
        args:

    Returns:
    """
    ctx = context.create_context(
        task='Create version',
        data=args)
    return base.exec_manager_func(version.create_version, ctx)


def do_restore_version(args):
    """
    Restore new version
    Args:
        args:

    Returns:
    """
    ctx = context.create_context(
        task='Restore version',
        data=args)
    return base.exec_manager_func(version.restore_version, ctx)


def do_patch_version(args):
    ctx = context.create_context(
        task='Get version',
        data=args)
    return base.exec_manager_func(version.patch_version, ctx)


def do_delete_version(args):
    ctx = context.create_context(
        task='Delete version',
        data=args)
    return base.exec_manager_func(version.delete_version, ctx)


def do_restore_versions(args):
    ctx = context.create_context(
        task='Restore versions',
        data=args)
    return base.exec_manager_func(version.restore_versions, ctx)


class Versions(Resource):
    get_version_args = {
        **base.PAGING_ARGS,
        'volume_id': fields.Str(missing=None),
        'vm_name': fields.Str(missing=None),
        'from': fields.Str(missing=None),
        'user_name': fields.Str(missing=None),
    }

    create_version_args = {
        'volume_id': fields.Str(required=True),
        'volume_name': fields.Str(required=False),
        'vm_id': fields.Int(required=True),
        'rbd_hints': fields.Str(missing=None),
        'base_version_uid': fields.Str(missing=None),
        'block_size': fields.Int(missing=None),
        'wait': fields.Bool(missing=False),
        'is_admin_backup': fields.Bool(required=False),
        'user_id': fields.Int(required=False)
    }

    restore_version_args = {
        'versions':  fields.List(fields.Str())
    }

    @auth.login_required
    @use_args(create_version_args, location=LOCATION)
    def post(self, args):
        return do_create_version(args=args)

    @auth.login_required
    @use_args(get_version_args, location=LOCATION)
    def get(self, args):
        return do_get_versions(args=args)

    @auth.login_required
    @use_args(restore_version_args, location=LOCATION)
    def put(self, args):
        return do_restore_versions(args=args)


class Version(Resource):
    get_version_args = {}

    restore_version_args = {
        'sparse': fields.Bool(missing=False),
        'force': fields.Bool(missing=False),
        'database_backend_less': fields.Bool(missing=False),
        'wait': fields.Bool(missing=False)
    }

    patch_version_args = {
        'protected': fields.Bool(missing=None),
        'labels': fields.DelimitedList(fields.Str(), missing=None)
    }

    delete_version_args = {
        'force': fields.Bool(missing=True),
        'keep_metadata_backup': fields.Bool(missing=False),
        'override_lock': fields.Bool(missing=False),
        'wait': fields.Bool(missing=False)
    }

    @auth.login_required
    @use_args(get_version_args, location=LOCATION)
    def get(self,  args, id):
        args['id'] = id
        return do_get_version(args=args)

    @auth.login_required
    @use_args(restore_version_args, location=LOCATION)
    def post(self,  args, id):
        args['id'] = id
        return do_restore_version(args=args)

    @auth.login_required
    @use_args(patch_version_args, location=LOCATION)
    def patch(self, args, id):
        args['id'] = id
        return do_patch_version(args=args)

    @auth.login_required
    @use_args(delete_version_args, location=LOCATION)
    def delete(self, args, id):
        args['id'] = id
        return do_delete_version(args=args)
