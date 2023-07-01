#
# Copyright (c) 2020 FTI-CAS
#

import random
import re
import time
import uuid

import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from oslo_log import log as logging

from benji.config import CONF


LOG = logging.getLogger(__name__)
UPPERCASE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LOWERCASE_CHARS = 'abcdefghijklmnopqrstuvwxyz'
DIGIT_CHARS = '01234567890'
SYMBOL_CHARS = '~!@#$%^&*()-_+?{}[]<>`|\\/:,.'
ALPHABET_CHARS = UPPERCASE_CHARS + LOWERCASE_CHARS
ALPHA_DIGIT_CHARS = ALPHABET_CHARS + DIGIT_CHARS


def gen_random(length, base_chars=ALPHA_DIGIT_CHARS):
    """
    Generate a random string with length and base characters.
    :param length:
    :param base_chars:
    :return:
    """
    if not base_chars or length == 0:
        return ""
    result = ""
    base_len = len(base_chars)
    for i in range(0, length):
        result = result + base_chars[random.randrange(0, base_len)]
    return result


def format_decimal(value):
    """
    Format a number as a decimal. E.g. 12345.7 -> 12,345.7
    :param value:
    :return:
    """
    return "{:,}".format(value)


def str2bool(value):
    """
    Convert a string to bool.
    :param value:
    :return:
    """
    if not value:
        return False
    if isinstance(value, bool):
        return value
    return value.lower().strip() not in ('false', 'no', 'off', '0')


def gen_user_password(password):
    """
    Generate user password.
    :param password:
    :return:
    """
    return generate_password_hash(password)


def check_user_password(password_hash, password):
    """
    Check to see if the password and hash are matching.
    :param password_hash:
    :param password:
    :return:
    """
    return check_password_hash(password_hash, password)


def valid_user_password(password, requirement):
    """
    Validate user password strength.
    :param password:
    :param requirement:
    :return:
    """
    min_len = requirement.get('min_len')
    max_len = requirement.get('max_len')
    uppercase = requirement.get('uppercase')
    lowercase = requirement.get('lowercase')
    digit = requirement.get('digit')
    symbol = requirement.get('symbol')

    uppercase_chars = UPPERCASE_CHARS if uppercase else ''
    lowercase_chars = LOWERCASE_CHARS if lowercase else ''
    digit_chars = DIGIT_CHARS if digit else ''
    if symbol:
        symbol_chars = symbol if isinstance(symbol, str) else SYMBOL_CHARS
    else:
        symbol_chars = ''

    # Length
    if (min_len and len(password) < min_len) or (max_len and len(password) > max_len):
        return False

    has_uppercase = False
    has_lowercase = False
    has_digit = False
    has_symbol = False
    for ch in password:
        if ch in uppercase_chars:
            has_uppercase = True
        elif ch in lowercase_chars:
            has_lowercase = True
        elif ch in digit_chars:
            has_digit = True
        elif ch in symbol_chars:
            has_symbol = True

    if (uppercase and not has_uppercase) or (lowercase and not has_lowercase) or \
            (digit and not has_digit) or (symbol and not has_symbol):
        return False
    return True


def password_requirement_desc(requirement):
    """
    Construct password requirement description to display to user.
    :param requirement:
    :return:
    """
    min_len = requirement.get('min_len')
    max_len = requirement.get('max_len')
    uppercase = requirement.get('uppercase')
    lowercase = requirement.get('lowercase')
    digit = requirement.get('digit')
    symbol = requirement.get('symbol')

    desc = []
    if min_len:
        desc.append('minimum length: ' + str(min_len))
    if max_len:
        desc.append('maximum length: ' + str(max_len))

    desc2 = []
    if uppercase:
        desc2.append('uppercase letter')
    if lowercase:
        desc2.append('lowercase letter')
    if digit:
        desc2.append('digit')
    if symbol:
        desc2.append('symbol')
    if desc2:
        desc2[0] = 'must contain ' + desc2[0]
        desc.extend(desc2)

    return ', '.join(desc)


def jwt_encode_token(data, expires_in=None, key=None, algorithm='HS256'):
    """
    Gen token for data.
    :param data: data to encode
    :param expires_in: time expire (seconds)
    :param key: secret key
    :param algorithm: algorithm
    :return:
    """
    content = {
        'data': data,
    }
    if expires_in:
        content.update({'exp': time.time() + expires_in})
    else:
        content.update({'time': time.time()})
    key = key or CONF.get('api_secret_key', 'Gu(iaJgTCo&57xa')
    algorithm = algorithm or 'HS256'

    try:
        return jwt.encode(content, key=key, algorithm=algorithm).decode('utf-8')
    except TypeError as e:
        LOG.error(e)
        raise


def jwt_decode_token(token, key=None, algorithms=('HS256',)):
    """
    Decode token and return the encoded data.
    :param token:
    :param key: secret key
    :param algorithms: algorithms
    :return:
    """
    key = key or CONF.get('api_secret_key', 'Gu(iaJgTCo&57xa')
    algorithms = algorithms or ('HS256',)
    try:
        return jwt.decode(token, key=key, algorithms=algorithms)['data']
    except Exception as e:
        return None


def valid_email(email):
    """
    Check if an e-mail is in valid form.
    :param email:
    :return:
    """
    # RFC 222
    # Pattern e-mail (for most common cases, but not very accuracy)
    # pattern = r"^([a-zA-Z0-9_\.\-])+\@(([a-zA-Z0-9_\-])+\.)+([a-zA-Z0-9]{2,})+$"
    # return re.match(pattern, email) is not None

    if ' ' in email:
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False
    domain = parts[1]
    parts = domain.split('.')
    if len(parts) < 2:
        return False
    for v in parts:
        if not v:
            return False
    return True


def parse_cellphone(cellphone, country_code='84'):
    """
    Parse a cellphone number. e.g. (+84) 0912345678 -> 84912345678
    :param cellphone:
    :param country_code:
    :return:
    """
    cellphone = cellphone.strip()
    cellphone = cellphone.replace('-', '')
    cellphone = cellphone.replace('+', '')
    cellphone = cellphone.replace(' ', '')
    if country_code and cellphone.startswith('0'):
        cellphone = country_code + cellphone[1:]
    return cellphone


def join_args(sep, *args):
    """

    :param sep:
    @type sep:
    :param args:
    @type args:
    :return:
    @rtype:
    """
    return sep.join(args)


def h_join(*args):
    """

    :param args:
    @type args:
    :return:
    @rtype:
    """
    return '-'.join(args)


def generate_unique_code():
    return str(uuid.uuid4())
