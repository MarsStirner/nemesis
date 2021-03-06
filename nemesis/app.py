# -*- coding: utf-8 -*-
from flask import Flask
import pytz
from werkzeug.contrib.profiler import ProfilerMiddleware

app = Flask(__name__)


# noinspection PyUnresolvedReferences
def bootstrap_app(templates_dir):
    from systemwide import db, cache, babel, principal, login_manager, beaker_session

    app.template_folder = templates_dir

    db.init_app(app)
    babel.init_app(app)
    login_manager.init_app(app)
    principal.init_app(app)
    beaker_session.init_app(app)
    cache.init_app(app)

    @babel.timezoneselector
    def get_timezone():
        return pytz.timezone(app.config['TIME_ZONE'])

    if app.config['PROFILE']:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    import models
    import views
    import nemesis.context_processors
