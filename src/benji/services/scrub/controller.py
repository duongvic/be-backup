from io import StringIO

from benji.services import base
import benji.exception
from benji import __version__
from benji.benji import Benji
from benji.config import Config
from benji.database import Version, VersionUid
from benji.utils import hints_from_rbd_diff, InputValidation, random_string
from benji.versions import VERSIONS

class ScrubController(base.BaseService):
    def __init__(self, config):
        super(ScrubController, self).__init__(config)

    def create_deep_scrub(self, ctx):
        data = ctx.data
        filter_expression = data['filter_expression']
        version_percentage = data['version_percentage']
        block_percentage = data['block_percentage']
        group_label = data['group_label']
        with Benji(self._config) as benji_obj:
            method = 'batch_deep_scrub'
            versions, errors = getattr(benji_obj, method)(filter_expression, version_percentage, block_percentage,
                                                          group_label)

            resp = benji_obj.export_data({'versions': [version.to_dict() for version in versions],
                                          'errors': [error.to_dict() for error in errors]},
                                         ignore_relationships=[
                                             ((Version,), ('blocks',))],
                                         )
            ctx.response = resp
            ctx.status = 201

        

    def create_scrub(self, ctx):
        data = ctx.data
        filter_expression = data['filter_expression']
        version_percentage = data['version_percentage']
        block_percentage = data['block_percentage']
        group_label = data['group_label']
        with Benji(self._config) as benji_obj:
            method = 'batch_scrub'
            versions, errors = getattr(benji_obj, method)(filter_expression, version_percentage, block_percentage,
                                                          group_label)

            resp = benji_obj.export_data({'versions': [version.to_dict() for version in versions], 'errors': [error.to_dict() for error in errors]},
                                         ignore_relationships=[
                                             ((Version,), ('blocks',))],
                                         )
            ctx.response = resp
            ctx.status = 201



