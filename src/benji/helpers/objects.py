from datetime import datetime

EPOCH = datetime.utcfromtimestamp(0)


class FmtDatetime(datetime):
    FMT_SEC_SINCE_EPOCH = 'sec_since_epoch'
    FMT_DATE = '%Y-%m-%d'
    FMT_TIME = '%H:%M:%S'
    FMT_DATE_TIME = '%Y-%m-%d %H:%M:%S'
    FMT_DATE_TIME_MICROSEC = '%Y-%m-%d %H:%M:%S.%f'

    @classmethod
    def fromdatetime(cls, dt, fmt):
        self = FmtDatetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour,
                           minute=dt.minute, second=dt.second, microsecond=dt.microsecond,
                           tzinfo=dt.tzinfo)
        self.fmt = fmt
        return self

    def __str__(self):
        fmt = self.fmt
        if fmt == self.FMT_SEC_SINCE_EPOCH:
            return (self - EPOCH).total_seconds()

        return self.strftime(fmt)
