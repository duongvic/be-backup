from benji.services import base
from benji.services.schedule_job.model import ScheduleJobModel, Storage
from benji.database import ScheduleJob, VolumeGroup
from benji import utils, errors
from benji.helpers import policy


class ScheduleJobController(base.BaseService):
    def __init__(self, config):
        super(ScheduleJobController, self).__init__(config)

    @property
    def supported(self):
        return True

    def get_schedule_job(self, ctx):
        with ScheduleJobModel(self._config) as model:
            job = model.get(ctx.data['id'])
            if job is None:
                ctx.set_error("Not found item", status=404)
                return

            ctx.response = job.to_dict()

    def list_schedule_jobs(self, ctx):
        result = []
        with ScheduleJobModel(self._config) as model:
            condition = self.build_condition(ctx)
            jobs, objects, prev_page = model.dump_raw_object(ctx, ScheduleJob, condition)

            if not ctx.is_admin():
                user_name = ctx.target_user.user_name
                storage = Storage.raw_query().filter(Storage.name == user_name).one_or_none()
                if storage is None:
                    ctx.response = None
                    return

                group_name = None
                for job in jobs:
                    group_name = job.group.name
                    job_dict = job.to_user_dict()
                    job_dict.update(group_name=group_name)
                    result.append(job_dict)

            else:
                for job in jobs:
                    group_name = job.group.name
                    job_dict = job.to_dict()
                    job_dict.update(group_name=group_name, user_name=job.storage.user.user_name)
                    result.append(job_dict)

            ctx.response = {
                'data': result,
                'has_more': objects.has_next,
                'next_page': objects.next_num if objects.has_next else None,
                'prev_page': prev_page,
            }

    def build_condition(self, ctx):
        data = ctx.data
        condition = ''

        if ctx.is_admin():
            user_name = data.get('user_name', None)
        else:
            user_name = ctx.target_user.user_name
        storage = Storage.raw_query().filter(Storage.name == user_name).one_or_none()

        if storage:
            condition += " storage_id == '{}' and ".format(storage.id)

        if condition != '':
            condition = '({})'.format(condition[:-5].strip())
            return condition
        return None

    def create_schedule_job(self, ctx):
        data = ctx.data
        retention = data['retention']
        start_time = data['start_time']
        group_id = data['group_id']

        if start_time < 0 or start_time > 1440:
            ctx.set_error("Start time is out of range", status=400)
            return

        if not data.get('name', None):
            data['name'] = utils.generate_uuid()

        if retention < -1 or retention > 360 or retention == 0:
            ctx.set_error("Retention is out of range valid", status=400)
            return

        # Set default daily & start for policy GFS
        if retention == -1:
            # data['start_time'] = 0
            data['start_time'] = policy.exclude_woking_time()
            data['days_of_week'] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

        group = VolumeGroup.raw_query().filter(VolumeGroup.id == group_id).first()
        if group is None:
            ctx.set_error(errors.RESOURCE_NOT_FOUND, status=403)
            return

        if (not ctx.is_admin()) and (group.user_id != ctx.target_user.id):
            ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
            return

        job = ScheduleJob.raw_query().filter(ScheduleJob.group_id == group_id).first()
        if job:
            ctx.set_error('group {} already have a policy'.format(group.name), status=400)
            return

        with ScheduleJobModel(self._config) as model:
            if ctx.is_admin():
                user_id = data.pop('user_id', None)
                storage = Storage.raw_query().filter(Storage.user_id == user_id).one_or_none()
            else:
                storage = model.get_storage(ctx.target_user.user_name)

            if not storage:
                ctx.set_error("Not found storage name", status=404)
                return
            else:
                data['storage_id'] = storage.id

            created_job, err = model.create(**data)
            if err:
                ctx.set_error(err, status=400)
                return

            ctx.response = created_job.to_dict()
            ctx.status = 201

    def update_schedule_job(self, ctx):
        data = ctx.data
        job_id = data.pop('id', None)
        with ScheduleJobModel(self._config) as model:
            job = model.get(job_id)
            if job is None:
                ctx.set_error("Not found item", status=400)
                return
            storage = model.get_storage(ctx.target_user.user_name)
            if not storage:
                ctx.set_error("Not found storage name", status=400)
                return

            if not ctx.is_admin():
                if storage.id != job.storage_id:
                    ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                    return

            # data['storage_id'] = storage.id
            current_retention = job.retention
            retention = data.get('retention', None)
            if retention is None and current_retention == -1:
                data['days_of_week'] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

            if retention is not None:
                if retention < -1 or retention == 0 or retention > 360:
                    ctx.set_error("Retention is out of range valid -1, 1-360", status=400)
                    return
                if retention == -1:
                    # data['start_time'] = policy.exclude_woking_time()
                    data['days_of_week'] = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

            start_time = data.get('start_time', None)
            if start_time is not None:
                if start_time < 0 or start_time > 1440:
                    ctx.set_error("Start_time is out of range valid 0-1440(minutes)", status=400)
                    return

            updated_job, err = model.update(job_id, **data)
            if err:
                ctx.set_error("Failed to create schedule job", status=400)
                return
            ctx.response = updated_job.to_dict()

    def delete_schedule_job(self, ctx):
        data = ctx.data
        job_id = data.pop('id', None)

        with ScheduleJobModel(self._config) as model:
            job = model.get(job_id)
            if job is None:
                ctx.set_error("Not found item", status=404)
                return

            if not ctx.is_admin() and (job.storage.user_id != ctx.target_user.id):
                ctx.set_error(errors.USER_ACTION_NOT_ALLOWED, status=403)
                return

            _, err = model.delete(job_id, data['force'])
            if err:
                ctx.set_error(err, status=400)
                return

            return
