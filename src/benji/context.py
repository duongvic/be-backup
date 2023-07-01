
from flask import _request_ctx_stack, request as flask_request
from werkzeug.local import LocalProxy

from benji import exception as benji_exc, errors, config as cfg
from benji.database import User, Database
from benji.helpers import types


def _get_context():
    return getattr(_request_ctx_stack.top, 'context', None)


current_context = LocalProxy(lambda: _get_context())


class Context(object):
    def __init__(self, task,
                 request_user=None, target_user=None,
                 check_token=True, request=None, response=None,
                 data=None, status=None):
        self.task = task
        self.request_user = request_user  # request user is someone who make a request
        self.target_user = target_user  # target user is someone who executes command
        self.check_token = check_token
        self.request = request
        self.response = response
        self.db_session = None
        self.data = data
        self.status = status
        self.error = None
        self.warning = None
        self.log_args = dict(data) if data else {}

    @property
    def succeed(self):
        return False if self.error else True

    @property
    def failed(self):
        return True if self.error else False

    def add_response(self, key, value):
        if not self.response:
            self.response = {}
        self.response[key] = value

    def get_response_value(self, key):
        if not self.response:
            return None
        return self.response.get(key)

    def clear_response(self):
        self.response = None

    def set_error(self, error, cause=None, status=500, clear=True):
        # LOG.error("Error: %s cause: %s", error, cause)
        if clear:
            self.clear_error()
        if isinstance(error, str):
            error = benji_exc.BenjiError(status, error, cause)
        self.add_error(error)
        self.status = status

    def add_error(self, error):
        if not isinstance(error, list):
            error = [error]
        all_errors = self.error
        if not isinstance(all_errors, list):
            all_errors = [all_errors] if all_errors else []
        all_errors.extend(error)
        self.error = all_errors if len(all_errors) > 1 else all_errors[0]

    def clear_error(self):
        self.error = None
        self.status = None

    def copy_error(self, ctx):
        self.set_error(ctx.error, status=ctx.status)

    def set_warning(self, warning, cause=None, clear=True):
        if clear:
            self.clear_warning()
        if isinstance(warning, str):
            warning = benji_exc.BenjiError(message=warning, cause=cause)
        self.add_warning(warning)

    def add_warning(self, warning):
        if not isinstance(warning, list):
            warning = [warning]
        all_warnings = self.warning
        if not isinstance(all_warnings, list):
            all_warnings = [all_warnings] if all_warnings else []
        all_warnings.extend(warning)
        self.warning = all_warnings if len(all_warnings) > 1 else all_warnings[0]

    def clear_warning(self):
        self.warning = None

    def copy_warning(self, ctx):
        self.add_warning(ctx.warning)

    def error_json(self):
        error = self.error
        if isinstance(error, benji_exc.BenjiError):
            error = [error]
        if isinstance(error, list):
            return [item.to_json() for item in error]
        return None

    def warning_json(self):
        warning = self.warning
        if isinstance(warning, benji_exc.BenjiError):
            return warning.to_json()
        if isinstance(warning, list):
            return [item.to_json() for item in warning]
        return None

    @property
    def is_cross_user_request(self):
        request_id = self.request_user.id if self.request_user else None
        target_id = self.target_user.id if self.target_user else None
        return request_id != target_id

    def compare_roles(self):
        request_role = types.UserRole.parse(self.request_user.user_role) if self.request_user else None
        target_role = types.UserRole.parse(self.target_user.user_role) if self.target_user else None
        ret = request_role <= target_role if request_role and target_role else True
        return ret

    def load_users(self):
        data = self.data or {}
        from benji import api
        current_user = api.api_auth.current_user()

        if self.check_token:
            user_id = getattr(current_user, 'id', None)
            if not user_id:
                self.set_error(errors.USER_NOT_AUTHORIZED, status=401)
                return
            self.request_user = User.find(id=user_id)
            if not self.request_user:
                self.set_error(errors.USER_NOT_AUTHORIZED, status=401)
                return

        # Target user
        target_user = (self.target_user or data.get('user_name', None) or self.request_user)
        self.target_user = User.load(target_user)

        # # Request user
        self.target_user = self.target_user or self.request_user

        # A lower user role cannot access higher user data
        if self.check_token:
            if self.is_cross_user_request and self.compare_roles():
                self.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return

    def is_admin(self):
        return self.request_user.user_role.is_admin()


def create_context(task,
                   request_user=None, target_user=None,
                   check_token=True,
                   request=flask_request, response=None,
                   data=None, status=None):
    """
    Create context from arguments.
    :param task:
    :param request_user:
    :param target_user:
    :param check_token:
    :param request:
    :param response:
    :param data:
    :param status:
    :return:
    """
    ctx = Context(task=task,
                  request_user=request_user, target_user=target_user,
                  check_token=check_token,
                  request=request, response=response,
                  data=data, status=status)
    ctx.load_users()

    # Push the context to the request context
    ctx_stack_top = _request_ctx_stack.top
    ctx_stack_top.context = ctx

    return ctx
