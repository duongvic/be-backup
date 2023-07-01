#
# Copyright (c) 2020 FTI-CAS
#
from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args

from benji import context
from benji.api.v1 import base
from benji import config as cfg
from benji.services.scrub.controller import ScrubController

scrub = ScrubController(cfg.CONF)

auth = base.auth
LOCATION = 'default'


class DeepScrub(Resource):

    create_deep_scrub_args = {
        'filter_expression': fields.Str(missing=None),
        'version_percentage': fields.Int(missing=100),
        'block_percentage': fields.Int(missing=100),
        'group_label': fields.Str(missing=None)
    }

    @use_args(create_deep_scrub_args, location=LOCATION)
    def post(self, args):
        return do_create_deep_scrub(args=args)


def do_create_deep_scrub(args):

    ctx = context.create_context(
        task='create deep scrub',
        data=args
    )
    return base.exec_manager_func(scrub.create_deep_scrub, ctx)


class Scrub(Resource):

    create_scrub_args = {
        'filter_expression': fields.Str(missing=None),
        'version_percentage': fields.Int(missing=100),
        'block_percentage': fields.Int(missing=100),
        'group_label': fields.Str(missing=None)
    }

    @use_args(create_scrub_args, location=LOCATION)
    def post(self, args):
        return do_create_scrub(args=args)


def do_create_scrub(args):

    ctx = context.create_context(
        task='create scrub',
        data=args
    )
    return base.exec_manager_func(scrub.create_scrub, ctx)