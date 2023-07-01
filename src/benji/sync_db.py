import urllib
from dateutil import parser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from benji.database import User, VM, TwoFactor
from benji.helpers import types


def make_session():
    password = urllib.parse.quote_plus('FTI-CAS-19%102&z0*#@37')
    engine = create_engine('postgresql://casadmin:' + password + '@172.16.4.252/vmdb_production', echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def seed_db():

    """Seed data from db miq """

    session_miq = make_session()

    users_miq = session_miq.execute(text("select * from users"))
    for user_miq in users_miq:
        miq_group_id = user_miq.current_group_id
        miq_user_role_ids = session_miq.execute(text("select miq_user_role_id from entitlements where miq_group_id=:miq_group_id limit 1").params(miq_group_id=miq_group_id))
        for user_role_id in miq_user_role_ids:
            miq_user_role_id = user_role_id['miq_user_role_id']

        miq_user_roles = session_miq.execute(text("select name from miq_user_roles where id=:miq_user_role_id limit 1").params(miq_user_role_id=miq_user_role_id))
        miq_user_role = None
        for user_role in miq_user_roles:
            miq_user_role = user_role['name']

        if not miq_user_role:
            continue

        user_role = types.UserRole.USER
        miq_user_role = miq_user_role.lower()
        if "admin" in miq_user_role:
            user_role = types.UserRole.ADMIN_IT

        user = User(miq_id=user_miq.id, fullname=user_miq.name, email=user_miq.email, user_name=user_miq.userid,
                    status=user_miq.status, password=user_miq.password_digest,
                    enable_two_factors=user_miq.enable_two_factors, user_role=user_role)
        user.create()

    vms = session_miq.execute(text("select name, ems_ref, created_on, evm_owner_id from vms where template=false"))
    for vm in vms:
        name, ems_ref, created_on, evm_owner_id = vm
        user = User.raw_query().filter(User.miq_id==evm_owner_id).one_or_none()
        if not user:
            continue

        vm = VM(name=name, ems_ref=ems_ref, created_at=created_on, user_id=user.id)
        vm.create()

    two_factors = session_miq.execute(text("select user_id, otp_token, hotp_counter, status from two_factors"))
    for two_factor in two_factors:
        user_id, otp_token, hotp_counter, status = two_factor
        user = User.raw_query().filter(User.miq_id==user_id).one_or_none()
        if not user:
            continue
        two_factor = TwoFactor(user_id=user.id, otp_token=otp_token,
                               hotp_counter=hotp_counter, status=types.TwoFactorStatus.parse(status))
        two_factor.create()

    session_miq.commit()
    session_miq.close()
