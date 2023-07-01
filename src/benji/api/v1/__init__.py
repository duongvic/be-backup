#
# Copyright (c) 2020 FTI-CAS
#

from flask import Blueprint, request, jsonify, make_response
from flask_restful import Api

from benji import app, config as cfg
from benji.api.v1 import (base, api_docs, version, storage, scrub, schedule_job, node, user, vm)
from benji.database import Database

api_auth = base.auth
bp_v1 = Blueprint('api_v1', __name__)


def before_request():
    if request.method == 'OPTIONS':
        rsp = make_response(jsonify([]), 204)
        rsp.headers['Access-Control-Allow-Origin'] = '*'
        rsp.headers['Access-Control-Allow-Headers'] = "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, " \
                                                      "Authorization, Accept, Origin, Cache-Control, X-Requested-With"
        rsp.headers['Access-Control-Allow-Credentials'] = "true"
        rsp.headers['Access-Control-Allow-Methods'] = "POST, HEAD, PATCH, OPTIONS, GET, PUT, DELETE"
        rsp.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        rsp.headers['Location'] = request.headers['Origin']
        return rsp

    if base.maintenance and not request.path.endswith('/maintenance'):
        return 'Sorry, off for maintenance!', 503

    # Open database connection
    Database.configure(cfg.CONF)
    Database.open()


@bp_v1.after_request
def after_request(rsp):
    rsp.headers['Access-Control-Allow-Origin'] = '*'
    rsp.headers['Access-Control-Allow-Headers'] = "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, " \
                                                  "Authorization, Accept, Origin, Cache-Control, X-Requested-With"
    rsp.headers['Access-Control-Allow-Credentials'] = "true"
    rsp.headers['Access-Control-Allow-Methods'] = "POST, HEAD, PATCH, OPTIONS, GET, PUT, DELETE"
    if request.method == 'OPTIONS':
        rsp.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        rsp.headers['Location'] = request.headers['Origin']
        return rsp
    Database.close()
    return rsp


bp_v1.before_request(before_request)
# bp_v1.after_request(after_request)
api_v1 = Api(bp_v1)
app.register_blueprint(bp_v1, url_prefix='/api/v1/benji')
#
# API DOCS
#
api_v1.add_resource(api_docs.ApiDocs, '/docs', endpoint='api_docs')

api_v1.add_resource(version.Versions, '/versions', endpoint='versions')
api_v1.add_resource(version.Version, '/version/<int:id>', endpoint='version')

api_v1.add_resource(storage.Storages, '/storages', endpoint='storages')
api_v1.add_resource(storage.Storage, '/storage/<int:id>', endpoint='storage')

api_v1.add_resource(scrub.DeepScrub, '/versions/deep-scrub', endpoint='deep-scrub')
api_v1.add_resource(scrub.Scrub, '/versions/scrub', endpoint='scrub')

# Schedule Job
api_v1.add_resource(schedule_job.ScheduleJobs, '/schedule/jobs')
api_v1.add_resource(schedule_job.ScheduleJob, '/schedule/job/<int:id>')

api_v1.add_resource(node.Nodes, '/nodes', endpoint='nodes')
api_v1.add_resource(node.Node, '/node/<int:id>', endpoint='node')

# user_miq
api_v1.add_resource(user.Auth, '/login')
api_v1.add_resource(user.TwoFactors, '/user/two-factors')
api_v1.add_resource(user.TwoFactor, '/user/two-factor')
api_v1.add_resource(user.RecoverTwoFactor, '/two-factor/recovery', endpoint='recover_two_factors')
api_v1.add_resource(user.RefreshToken, '/refresh', endpoint='refresh_token')
api_v1.add_resource(user.UsersStatistic, '/users/statistic', endpoint='users_statistic')
api_v1.add_resource(user.UserStatistic, '/user/statistic',  endpoint='statistic')
api_v1.add_resource(user.Users, '/users', endpoint='users')

# VM
api_v1.add_resource(vm.VMs, '/vms')
api_v1.add_resource(vm.VM, '/vm/backups')
api_v1.add_resource(vm.VmVolumes, '/vm/<int:id>/volumes')

# Backup Group
api_v1.add_resource(vm.VolumeGroups, '/volume-groups')
api_v1.add_resource(vm.VolumeGroup, '/volume-group/<int:id>')
api_v1.add_resource(vm.VolumeBackupGroups, '/volume-backup-groups')
