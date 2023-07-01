import bcrypt

from benji import errors
from benji import exception as bj_exc
from benji.database import User, TwoFactor, Node, Storage, VM, Version, VolumeGroup
from benji.config import CONF
from benji.helpers import utils, ops_utils, types, str_utils
from benji.services.storage.model import StorageModel
from benji.services.user.model import UserModel
from benji.services import base


class UserController(base.BaseService):
    def __init__(self, config):
        super(UserController, self).__init__(config)

    def login(self, ctx):
        """
        Login
        :param ctx:
        :return:
        """
        data = ctx.data
        password = data['password']

        user = ctx.target_user
        if not user:
            ctx.set_error(errors.USER_NOT_AUTHORIZED, status=401)
            return

        self.check_user_status(ctx)
        if ctx.failed:
            return

        if not UserController.verify_user_password(user.password, password):
            ctx.set_error(errors.USER_PASSWORD_INVALID, status=401)
            return

        if user.enable_two_factors:
            otp_token = data.get('otp_token')
            if not otp_token:
                ctx.set_error(errors.OTP_TOKEN_INVALID, status=428)
                return
            two_factor = TwoFactor.raw_query().filter(TwoFactor.user_id == user.id).one_or_none()
            if not two_factor:
                ctx.set_error(errors.TWO_FACTOR_NOT_ENABLED, status=401)
                return

            if not two_factor.verify_otp_token(otp_token):
                ctx.set_error(errors.OTP_TOKEN_INVALID, status=401)
                return

        access_token_exp = CONF.get('API_ACCESS_TOKEN_EXPIRATION', 60000)
        refresh_token_exp = CONF.get('API_REFRESH_TOKEN_EXPIRATION', 60000)

        resp = {
            'id': user.id,
            'user_name': user.user_name,
            'email': user.email,
            'role': user.user_role.value,
            'fullname': user.fullname,
            'token_type': 'Bearer',
            'enable_two_factors': user.enable_two_factors,
            'access_token': user.gen_token(expires_in=access_token_exp),
            'expires_in': access_token_exp,
            'expires_on': utils.utc_future(seconds=access_token_exp),
            'refresh_token': user.gen_token(expires_in=refresh_token_exp),
            'refresh_token_expires_in': refresh_token_exp,
            'refresh_token_expires_on': utils.utc_future(seconds=refresh_token_exp),
        }

        ctx.response = resp
        return ctx.response

    def check_user_status(self, ctx):
        if not ctx.target_user.is_active:
            ctx.set_error("User was locked. Please contact with us to unlock your account", status=400)
            return

        return True

    @staticmethod
    def verify_user_password(password_hashed=None, password=None):
        """
        Verify password
        :param password_hashed:
        :param password:
        :return: bool
        """
        try:
            password_hash = password_hashed.encode('utf-8')
            password = password.encode('utf-8')
            return bcrypt.checkpw(password, password_hash)
        except:
            return None

    def logout(self, ctx):
        """

        :param ctx:
        :return:
        """

    def refresh_token(self, ctx):
        """
        Refresh token for user.
        :param ctx:
        :return:
        """
        if not self.check_user(ctx, roles=None):
            return

        user = ctx.target_user
        access_token_exp = CONF.get('API_ACCESS_TOKEN_EXPIRATION', 600)
        refresh_token_exp = CONF.get('API_REFRESH_TOKEN_EXPIRATION', 600)
        response = {
            'token_type': 'Bearer',
            'access_token': user.gen_token(expires_in=access_token_exp),
            'expires_in': access_token_exp,
            'expires_on': utils.utc_future(seconds=access_token_exp),
            'refresh_token': user.gen_token(expires_in=refresh_token_exp),
            'refresh_token_expires_in': refresh_token_exp,
            'refresh_token_expires_on': utils.utc_future(seconds=refresh_token_exp),
        }
        ctx.response = response
        return response

    def check_user(self, ctx, roles=None):
        """
        Check request user permission.
        :param ctx:
        :param roles:
        :return:
        """
        if roles and not ctx.check_request_user_role(roles):
            ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
            return False

        if ctx.is_cross_user_request:
            # Cross user request, but request user role is lower than target user role
            if ctx.compare_roles():  # if request user role <= target user role
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return False
            return True
        else:  # request_user == target_user
            return self.check_user_status(ctx)

    def sumup_resource(self, ctx):
        response = {}
        user = ctx.target_user
        if ctx.is_admin():
            user_id = ctx.data.get('user_id')
            if user_id:
                user = User.find_by_id(user_id)
                if not user:
                    ctx.set_error(errors.USER_NOT_FOUND, status=404)
                    return

        backup_count = 0
        storage = Storage.raw_query().filter(Storage.user_id == user.id).one_or_none()
        if not storage:
            response['disk_used'] = 0
            response['disk_allowed'] = 0
        else:
            response['disk_used'] = storage.disk_used
            response['disk_allowed'] = storage.disk_allowed
            bks = Version.raw_query().filter(Version.storage_id == storage.id, Version.deleted == False).all()
            backup_count += len(bks)

        response['backup_count'] = backup_count

        vms = VM.raw_query().filter(VM.user_id == user.id).all()
        response['vm_count'] = len(vms)

        volume_count = 0
        try:
            ops_handler = ops_utils.OpsHandler(CONF.get('ops_auth', None))
        except bj_exc.BenjiException as e:
            ctx.set_error(str(e), status=400)
            return
        for vm in vms:
            volumes = ops_handler.list_volumes(vm.ems_ref) or []
            volume_count += len(volumes)
        response['volume_count'] = volume_count

        bk_groups = VolumeGroup.raw_query().filter(VolumeGroup.user_id == user.id).all()
        response['backup_group_count'] = len(bk_groups)

        ctx.response = response

    def sumup_resource_users(self, ctx):
        res = []
        result = {}

        if not ctx.is_admin():
            ctx.set_error(error=errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        with StorageModel(self._config) as model:
            condition = self.build_condition_sumup(ctx)
            storages, objects, prev_page = model.dump_raw_object(ctx, Storage, condition)

            if not storages:
                ctx.set_error(errors.RESOURCE_NOT_FOUND, status=404)
                return

            for storage in storages:
                storage_dict = storage.to_dict()
                result['node_name'] = storage.node.name
                result['user_id'] = storage.user_id
                result['user_name'] = storage.user.user_name
                result['disk_used'] = storage_dict['disk_used']
                result['disk_allowed'] = storage_dict['disk_allowed']
                vms = VM.raw_query().filter(VM.user_id == storage.user_id).all()
                result['vm_count'] = len(vms)


                backup_count = 0
                bks = Version.raw_query().filter(Version.storage_id == storage.id, Version.deleted == False).all()
                backup_count += len(bks)
                result['backup_count'] = backup_count

                bk_groups = VolumeGroup.raw_query().filter(VolumeGroup.user_id == storage.user_id).all()
                result['backup_group_count'] = len(bk_groups)
                s_result = result.copy()
                res.append(s_result)

            response = {
                'data': res,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
                }
            ctx.response = response

    def build_condition_sumup(self, ctx):
        data = ctx.data
        condition = ''
        user_name = data.get('user_name', None)
        node_name = data.get('node_name', None)
        if user_name:
            user = User.raw_query().filter(User.user_name == user_name).one_or_none()
            condition += " user_id == '{}' and ".format(user.id)

        if node_name:
            node = Node.raw_query().filter(Node.name == node_name).one_or_none()
            condition += " node_id == '{}' and ".format(node.id)

        if condition != '':
            condition = '({})'.format(condition[:-5].strip())
            return condition
        return None

    def get_two_factor(ctx):
        user = ctx.request_user
        two_factor = TwoFactor.raw_query().get(user.id)
        if not two_factor:
            error = 'You have been disabled two factors.'
            ctx.set_error(error, status=400)
            return
        return TwoFactor.dump_object(ctx, two_factor)

    def create_two_factor(ctx):
        user = ctx.request_user

        two_factor = TwoFactor.raw_query().get(user.id)
        if two_factor:
            if two_factor.status != types.TwoFactorStatus.DISABLED:
                error = 'You have been enabled two factors.'
                ctx.set_error(error, status=400)
                return
            else:
                two_factor.update(status=types.TwoFactorStatus.PENDING)
                # two_factor.status = md_type.TwoFactorStatus.PENDING
                # two_factor.otp_token = md.TwoFactor.regenerate_otp_token()
                # _, err = two_factor.create()
                # if err:
                #     LOG.error("Error [create_two_factor(%s)]: %s", user.id, err)
                #     ctx.set_error(errors.INTERNAL_SERVER_ERROR, status=500)
                #     return
                user.update(enable_two_factor=True)
                return TwoFactor.dump_object(ctx, two_factor)
        else:
            user.enable_two_factor = True
            two_factor = TwoFactor()
            two_factor.user_id = user.id
            two_factor.otp_token = TwoFactor.regenerate_otp_token()
            _, err = two_factor.create()
            if err:
                ctx.set_error(errors.INTERNAL_SERVER_ERROR, status=500)
                return

            _, err = user.save()
            if err:
                two_factor.delete()
                ctx.set_error(errors.INTERNAL_SERVER_ERROR, status=500)
                return
            ret = TwoFactor.dump_object(ctx, two_factor)
            return ret

    def verify_two_factor(ctx):
        data = ctx.data
        otp_token = data['otp_token']

        user = ctx.request_user
        two_factor = TwoFactor.raw_query().get(user.id)
        if not two_factor:
            error = 'Two factors is not enabled.'
            ctx.set_error(error, status=400)
            return

        status = two_factor.verify_otp_token(otp_token)
        if not status:
            ctx.set_error("Invalid OTP", status=400)
            return
        ctx.response = True

    def reset_two_factor(ctx):
        # user = ctx.request_user
        data = ctx.data
        username = data['username']
        password = data['password']

        user = User.get_by(user_name=username)
        if not user:
            ctx.set_error(errors.USER_NOT_FOUND, status=404)
            return

        if not str_utils.check_user_password(user.password, password):
            ctx.set_error(errors.USER_PASSWORD_INVALID, status=401)
            return

        two_factor = TwoFactor.raw_query().get(user.id)
        if not two_factor:
            error = 'Two factors is not enabled.'
            ctx.set_error(error, status=400)
            return

        two_factor.otp_token = two_factor.regenerate_otp_token()

        two_factor.save()
        ctx.response = True

    def delete_two_factor(ctx):
        data = ctx.data
        otp_token = data['otp_token']

        user = ctx.request_user
        two_factor = TwoFactor.raw_query().get(user.id)
        if not two_factor:
            ctx.set_error(errors.TWO_FACTOR_NOT_ENABLED, status=400)
            return

        if not two_factor.verify_otp_token(otp_token):
            ctx.set_error(errors.OTP_TOKEN_INVALID, status=400)
            return

        two_factor.update(status=types.TwoFactorStatus.DISABLED)
        user.update(enable_two_factor=False)
        ctx.response = True
        return

    def list_users(self, ctx):
        response = {
            'data': [],
            'has_more': False,
            'next_page': None,
            'prev_page': None,
        }
        with UserModel(self._config) as model:
            if not ctx.is_admin():
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return None

            condition = self.build_condition(ctx)
            users, objects, prev_page = model.dump_raw_object(ctx, User, condition)
            result = []

            if not users:
                return None

            for user in users:
                user_dict = user.to_dict(ignore_fields=['password', 'miq_id', 'enable_two_factors'])
                storage = Storage.get_by_name(user.user_name)
                if storage:
                    user_dict.update(has_storage=True)
                else:
                    user_dict.update(has_storage=False)
                result.append(user_dict)

            response = {
                'data': result,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
            }

            ctx.response = response

    def build_condition(self, ctx):
        data = ctx.data
        condition = ''
        user_name = data.get('user_name', None)
        email = data.get('email', None)
        if user_name:
            condition += " user_name == '{}' and ".format(user_name)
        if email:
            condition += " email == '{}' and ".format(email)
        condition += " user_role == '{}' and ".format("USER")
        if condition != '':
            condition = '({})'.format(condition[:-5].strip())
            return condition
        return None
