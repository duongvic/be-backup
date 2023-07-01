#
# Copyright (c) 2020 FTI-CAS
#
from flask_restful import Resource
from webargs import fields, validate
from webargs.flaskparser import use_args

from benji import context
from benji.api.v1 import base
from benji import config as cfg
from benji.services.storage.controller import StorageController

storage = StorageController(cfg.CONF)

auth = base.auth
LOCATION = 'default'


def do_get_storage(args):

    ctx = context.create_context(
        task='Get storage',
        data=args
    )
    return base.exec_manager_func(storage.get_storage, ctx)


def do_list_storages(args):

    ctx = context.create_context(
        task='List storages',
        data=args
    )
    return base.exec_manager_func(storage.list_storages, ctx)


def do_create_storage(args):

    ctx = context.create_context(
        task='Create storage',
        data=args
    )
    return base.exec_manager_func(storage.create_storage, ctx)


def do_update_storage(args):

    ctx = context.create_context(
        task='Update storage',
        data=args
    )
    return base.exec_manager_func(storage.update_storage, ctx)


def do_delete_storage(args):

    ctx = context.create_context(
        task='Delete storage',
        data=args
    )
    return base.exec_manager_func(storage.delete_storage, ctx)


class Storages(Resource):

    get_storages_args = {
        **base.PAGING_ARGS,
        'storage_name': fields.Str(required=False)
    }

    create_storage_args = {
        'user_id': fields.Int(required=False),
        'disk_allowed': fields.Int(required=True, validate=[validate.Range(min=1)])
    }

    @auth.login_required
    @use_args(get_storages_args, location=LOCATION)
    def get(self, args):
        return do_list_storages(args=args)

    @auth.login_required
    @use_args(create_storage_args, location=LOCATION)
    def post(self, args):
        return do_create_storage(args=args)


class Storage(Resource):

    get_storage_args = {
        'storage_name': fields.Str(required=False)
    }

    update_storage_args = {
        'disk_allowed': fields.Int(required=False, missing=0)
    }

    delete_storage_args = {
        'force': fields.Bool(missing=True)
    }

    @auth.login_required
    @use_args(get_storage_args, location=LOCATION)
    def get(self, args, id):
        args['id'] = id
        return do_get_storage(args=args)

    @auth.login_required
    @use_args(update_storage_args, location=LOCATION)
    def put(self, args, id):
        args['id'] = id
        return do_update_storage(args=args)

    @auth.login_required
    @use_args(delete_storage_args)
    def delete(self, args, id):
        args['id'] = id
        return do_delete_storage(args)
