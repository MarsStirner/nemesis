# -*- coding: utf-8 -*-

from flask import g
from flask.ext.principal import Permission, RoleNeed

from .systemwide import db
from nemesis.models.caesar import Settings, Roles
from nemesis.app import app


def create_config_func(module_name, config_table):

    def _config(code):
        """Возвращает значение конфигурационной переменной, полученной из таблицы %module_name%_config"""
        #Get app_settings
        app_settings = dict()
        try:
            for item in db.session.query(Settings).all():
                app_settings.update({item.code: item.value})
            # app_settings = {item.code: item.value for item in db.session.query(Settings).all()}
        except Exception, e:
            print e

        config = getattr(g, '%s_config' % module_name, None)
        if not config:
            values = db.session.query(config_table).all()
            config = dict()
            for value in values:
                config[value.code] = value.value
            setattr(g, '%s_config' % module_name, config)
        config.update(app_settings)
        return config.get(code, None)

    return _config

permissions = dict()

with app.app_context():
    try:
        roles = db.session.query(Roles).all()
    except Exception, e:
        print e
        permissions['admin'] = Permission(RoleNeed('admin'))
    else:
        if roles:
            for role in roles:
                permissions[role.code] = Permission(RoleNeed(role.code))
                permissions[role.code].description = role.description
        else:
            permissions['admin'] = Permission(RoleNeed('admin'))

# TODO: разобратсья как покрасивше сделать
admin_permission = permissions.get('admin')
user_permission = permissions.get('user')
