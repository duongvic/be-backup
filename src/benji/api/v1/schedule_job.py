#
# Copyright (c) 2020 FTI-CAS
#
from flask_restful import Resource
from webargs import fields, validate
from webargs.flaskparser import use_args

from benji import context

from benji.api.v1 import base
from benji.services import ScheduleJobController
from benji import config as cfg

auth = base.auth
LOCATION = 'default'

schedule_job = ScheduleJobController(cfg.CONF)


def do_list_schedule_jobs(args):
    ctx = context.create_context(
        task='List backup jobs',
        data=args)
    return base.exec_manager_func(schedule_job.list_schedule_jobs, ctx)


def do_get_schedule_job(args):
    ctx = context.create_context(
        task='Get backup job',
        data=args)
    return base.exec_manager_func(schedule_job.get_schedule_job, ctx)


def do_create_schedule_job(args):
    ctx = context.create_context(
        task='Create backup job',
        data=args)
    return base.exec_manager_func(schedule_job.create_schedule_job, ctx)


def do_update_schedule_job(args):
    ctx = context.create_context(
        task='Update backup job',
        data=args)
    return base.exec_manager_func(schedule_job.update_schedule_job, ctx)


def do_delete_schedule_job(args):
    ctx = context.create_context(
        task='Delete backup job',
        data=args)
    return base.exec_manager_func(schedule_job.delete_schedule_job, ctx)


class ScheduleJobs(Resource):

    get_schedule_job_args = {
        **base.PAGING_ARGS,
        'user_name': fields.Str(required=False)
    }

    create_schedule_job_args = {
        'group_id': fields.Int(required=True),
        'name': fields.Str(required=False),
        'mode': fields.Str(required=True, validate=validate.OneOf(['SNAPSHOT', "BACKUP"])),
        'days_of_week': fields.List(fields.Str(validate=validate.OneOf(['mon', 'tue', 'wed',
                                                                        'thu', 'fri', 'sat', 'sun'])), required=True),
        'start_time': fields.Int(required=True),
        'compression': fields.Str(required=False),
        'retention': fields.Int(required=True),
        'user_id': fields.Int(required=False)
    }

    @auth.login_required
    @use_args(get_schedule_job_args, location=LOCATION)
    def get(self, args):
        return do_list_schedule_jobs(args)

    @auth.login_required
    @use_args(create_schedule_job_args, location=LOCATION)
    def post(self, args):
        return do_create_schedule_job(args)


class ScheduleJob(Resource):

    get_schedule_job_args = {
        **base.PAGING_ARGS
    }

    update_schedule_job_args = {
        'name': fields.Str(required=False),
        'mode': fields.Str(required=False, validate=validate.OneOf(['SNAPSHOT', "BACKUP"])),
        'days_of_week': fields.List(fields.Str(validate=validate.OneOf(['mon', 'tue', 'wed',
                                                                        'thu', 'fri', 'sat', 'sun'])), required=False),
        'start_time': fields.Int(required=False),
        'compression': fields.Str(required=False),
        'retention': fields.Int(required=False),
        'user_name': fields.Str(required=False)
    }

    delete_schedule_job_args = {
        'force': fields.Bool(missing=False)
    }

    @auth.login_required
    @use_args(get_schedule_job_args, location=LOCATION)
    def get(self, args, id):
        args['id'] = id
        return do_get_schedule_job(args)

    @auth.login_required
    @use_args(update_schedule_job_args)
    def put(self, args, id):
        args['id'] = id
        return do_update_schedule_job(args)

    @auth.login_required
    @use_args(delete_schedule_job_args)
    def delete(self, args, id):
        args['id'] = id
        return do_delete_schedule_job(args)
