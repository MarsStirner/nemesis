# -*- coding: utf-8 -*-
from nemesis.app import app
from nemesis.lib.apiutils import api_method
from nemesis.lib.user import UserAuth
from nemesis.systemwide import cache

__author__ = 'viruzzz-kun'


@cache.memoize(86400)
def api_roles_int(user_login):
    return UserAuth.get_roles_by_login(user_login.strip())


@app.route('/api/roles/')
@app.route('/api/roles/<user_login>')
@api_method
def api_roles(user_login):
    return api_roles_int(user_login)


