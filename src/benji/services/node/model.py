from contextlib import AbstractContextManager

from benji.database import Node
from benji.helpers.data_utils import valid_kwargs
from benji.services.base import BaseModel


class NodeModel(BaseModel, AbstractContextManager):
    __model__ = Node

    @valid_kwargs('name', 'host', 'port')
    def create(self, **params):
        node = self.__model__(**params)
        return node.create()

    @valid_kwargs('name', 'host', 'port')
    def update(self, id, **params):
        node = self.get(id)
        return node.update(**params)

