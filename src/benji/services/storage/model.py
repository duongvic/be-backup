from contextlib import AbstractContextManager

from benji.database import Storage, Node
from benji.helpers.data_utils import valid_kwargs
from benji.services.base import BaseModel
from benji import config as cfg


class StorageModel(BaseModel, AbstractContextManager):
    __model__ = Storage

    @valid_kwargs('user_id', 'name', 'module', 'configuration', 'disk_allowed')
    def create(self, **params):
        nodes = Node.raw_query().filter(Node.deleted == False,
                                        Node.disk_used_overcommit <= cfg.CONF.get('lvm_permit_overcommit', 1.4)).all()

        selected_node = min(nodes, key=lambda x: len(x.storages)) if len(nodes) >= 1 else None

        if selected_node is None:
            return None, "Not found any nodes"

        params['node_id'] = selected_node.id
        storage = self.__model__(**params)
        return storage.create()

    @valid_kwargs('disk_allowed')
    def update(self, id, **params):
        storage = self.get(id)
        return storage.update(**params)
