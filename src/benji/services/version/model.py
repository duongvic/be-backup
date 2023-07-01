from datetime import datetime, timedelta
from contextlib import AbstractContextManager
from benji.database import Version, ScheduleJob
# from sqlalchemy import and_
# from benji.helpers import policy

from benji.services.base import BaseModel


class VersionModel(BaseModel, AbstractContextManager):
    __model__ = Version

    def create(self, **kwargs):
        # job = ScheduleJobs.raw_query().filter(and_(ScheduleJobs.volume_id == kwargs['volume'],
        #                                       ScheduleJobs.deleted is False)).one_or_none()
        # if job:
        #     kwargs['expired_at'] = datetime.utcnow() + timedelta(days=job.retention)
        #     kwargs['expired_at'] = policy.do_check_gfs(job.retention)
        return Version(**kwargs).create()
