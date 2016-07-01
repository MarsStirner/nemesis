# -*- coding: utf-8 -*-

import pytz
import re

from flask import Flask, url_for, request
from flask_login import current_user
from werkzeug.contrib.profiler import ProfilerMiddleware

from nemesis.lib.frontend import frontend_config


app = Flask(__name__)


# noinspection PyUnresolvedReferences
def bootstrap_app(templates_dir):
    from systemwide import db, cache, babel, principal, login_manager, beaker_session, celery
    from nemesis.api_blueprint.rb import module as rb_module

    app.register_blueprint(rb_module, url_prefix='/api')

    if templates_dir:
        app.template_folder = templates_dir

    db.init_app(app)
    babel.init_app(app)
    login_manager.init_app(app)
    principal.init_app(app)
    beaker_session.init_app(app)
    cache.init_app(app)
    if app.config['CELERY_ENABLED']:
        celery.init_app(app)

    @babel.timezoneselector
    def get_timezone():
        return pytz.timezone(app.config['TIME_ZONE'])

    if app.config['PROFILE']:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    import models
    import views
    import nemesis.context_processors

    init_logger()
    create_databases(app)
    _init_enums(app)


def init_logger():
    try:
        from nemesis.version import version
    except ImportError:
        version = 'Unversioned Nemesis'
    import logging
    from pysimplelogs2 import SimplelogHandler

    debug_mode = app.config['DEBUG']

    formatter = logging.Formatter(
        u'%(asctime)s - %(pathname)s:%(funcName)s [%(levelname)s] %(message)s'
        if debug_mode else
        u'%(message)s'
    )

    handler = SimplelogHandler()
    url = app.config['SIMPLELOGS_URL']
    handler.set_url(url)
    handler.owner = {
        'name': app.config['PROJECT_NAME'],
        'version': version
    }
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger = logging.getLogger('simple')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

    logger.debug('SimpleLogs Handler initialized')


def create_databases(app):
    from systemwide import db
    if app.config['CELERY_ENABLED']:
        with app.app_context():
            try:
                db.create_all(bind='celery_tasks')
            except Exception, e:
                from celery_config import CAT_DB_NAME
                raise Exception(
                    u'Database with name `{0}` should exist. Additional info: {1}'.format(
                        CAT_DB_NAME, unicode(e.message)
                    )
                )


def _init_enums(app):
    from nemesis.lib.enum import EnumBase
    with app.app_context():
        for EnumClass in EnumBase.loadable_descendants.itervalues():
            EnumClass.reload()


@frontend_config
def fc_urls():
    """
    Неспецифическая конфигурация фронтенда всех производных Nemesis. Общие URL'ы
    :return:
    """
    config = app.config
    coldstar_url = config['COLDSTAR_URL'].rstrip('/') + '/'
    coldstar_ws_url = re.sub(ur'^http(s?)://(.*)$', ur'ws\g<1>://\g<2>', coldstar_url)
    simargl_url = config['SIMARGL_URL'].rstrip('/') + '/'
    pharmexpert_url = config.get('PHARMEXPERT_URL', '').rstrip('/') + '/'
    print_subsystem_url = config.get('PRINT_SUBSYSTEM_URL', '').rstrip('/') + '/'
    current_role = None
    try:
        current_role = current_user.current_role
    except AttributeError:
        pass
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
            },
            'ezekiel': {
                'EventSource': coldstar_url + "ezekiel/es/{0}",
                'WebSocket': coldstar_ws_url + "ezekiel/ws",
            },
            'simargl': {
                'EventSource': simargl_url + 'simargl-es',
                'RPC': simargl_url + 'simargl-rpc',
            },
            'pharmexpert': {
                'get_info_preparation': pharmexpert_url + 'api/getInfoPreparationStatus',
                'get_info_preparation_by_key': pharmexpert_url + 'api/getInfoPreparationByKey',
                'get_info_prepararion_html': pharmexpert_url + 'api/getInfoPreparationHTML',
            },
            'webmis_1_0': {
                'create_event': "{0}patients/{{0}}/appeals/new/?token={1}&role={2}".format(
                    config.get('WEBMIS10_URL', ''),
                    request.cookies.get(config['CASTIEL_AUTH_TOKEN']),
                    current_role
                ),
            },
            'nemesis': {
                'rb_root': url_for('rb.api_refbook'),
                'rbThesaurus_root': url_for('rb.api_thesaurus'),
                'print_subsystem': {
                    'base': print_subsystem_url,
                    'templates': print_subsystem_url + 'templates/',
                    'print': print_subsystem_url + 'print_template'
                },
                'kladr': {
                    'search_city': url_for('kladr_search_city'),
                    'search_street': url_for('kladr_search_street'),
                },
                'area_list': url_for('api_area_list'),
                'roles': url_for('api_roles'),
                'doctors_to_assist': url_for('api_doctors_to_assist'),
            }
        },
        'ui': {
            'defaultHideTimeout': 400
        }
    }


@frontend_config
def fc_settings():
    """
    Неспецифическая конфигурация фронтенда всех производных Nemesis. Общие настройки
    :return:
    """
    from nemesis.lib.settings import Settings
    from nemesis.lib.data_ctrl.utils import get_default_org

    settings = Settings()
    default_org = get_default_org()
    return {
        'settings': {
            'user_idle_timeout': settings.getInt('Auth.UserIdleTimeout', 15 * 60),
            'logout_warning_timeout': settings.getInt('Auth.LogoutWarningTimeout', 200),
        },
        'local_config': {
            'cas_token_name': app.config['CASTIEL_AUTH_TOKEN'],
            'default_org_id': default_org.id if default_org else None,
            'pharmexpert': {
                'enabled': bool(app.config.get('PHARMEXPERT_URL', False)),
                'security_key': app.config.get('PHARMEXPERT_SECURITY_KEY', ''),
            },
        }
    }


