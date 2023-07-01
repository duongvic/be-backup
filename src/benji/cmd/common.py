from benji.logging import init_logging
from benji.io.factory import IOFactory
from benji.storage.factory import StorageFactory

from benji import config as benji_cfg


def initialize(extra_opts=None, pre_logging=None):
    init_logging(logfile=benji_cfg.CONF.get('logFile', types=(str, type(None))),
                 console_level=benji_cfg.CONF.get('log_level', 'INFO'),
                 console_formatter=benji_cfg.CONF.get('console_formatter', 'console-colored'))

    IOFactory.initialize(benji_cfg.CONF)
    StorageFactory.initialize(benji_cfg.CONF)

    return benji_cfg.CONF


def with_initialize(main_function=None, **kwargs):
    """
    Decorates a script main function to make sure that dependency imports and
    initialization happens correctly.
    """
    def apply(main_function):
        def run():
            conf = initialize(**kwargs)
            return main_function(conf)

        return run

    if main_function:
        return apply(main_function)
    else:
        return apply
