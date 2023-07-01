from shade import exc as shade_exc
from shade.client import Client as ShadeClient
from shade.v1.base import OpenStackConfig

from benji import exception as bj_exc


class OpsHandler:
    def __init__(self, ops_auth):
        ops_config = OpenStackConfig(**ops_auth)
        try:
            self.client = ShadeClient(os_config=ops_config)
        except shade_exc.OpenStackCloudException as e:
            self.compute_client = None
            raise bj_exc.BenjiError("Internal Server Error")

    def list_volumes(self, server_id):
        try:
            return self.client.compute.list_volumes(server_id)
        except shade_exc.OpenStackCloudException as e:
            return None

    def get_volume_by_id(self, id):
        try:
            return self.client.volume.get_volume_by_id(id)
        except shade_exc.OpenStackCloudException as e:
            return None