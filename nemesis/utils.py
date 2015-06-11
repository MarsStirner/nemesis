# -*- coding: utf-8 -*-

from flask import g
from nemesis.lib.misperms import Permission

from .systemwide import db
from nemesis.models.caesar import Settings


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

admin_permission = Permission('admin')
