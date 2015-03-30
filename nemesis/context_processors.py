# -*- coding: utf-8 -*-
from nemesis.app import app
from datetime import datetime
from nemesis.lib.user import UserUtils, UserProfileManager
from version import version as app_version
from nemesis_version import version as nemesis_version
from nemesis.lib.enum import Enum


@app.context_processor
def enum():
    ps_url = app.config['PRINT_SUBSYSTEM_URL'].rstrip('/')
    return {
        'Enum': Enum,
        'LPU_STYLE': app.config['LPU_STYLE'],

        'user_utils': UserUtils(),
        'user_profiles_mng': UserProfileManager(),

        'print_subsystem_url': ps_url,
        'print_subsystem_templates': '%s/templates/' % ps_url,
        'print_subsystem_print_template': '%s/print_template' % ps_url,

        'copy_year': datetime.today().year,
        'app_version': app_version,
        'nemesis_version': nemesis_version
    }

