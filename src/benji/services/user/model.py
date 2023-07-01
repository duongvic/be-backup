from contextlib import AbstractContextManager

from benji.database import User
from benji.services.base import BaseModel


class UserModel(BaseModel, AbstractContextManager):
    __model__ = User

