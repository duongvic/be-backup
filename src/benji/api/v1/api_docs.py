#
# Copyright (c) 2020 FTI-CAS
#

from flask_restful import Resource
from flask import jsonify
from flask_swagger import swagger

from benji import app


class ApiDocs(Resource):
    def get(self):
        return jsonify(swagger(app))
