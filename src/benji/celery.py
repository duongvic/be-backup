from celery import Celery
from benji.database import Database

from benji.database import Database
from benji.config import CeleryConfig

app = Celery('benji', broker=CeleryConfig.BROKER_URL)
app.config_from_object(CeleryConfig)
app.autodiscover_tasks()


from benji.io.factory import IOFactory
from benji.storage.factory import StorageFactory

from benji import config as benji_cfg

IOFactory.initialize(benji_cfg.CONF)
StorageFactory.initialize(benji_cfg.CONF)

Database.configure(benji_cfg.CONF)
Database.open()
