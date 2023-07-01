import datetime
import enum
from functools import wraps
import inspect


def valid_kwargs(*valid_args):
    """
    Check if argument passed as **kwargs to a function are
    present in valid_args
    Typically, valid_kwargs is used when we want to distinguish
    between none and omitted arguments and we still want to validate
    the argument list
    Usage
    @valid_kwargs('flavor_id', 'image_id')
    def my_func(self, arg1, arg2, **kwargs):
        ...
    :param valid_args:
    :return:
    """

    def wrapper(func):
        """
        :param func:
        :return:
        """

        @wraps(func)
        def func_wrapper(*args, **kwargs):
            all_args = inspect.getfullargspec(func)
            for k in kwargs:
                if k not in all_args.args[1:] and k not in valid_args:
                    raise TypeError(
                        "{f}() got an unexpected keyword argument "
                        "'{arg}'".format(f=inspect.stack()[1][3], arg=k)
                    )
            return func(*args, **kwargs)

        return func_wrapper

    return wrapper


def dump_value(value):
    if not value:
        return value

    dump_types = (dict, list, tuple)
    if isinstance(value, dump_types):
        if isinstance(value, dict):
            return value
        else:
            dump_data = []
            for item in value:
                dump_data.append(dump_value(item))
    elif isinstance(value, enum.Enum):
        dump_data = value.value
    elif isinstance(value, datetime.datetime):
        dump_data = value.strftime('%Y-%m-%d %H:%M')
    else:
        dump_data = value

    return dump_data