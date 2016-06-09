# -*- encoding: utf-8 -*-
from jinja2 import TemplateNotFound
from flask import render_template, abort, redirect, url_for, flash

from nemesis.utils import admin_permission
from nemesis.app import app
from nemesis.systemwide import db


@app.route('/settings/', methods=['GET', 'POST'])
@admin_permission.require(http_exception=403)
def settings_html():
    from nemesis.models.caesar import Settings
    from wtforms import StringField
    from wtforms.validators import DataRequired
    from flask_wtf import Form
    try:
        class ConfigVariablesForm(Form):
            pass

        variables = db.session.query(Settings).order_by('id').all()
        for variable in variables:
            setattr(ConfigVariablesForm,
                    variable.code,
                    StringField(variable.code, validators=[DataRequired()], default="", description=variable.name))

        form = ConfigVariablesForm()
        for variable in variables:
            form[variable.code].value = variable.value

        if form.validate_on_submit():
            for variable in variables:
                variable.value = form.data[variable.code]
            db.session.commit()
            flash(u'Настройки изменены')
            return redirect(url_for('settings_html'))

        return render_template('settings.html', form=form)
    except TemplateNotFound:
        abort(404)


