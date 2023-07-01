from datetime import datetime, timedelta
import calendar
from sqlalchemy import and_

from benji.celery import app
from benji import config as cfg
from benji import utils
from benji.benji import Benji
from benji.database import ScheduleJob, Locking, Version, VersionStatus, VolumeScheduleJob
from benji.database import VersionUid
from benji.helpers import utils as time_utils
from benji.logging import logger
from benji.tasks import backup
from benji.helpers import policy


@app.task()
def run_schedule_job():
    logger.info("Start backing up data")
    with Benji(cfg.CONF) as benji_obj:
        job_arr = []
        _now = time_utils.get_local_time()
        weekday = _now.today().weekday()
        day_of_week = calendar.day_name[weekday]
        day_of_week = day_of_week[0:3].lower()
        cur_hhmm = _now.hour * 60 + _now.minute
        if cur_hhmm >= 1440:
            cur_hhmm = 1440

        next_hhmm = cur_hhmm + 10
        extra_time = 0
        if next_hhmm > 1440:
            extra_time = next_hhmm - 1440
            next_hhmm = 1440

        condition = and_(ScheduleJob.start_time >= cur_hhmm, ScheduleJob.start_time < next_hhmm,
                         ScheduleJob.days_of_week.like(f'%{day_of_week}%'))

        jobs = ScheduleJob.raw_query().filter(condition)
        job_arr.extend(jobs.all())

        if extra_time:
            if weekday >= 6:
                weekday = 0
            day_of_week = calendar.day_name[weekday + 1]
            day_of_week = day_of_week[0:3].lower()
            condition = and_(ScheduleJob.start_time >= 0, ScheduleJob.start_time < extra_time,
                             ScheduleJob.days_of_week.like(f'%{day_of_week}%'))
            jobs = ScheduleJob.raw_query().filter(condition)
            job_arr.extend(jobs.all())

        for job in job_arr:
            logger.info("Run schedule job {}".format(job.id))
            job_volumes = VolumeScheduleJob.raw_query().filter(VolumeScheduleJob.sj_id == job.id).all()
            if not job_volumes:
                continue

            Locking.lock(lock_name='ScheduleJob {}'.format(job.id),
                         reason='Running backup for job {}'.format(job.name))
            try:
                for job_vol in job_volumes:
                    if job.storage.disk_used >= job.storage.disk_allowed:
                        continue

                    logger.info("Start backing up data of volume of "
                                "the identifier {}".format(job_vol.volume_id))
                    version_uid = '{}-{}'.format(utils.generate_uuid(), utils.random_string(6))
                    version_uid_obj = VersionUid(version_uid)
                    source = 'rbd:volumes/volume-{}'.format(job_vol.volume_id)
                    expired_at = None

                    if job.retention:
                        # expired_at = datetime.utcnow() + timedelta(days=job.retention)
                        expired_at = policy.do_check_gfs(job.retention)

                    version, err = Version(uid=version_uid_obj, volume=job_vol.volume_id, vm_id=job_vol.vm_id,
                                           volume_name=job_vol.volume_name, job_name=job.name, snapshot='',
                                           size=0, block_size=0, storage_id=job.storage.id, expired_at=expired_at,
                                           status=VersionStatus.incomplete, protected=False).create()
                    if not err:
                        node = dict(host=job.storage.node.host, port=job.storage.node.port)
                        backup.create.apply_async(args=[node, version.id, source, None])
                    else:
                        logger.error(e)

                    logger.info("[run_schedule_job()] Run asynchronously to backing up data "
                                "of volume of the identifier {}".format(job_vol.volume_id))
            except Exception as e:
                logger.error("Failed to run schedule job. Error: {}".format(e))
            finally:
                Locking.unlock(lock_name='ScheduleJob {}'.format(job.id))

            logger.info("Run schedule job successfully")

    logger.info("End backing up data")


@app.task()
def delete_expired_versions():
    with Benji(cfg.CONF) as benji_obj:
        _now = time_utils.get_local_time().replace(hour=0, minute=0, second=0, microsecond=0)
        _next = _now + timedelta(days=1)
        versions = Version.raw_query().filter(Version.expired_at >= _now, Version.expired_at < _next).all()
        for version in versions:
            try:
                version_uid_obj = VersionUid(version.uid)
                benji_obj.rm(version_uid_obj, force=True)
                version.remove()
            except Exception as e:
                logger.debug("Error [check_retention()] {}".format(str(e)))
