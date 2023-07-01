from contextlib import AbstractContextManager

from benji.database import ScheduleJob, Storage, VolumeScheduleJob, VolumeBackupGroup
from benji.helpers.data_utils import valid_kwargs

from benji.services.base import BaseModel


class ScheduleJobModel(BaseModel, AbstractContextManager):
    __model__ = ScheduleJob

    @valid_kwargs('group_id', 'storage_id', 'name', 'retention',
                  'days_of_week', 'start_time', 'mode', 'volume_id', 'compression')
    def create(self, **params):
        group_id = params['group_id']
        bks_group = VolumeBackupGroup.raw_query().filter(VolumeBackupGroup.group_id == group_id).all()
        if not bks_group:
            return None, "Not found volumes in group"

        days_of_week = params['days_of_week']
        days_of_week_str = ','.join(day for day in days_of_week)
        params['days_of_week'] = days_of_week_str
        job = self.__model__(**params)
        job, err = job.create()
        if err:
            return None, "Failed to create schedule job"

        for bk_group in bks_group:
            _, err = VolumeScheduleJob(sj_id=job.id, volume_id=bk_group.volume_id,
                                       volume_name=bk_group.volume_name, vm_id=bk_group.vm_id).create()
        return job, None

    @valid_kwargs('volume_id', 'storage_id', 'name', 'retention',
                  'days_of_week', 'start_time', 'mode', 'storage_id', 'compression')
    def update(self, id, **params):
        job = self.get(id)
        days_of_week = params['days_of_week']
        days_of_week_str = ','.join(day for day in days_of_week)
        params['days_of_week'] = days_of_week_str
        return job.update(**params)
    
    def get_storage(self, name):
        storage = Storage.raw_query().filter(Storage.name == name).one_or_none()
        return storage

    def delete(self, id, force=True):
        obj = self.__model__.find_by_id(id)
        if not obj:
            return None, "Not found item"

        VolumeScheduleJob.raw_query().filter(VolumeScheduleJob.sj_id == id).delete()
        _, err = obj.delete(True)
        if err:
            return False, err

        return True, None
