from benji import errors, config as cfg, utils, exception as bj_exc
from contextlib import AbstractContextManager
from benji.database import VM, VolumeGroup, VolumeBackupGroup, ScheduleJob, VolumeScheduleJob
from benji.helpers import ops_utils
from benji.services.base import BaseModel


class VMModel(BaseModel, AbstractContextManager):
    __model__ = VM


class VolumeGroupModel(BaseModel, AbstractContextManager):
    __model__ = VolumeGroup

    def create(self, user_id, volumes, name=None, description=None):
        group = self.__model__(user_id=user_id, name=name, description=description)
        group, err = group.create()
        if err:
            return None, err

        for volume in volumes:
            vol_bg = VolumeBackupGroup(group_id=group.id, volume_id=volume['id'],
                                       volume_name=volume.get('name'), vm_id=volume['vm_id'])
            vol_bg.create()

        group = self.get(group.id)
        return group, None

    def update(self, id, volumes=None, name=None, description=None):
        group = self.get(id)
        if not group:
            return None, "Not found item"

        if name:
            group.name = name

        if description:
            group.description = description

        group, err = group.save()
        if err:
            return None, err

        if volumes:
            VolumeBackupGroup.raw_query().filter(VolumeBackupGroup.group_id == group.id).delete()
            for volume in volumes:
                vol_bg = VolumeBackupGroup(group_id=id, volume_id=volume['id'], vm_id=volume['vm_id'])
                vol_bg.create()

        return group, None

    def delete(self, id, force=True):
        obj = self.__model__.find_by_id(id)
        if not obj:
            return None, "Not found item"

        job = ScheduleJob.raw_query().filter(ScheduleJob.group_id == id).one_or_none()
        if job:
            VolumeScheduleJob.raw_query().filter(VolumeScheduleJob.sj_id == job.id).delete()
        ScheduleJob.raw_query().filter(ScheduleJob.group_id == id).delete()
        VolumeBackupGroup.raw_query().filter(VolumeBackupGroup.group_id == id).delete()
        _, err = obj.delete(True)
        if err:
            return None, err

        return True, None
