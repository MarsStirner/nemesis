# -*- coding: utf-8 -*-
from wtforms import StringField, BooleanField, PasswordField, RadioField, SelectField
from wtforms.validators import Required, Optional
from flask_wtf import Form


class LoginForm(Form):
    login = StringField(u'Логин', validators=[Required()])
    password = PasswordField(u'Пароль', validators=[Required()])


class RoleForm(Form):
    roles = SelectField(u'Роль', validators=[Optional()], choices=[])

