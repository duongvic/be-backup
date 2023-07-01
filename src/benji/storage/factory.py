#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import importlib
import threading
from typing import Dict, NamedTuple, Any

from benji import config as cfg
from benji.config import Config, ConfigList
from benji.database import Storage, Database
from benji.exception import ConfigurationError, InternalError
from benji.repr import ReprMixIn
from benji.transform.factory import TransformFactory


class _StorageFactoryModule(NamedTuple):
    module: Any
    storage_id: int
    arguments: Dict[str, Any]


class StorageFactory(ReprMixIn):
    _modules: Dict[str, _StorageFactoryModule] = {}
    _local = threading.local()

    def __init__(self) -> None:
        raise InternalError('StorageFactory constructor called.')

    @classmethod
    def _import_modules(cls, config: Config, modules: ConfigList) -> None:
        for index, module_dict in enumerate(modules):
            module = Config.get_from_dict(module_dict,
                                          'module',
                                          types=str,
                                          full_name_override=modules.full_name,
                                          index=index)
            name = Config.get_from_dict(module_dict,
                                        'name',
                                        types=str,
                                        full_name_override=modules.full_name,
                                        index=index)
            storage_id = Config.get_from_dict(module_dict,
                                              'storageId',
                                              None,
                                              types=int,
                                              full_name_override=modules.full_name,
                                              index=index)
            configuration = Config.get_from_dict(module_dict,
                                                 'configuration',
                                                 None,
                                                 types=dict,
                                                 full_name_override=modules.full_name,
                                                 index=index)

            if name in cls._modules:
                raise ConfigurationError('Duplicate name "{}" in list {}.'.format(name, modules.full_name))

            module = importlib.import_module('{}.{}'.format(__package__, module))
            try:
                configuration = config.validate(module=module.__name__, config=configuration)
            except ConfigurationError as exception:
                raise ConfigurationError('Configuration for storage {} is invalid.'.format(name)) from exception
            cls._modules[name] = _StorageFactoryModule(module=module,
                                                       storage_id=storage_id,
                                                       arguments={
                                                           'config': config,
                                                           'name': name,
                                                           'module_configuration': configuration
                                                       })

    @classmethod
    def import_module(cls, config: Config, storage: Storage):
        if storage.name in cls._modules:
            raise ConfigurationError('Duplicate name "{}" in list {}.'.format(storage.name,
                                                                              storage.module.full_name))
        module = importlib.import_module('{}.{}'.format(__package__, storage.module))
        configuration = config.validate(module=module.__name__, config=storage.configuration)
        cls._modules[storage.name] = _StorageFactoryModule(module=module, storage_id=storage.id,
                                                           arguments=dict(config=config, name=storage.name,
                                                                          module_configuration=configuration))

    @classmethod
    def import_modules(cls, config):
        Database.configure(config)
        Database.open()
        storages = Storage.list()
        for storage in storages:
            if storage.name not in cls._modules:
                cls.import_module(config, storage)
        Database.close()

    @classmethod
    def initialize(cls, config: Config) -> None:
        TransformFactory.initialize(config)
        cls._modules = {}
        storages: ConfigList = config.get('storages', types=list)
        cls._import_modules(config, storages)

    @classmethod
    def close(cls) -> None:
        instances = cls._local.__dict__.setdefault('instances', {})

        for storage in instances.values():
            storage.close()

        cls._local.instances = {}

    @classmethod
    def get_by_name(cls, name) -> Any:
        storage = Storage.raw_query().filter(Storage.name == name).one_or_none()
        if storage is None:
            raise ConfigurationError('Storage {} is undefined.'.format(name))
        module = importlib.import_module('{}.{}'.format(__package__, storage.module))
        try:
            configuration = cfg.CONF.validate(module=module.__name__, config=storage.configuration)
        except ConfigurationError as exception:
            raise ConfigurationError('Storage {} is undefined.'.format(name))
        module_arguments = dict(config=cfg.CONF, name=storage.name, module_configuration=configuration)
        return module.Storage(**module_arguments)

    @classmethod
    def get_modules(cls) -> Dict[str, _StorageFactoryModule]:
        return cls._modules
