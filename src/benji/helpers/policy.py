from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from random import randint

from benji.helpers import utils

# GFS _ Policy
## days
SON = 8
## weeks
FATHER = 5
## months
GRANDFATHER = 2

# Exclude working time 08:00-17:00
START_WORKING_TIME = 8
END_WORKING_TIME = 17 

def exclude_woking_time():
    """
    Exclude working time START_WORKING_TIME:00 - END_WORKING_TIME:00
    """
    start_time = randint(END_WORKING_TIME * 60, (START_WORKING_TIME + 24) * 60)
    if start_time >= 1440:
        start_time = start_time - 1440
    return start_time


def is_month_end():
    """
    Check to day is end of month
    """
    # today = datetime(2021, 7, 31).date()
    today = datetime.now().date()
    next_month = today.replace(day=28) + timedelta(days=4)
    last_day_of_month = next_month - timedelta(days=next_month.day)
    if today == last_day_of_month:
        return True


def is_weekend():
    """
    Check to day is weekend(Sunday)
    """
    if date.today().weekday() == 6:
        return True


def do_check_gfs(retention):
    """
    If retention > 0 then expired_at = created_at + retention
    Check if retention = -1 set expired_at with GFS

    :param retention:
    :return:
    """
    expired_at = None
    if retention != -1 and retention > 0:
        # Backup with customize policy
        expired_at = utils.get_local_time() + relativedelta(days=+retention)
    elif retention == -1:
        # Backup with default policy GFS
        if is_month_end():
            expired_at = utils.get_local_time() + relativedelta(months=+GRANDFATHER)
        elif is_weekend():
            expired_at = utils.get_local_time() + relativedelta(weeks=+FATHER)
        else:
            expired_at = utils.get_local_time() + relativedelta(days=+SON)
    return expired_at
