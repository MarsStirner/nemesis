# -*- coding: utf-8 -*-
from pytz import timezone
from nemesis.app import app
from datetime import datetime
from nemesis.lib.user import UserUtils, UserProfileManager
from version import version as _version, last_change_date

@app.context_processor
def copyright():
    return dict(copy_year=datetime.today().year)


@app.context_processor
def version():
    change_date = timezone(app.config['TIME_ZONE']).localize(last_change_date)
    return dict(version=_version, change_date=change_date)


@app.context_processor
def print_subsystem():
    ps_url = app.config['PRINT_SUBSYSTEM_URL'].rstrip('/')
    return {
        'print_subsystem_url': ps_url,
        'print_subsystem_templates': '%s/templates/' % ps_url,
        'print_subsystem_print_template': '%s/print_template' % ps_url,
    }


@app.context_processor
def user_utils():
    return {
        'user_utils': UserUtils(),
        'user_profiles_mng': UserProfileManager()
    }
