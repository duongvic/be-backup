from benji import config as benji_cfg
from benji.cmd.common import with_initialize
from benji.logging import logger


def rest_api(config, bind_address: str, bind_port: int):
    from benji import app as benji_app
    benji_app.config.from_object(config)
    logger.info(f'Starting REST API via gunicorn on {bind_address}:{bind_port}.')
    benji_app.run(host=bind_address, port=bind_port, debug=True)


@with_initialize
def main(conf):
    rest_api(conf, benji_cfg.CONF.get('bind_host'),  benji_cfg.CONF.get('bind_port'))


if __name__ == '__main__':
    main()
