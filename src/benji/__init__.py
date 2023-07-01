# __path__ = __import__('pkgutil').extend_path(__path__, __name__)

# __all__ = ['__version__', '__path__', 'celery_app', 'app']
from __future__ import absolute_import


from ._version import __version__

# del _version  # remove to avoid confusion with __version__

from flask import Flask
from flask_babel import Babel
from flask_cors import CORS
from flask_executor import Executor
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from benji.config import Config, CeleryConfig
from benji.tasks.schedule_job import run_schedule_job

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = ""
# Hardcode log level
app.logger.setLevel(1)

# CORS
cors = CORS(app, resources={r'/api/*': {'origins': '*'}})

# Executor
thread_executor = Executor(app, name='thread')
process_executor = Executor(app, name='process')

# Limiter
default_limits = []
limiter = Limiter(app, key_func=get_remote_address, default_limits=default_limits)
from benji.api import v1 as api_v1

api = api_v1

babel = Babel(app)
