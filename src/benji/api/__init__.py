#
# Copyright (c) 2020 FTI-CAS
#

from flask_swagger_ui import get_swaggerui_blueprint

from benji import app


app.register_blueprint(get_swaggerui_blueprint(
    base_url='/api/docs',
    api_url='/api/v1/docs',  # default to show docs of v1
    config={
        'app_name': "Benji API docs"
    },
), url_prefix='/api/docs')
