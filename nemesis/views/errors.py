# -*- coding: utf-8 -*-
from flask import flash
from flask import render_template
from flask_login import current_user
from nemesis.app import app
from nemesis.lib.utils import request_wants_json
from nemesis.lib.utils import jsonify

__author__ = 'viruzzz-kun'


@app.errorhandler(403)
def authorisation_failed(e):
    if request_wants_json():
        return jsonify(unicode(e), result_code=403, result_name=u'Forbidden')
    flash(u'У вас недостаточно прав для доступа к функционалу')
    return render_template('user/denied.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    if request_wants_json():
        return jsonify(unicode(e), result_code=404, result_name=u'Page not found')
    flash(u'Указанный вами адрес не найден')
    template_name = '404.html' if current_user.is_authenticated else '404_v2.html'
    return render_template(template_name), 404
