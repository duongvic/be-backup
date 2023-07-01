from os import environ as env

from flask_httpauth import HTTPTokenAuth
from flask_restful import abort
from webargs import fields, validate
from webargs.flaskparser import parser
from webargs.multidictproxy import MultiDictProxy

from benji import app
from benji.database import User
from benji.helpers import json as app_json

auth = HTTPTokenAuth(scheme='Bearer')
maintenance = env.get('CAS_MAINTENANCE', '').lower() in ('true', '1', 'on', 'yes')

LIST_ITEMS_PER_PAGE = 10
LIST_MAX_ITEMS_PER_PAGE = 1000

PAGING_ARGS = {
    'page': fields.Int(required=False, missing=0),
    'page_size': fields.Int(
        required=False,
        missing=LIST_ITEMS_PER_PAGE,
        validate=[validate.Range(min=1, max=LIST_MAX_ITEMS_PER_PAGE)]),
    'sort_by': fields.List(fields.Str(), required=False),  # form: col1,col2__desc,col3__asc default asc
}

GET_OBJECT_ARGS = {
    **PAGING_ARGS,
}
LIST_OBJECTS_ARGS = {
    **PAGING_ARGS,
}


class ApiJSONEncoder(app_json.AppJSONEncoder):
    """
    JSON encoder for API.
    """


# Set some configurations
app.config['RESTFUL_JSON'] = {
    'cls': ApiJSONEncoder,
}


@auth.verify_token
def verify_request_token(token):
    if not token:
        return None

    return User.verify_token(token)


@parser.location_loader("default")
def load_data(request, schema):
    """
    Load data from args, json fields of the request.
    :param request:
    :param schema:
    :return:
    """
    new_data = request.args.copy()
    try:
        req_json = request.json
        if req_json:
            new_data.update(req_json)
    except:
        pass
    result = MultiDictProxy(new_data, schema)
    return result


@parser.error_handler
def handle_request_parsing_error(err, req, schema, *, error_status_code, error_headers):
    http_status_code = error_status_code or 400
    abort(http_status_code, error=err.messages)


def _do_exec_manager_func(func, ctx):
    """
    Execute manager function.
    :param func:
    :param ctx:
    :return:
    """
    ex = None
    if ctx.succeed:
        try:
            func(ctx)
        except BaseException as e:
            print(e)
            ex = e
    # When context fails, rollback all uncommitted database changes
    if ex is not None or ctx.failed:
        if ex:
            ctx.set_error("Internal Server Error", cause=ex, status=500)


def exec_manager_func(func, ctx, required_roles=None):
    """
    Execute manager function.
    :param func:
    :param ctx:
    :param required_roles:
    :return:
    """
    _do_exec_manager_func(func, ctx)

    return process_result_context(ctx)


def process_result_context(ctx):
    """
    Process result context.
    :param ctx:
    :return:
    """
    if ctx.succeed:
        response = ctx.response
        if ctx.warning:
            if not response:
                response = {}
            if isinstance(response, dict):
                response['warning'] = ctx.warning_json()

        # In-progress task
        if ctx.status == 202:
            log_id = ctx.log_args.get('log_id')
            if log_id:
                if response is None:
                    response = {}
                if isinstance(response, dict):
                    response['log_id'] = log_id
                    response['log_status'] = ctx.log_args.get('log_status')
        return response, ctx.status or 200
    else:
        resp = {'errors': ctx.error_json()}
        return resp, ctx.status or 500
