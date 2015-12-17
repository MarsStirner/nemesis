# -*- coding: utf-8 -*-

import types

from nemesis.systemwide import db
from nemesis import models as app_models


class AbstractModelProvider(object):

    session = db.session

    @classmethod
    def set_session(cls, session):
        cls.session = session

    @classmethod
    def get(cls, name):
        raise NotImplementedError()

    @classmethod
    def get_query(cls, name):
        raise NotImplementedError()


class ApplicationModelProvider(AbstractModelProvider):

    @classmethod
    def get(cls, name):
        for module_attr in app_models.__dict__.itervalues():
            if isinstance(module_attr, types.ModuleType) and hasattr(module_attr, name):
                return getattr(module_attr, name)
        raise Exception(u'Не найден класс модели по имени {0}'.format(name))

    @classmethod
    def get_query(cls, name):
        model = cls.get(name)
        return cls.session.query(model)