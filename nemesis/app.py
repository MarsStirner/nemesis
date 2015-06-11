# -*- coding: utf-8 -*-
from flask import Flask, url_for
import pytz
from werkzeug.contrib.profiler import ProfilerMiddleware
from nemesis.lib.frontend import frontend_config

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

    from pysimplelogs.logger import SimpleLogger
    from version import version

    SimpleLogger.get_logger(
        app.config['SIMPLELOGS_URL'],
        app.config['PROJECT_NAME'],
        dict(name=app.config['PROJECT_NAME'], version=version),
        app.config['DEBUG']
    )


@frontend_config
def fc_urls():
    """
    Неспецифическая конфигурация фронтенда всех производных Nemesis. Общие URL'ы
    :return:
    """
    config = app.config
    coldstar_url = config['COLDSTAR_URL'].rstrip('/') + '/'
    return {
        'url': {
            'logout': url_for("logout"),
            'coldstar': {
                'cas_check_token': coldstar_url + "cas/api/check/",
                'cas_prolong_token': coldstar_url + "cas/api/prolong/",
                'cas_release_token': coldstar_url + "cas/api/release/",
                'scan_get_device_list': coldstar_url + "scan/list/",
                'scan_process_scan': coldstar_url + "scan/scan",
                'ezekiel_acquire_lock': coldstar_url + "ezekiel/acquire/{0}",
                'ezekiel_prolong_lock': coldstar_url + "ezekiel/prolong/{0}",
                'ezekiel_release_lock': coldstar_url + "ezekiel/release/{0}",
            }
        }
    }


@frontend_config
def fc_settings():
    """
    Неспецифическая конфигурация фронтенда всех производных Nemesis. Общие настройки
    :return:
    """
    from nemesis.lib.settings import Settings

    settings = Settings()
    return {
        'settings': {
            'user_idle_timeout': settings.getInt('Auth.UserIdleTimeout', 15 * 60),
            'logout_warning_timeout': settings.getInt('Auth.LogoutWarningTimeout', 200),
        }
    }


