#
# Copyright (c) 2020 FTI-CAS
#
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from benji import context

from benji.api.v1 import base
from benji.services import NodeController
from benji import config as cfg

auth = base.auth
LOCATION = 'default'

node = NodeController(cfg.CONF)


def do_list_nodes(args):
    ctx = context.create_context(
        task='List backup jobs',
        data=args)
    return base.exec_manager_func(node.list_nodes, ctx)


def do_get_node(args):
    ctx = context.create_context(
        task='Get backup job',
        data=args)
    return base.exec_manager_func(node.get_node, ctx)


def do_create_node(args):
    ctx = context.create_context(
        task='Create backup job',
        data=args)
    return base.exec_manager_func(node.create_node, ctx)


def do_update_node(args):
    ctx = context.create_context(
        task='Update backup job',
        data=args)
    return base.exec_manager_func(node.update_node, ctx)


def do_delete_node(args):
    ctx = context.create_context(
        task='Delete backup job',
        data=args)
    return base.exec_manager_func(node.delete_node, ctx)


class Nodes(Resource):

    get_node_args = {
        **base.PAGING_ARGS
    }

    create_node_args = {
        'name': fields.Str(required=True),
        'host': fields.Str(required=True),
        'port': fields.Integer(required=True),
    }

    @auth.login_required
    @use_args(get_node_args, location=LOCATION)
    def get(self, args):
        return do_list_nodes(args)

    @auth.login_required
    @use_args(create_node_args, location=LOCATION)
    def post(self, args):
        return do_create_node(args)


class Node(Resource):

    get_node_args = {
        **base.PAGING_ARGS
    }

    update_node_args = {

    }

    delete_node_args = {
        'force': fields.Bool(missing=False)
    }

    @auth.login_required
    @use_args(get_node_args, location=LOCATION)
    def get(self, args, id):
        args['id'] = id
        return do_get_node(args)

    @auth.login_required
    @use_args(update_node_args)
    def put(self, args, id):
        args['id'] = id
        return do_update_node(args)

    @auth.login_required
    @use_args(delete_node_args, location=LOCATION)
    def delete(self, args, id):
        args['id'] = id
        return do_delete_node(args)
