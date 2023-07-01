from flask_restful import Resource
from webargs import fields, validate
from webargs.flaskparser import use_args
from benji import config as cfg
from benji import context
from benji.api.v1 import (base)
from benji.services.user.controller import UserController


user = UserController(cfg.CONF)

LOCATION = 'default'
auth = base.auth


def do_login(args):
    """
    Do login user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='login user',
        check_token=False,
        data=args)

    return base.exec_manager_func(user.login, ctx)


def do_logout(args):
    """
    Do logout user.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='logout user',
        data=args)
    return base.exec_manager_func(user.logout, ctx)


class Auth(Resource):
    login_args = {
        'user_name': fields.Str(required=True),
        'password': fields.Str(required=True),
        'otp_token': fields.Str(required=False, validate=lambda token: len(token) == 6),
    }

    logout_args = {
    }

    @use_args(login_args, location=LOCATION)
    def post(self, args):
        return do_login(args=args)

    @auth.login_required
    @use_args(logout_args, location=LOCATION)
    def delete(self, args):
        return do_logout(args=args)


#####################################################################
# TOKENS
#####################################################################
def do_refresh_token(args):
    """
    Do refresh token.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='refresh user token',
        data=args)
    return base.exec_manager_func(user.refresh_token, ctx)


class RefreshToken(Resource):
    refresh_token_args = {
    }

    @auth.login_required
    @use_args(refresh_token_args, location=LOCATION)
    def put(self, args):
        return do_refresh_token(args=args)


def do_statistic(args):
    """
    Do statistic resource.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='Statistic resource',
        data=args)
    return base.exec_manager_func(user.sumup_resource, ctx)


class UserStatistic(Resource):
    statistic_args = {
        'user_id': fields.Int(required=False),
    }

    @auth.login_required
    @use_args(statistic_args, location=LOCATION)
    def get(self, args):
        return do_statistic(args=args)


def do_users_statistic(args):
    """
    Do statistic resource.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='Statistic resource users',
        data=args)
    return base.exec_manager_func(user.sumup_resource_users, ctx)


class UsersStatistic(Resource):
    users_statistic_args = {
        **base.PAGING_ARGS,
        'user_name': fields.Str(required=False),
        'node_name': fields.Str(required=False),
    }

    @auth.login_required
    @use_args(users_statistic_args, location=LOCATION)
    def get(self, args):
        return do_users_statistic(args=args)


def do_get_users(args):
    """
    Do get multiple users.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='get users',
        data=args)
    return base.exec_manager_func(user.list_users, ctx)


class Users(Resource):
    get_users_args = {
        **base.PAGING_ARGS,
        'user_name': fields.Str(required=False),
        'email': fields.Str(required=False)
    }

    @auth.login_required
    @use_args(get_users_args, location=LOCATION)
    def get(self, args):
        return do_get_users(args=args)


#####################################################################
# Two Factors
#####################################################################

def do_create_two_factor(args):
    """
    Do create two factor.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='create two factor',
        check_token=True,
        data=args)
    return base.exec_manager_func(user.create_two_factor, ctx)


def do_get_two_factor(args):
    """
    Do create two factor.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='get two factor',
        check_token=True,
        data=args)
    return base.exec_manager_func(user.get_two_factor, ctx)


def do_verify_two_factor(args):
    """
    Do create two factor.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='verify two factor',
        check_token=True,
        data=args)
    return base.exec_manager_func(user.verify_two_factor, ctx)


def do_reset_two_factor(args):
    """
    Do reset two factor.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='reset two factor',
        check_token=True,
        data=args)
    return base.exec_manager_func(user.reset_two_factor, ctx)


def do_delete_two_factor(args):
    """
    Do delete two factor.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='delete two factor',
        check_token=True,
        data=args)
    return base.exec_manager_func(user.delete_two_factor, ctx)


class TwoFactors(Resource):
    get_two_factor_args = base.LIST_OBJECTS_ARGS

    create_two_factor_args = {
    }

    @use_args(get_two_factor_args, location=LOCATION)
    def get(self):
        pass

    @auth.login_required
    @use_args(create_two_factor_args, location=LOCATION)
    def post(self, args):
        return do_create_two_factor(args=args)


class TwoFactor(Resource):
    get_two_factor_args = base.LIST_OBJECTS_ARGS

    verify_two_factor_args = {
        'otp_token': fields.Str(required=True, validate=lambda otp: len(otp) == 6),
    }

    reset_two_factor_args = {
        'email': fields.Str(required=False),
    }

    delete_two_factor_args = {
        'otp_token': fields.Str(required=True, validate=lambda otp: len(otp) == 6),
    }

    @auth.login_required
    @use_args(get_two_factor_args, location=LOCATION)
    def get(self, args):
        return do_get_two_factor(args=args)

    @auth.login_required
    @use_args(reset_two_factor_args, location=LOCATION)
    def post(self, args):
        return do_reset_two_factor(args=args)

    @auth.login_required
    @use_args(verify_two_factor_args, location=LOCATION)
    def put(self, args):
        return do_verify_two_factor(args=args)

    @auth.login_required
    @use_args(delete_two_factor_args, location=LOCATION)
    def delete(self, args):
        return do_delete_two_factor(args=args)


#####################################################################
# RESET TWO FACTORS
#####################################################################
def do_recover_two_factor(args):
    """
    Do recover two factor.
    :param args:
    :return:
    """
    ctx = context.create_context(
        task='recover two factor',
        check_token=False,
        data=args)
    return base.exec_manager_func(user.reset_two_factor, ctx)


class RecoverTwoFactor(Resource):
    reset_two_factor_args = {
        'username': fields.Str(required=True),
        'password': fields.Str(required=True),
    }

    # @auth.login_required
    @use_args(reset_two_factor_args, location=LOCATION)
    def post(self, args):
        return do_recover_two_factor(args=args)
