#
# Copyright (c) 2020 FTI-CAS
#

from datetime import datetime
import json

from flask import json as flask_json

from benji.helpers import objects

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DATE_TIME_MICROSEC_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class AppJSONEncoder(flask_json.JSONEncoder):
    """
    Custom JSON encoder for the app.
    """
    def default(self, obj):
        if isinstance(obj, objects.FmtDatetime):
            return str(obj)
        # if isinstance(obj, date):
        #     return date_util.format(obj, format=DATE_FORMAT)
        # if isinstance(obj, time):
        #     return date_util.format(obj, format=TIME_FORMAT)
        if isinstance(obj, datetime):
            # Another way: date_util.format(obj, format=DATE_TIME_FORMAT)
            return obj.strftime(DATE_TIME_FORMAT)

        return super().default(obj)


def json_dumps(value, **kw):
    """
    Dumps json value to string.
    :param value:
    :param kw:
    :return:
    """
    kw['cls'] = AppJSONEncoder
    return json.dumps(value, **kw)


def json_loads(string, **kw):
    """
    Loads json value from string.
    :param string:
    :param kw:
    :return:
    """
    return json.loads(string, **kw)
