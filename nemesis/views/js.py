# -*- coding: utf-8 -*-
from flask import render_template_string
from flask_login import current_user
from nemesis.app import app
from nemesis.lib.apiutils import api_method
from nemesis.lib.utils import safe_traverse

__author__ = 'viruzzz-kun'


@app.route('/api/current-user.json')
@api_method
def api_current_user():
    return current_user.export_js()


@app.route('/config.js')
def config_js():
    conf = getattr(app, 'frontend_config', {})
    return (
        render_template_string(
            """'use strict'; angular.module('hitsl.core').constant('WMConfig', {{ config|tojson|safe }});""",
            config=conf),
        200,
        [('Content-Type', 'application/ecmascript; charset=utf-8')]
    )


@app.route('/current_user.js')
def current_user_js():
    return (
        render_template_string("""'use strict';
angular.module('hitsl.core')
.service('CurrentUser', [function () {
    var self = this;
    angular.extend(self, {{ current_user | tojson | safe }});
    self.get_main_user = function () {
        return this.master || this;
    };
    self.has_right = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.get_user().rights)).length > 0;
    };
    self.has_role = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.roles)).length > 0;
    };
    self.current_role_in = function () {
        return [].clone.call(arguments).has(this.current_role);
    };
}]);""", current_user=current_user.export_js()),
        200,
        [('Content-Type', 'application/ecmascript; charset=utf-8')]
    )


@app.route('/specific_js_config.js')
def specific_js_config():
    parts = []
    new_href_protocols = safe_traverse(app.config, 'system_prefs', 'ui', 'frontend_additional_href_protocols')
    if new_href_protocols is not None:
        protocols_regex = '^\s*(https?|ftp|mailto|{0}):'.format(new_href_protocols)
        parts.append(u"""\
angular.module('hitsl.ui').config(['$compileProvider',
    function( $compileProvider )
    {{
        $compileProvider.aHrefSanitizationWhitelist(/{0}/);
    }}
]);""".format(protocols_regex))

    return (
        render_template_string(u'\n'.join(parts)),
        200,
        [('Content-Type', 'application/ecmascript; charset=utf-8')]
    )
