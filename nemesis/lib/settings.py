# -*- coding: utf-8 -*-

from nemesis.systemwide import db
from nemesis.models.exists import Setting


# TODO: redo for web
class Settings(object):
    """Модель доступа к общим (БД, таблицы Setting) настройкам МИС."""
    _cache = None

    @classmethod
    def loadAll(cls):
        cls._cache = {}
        for setting in Setting.query.all():
            cls._cache[setting.path] = (setting.id, setting.value)

    @classmethod
    def purge(cls):
        cls._cache = None

    @classmethod
    def get(cls, key, default=None):
        if cls._cache is None:
            cls.loadAll()
        if not key in cls._cache:
            cls.set(key, default)
        if key in cls._cache:
            return cls._cache[key][1]

    @classmethod
    def getInt(cls, key, default=0):
        return int(cls.get(key, default))

    @classmethod
    def getString(cls, key, default=''):
        return cls.get(key, default)

    @classmethod
    def getBool(cls, key, default=False):
        try:
            val = int(cls.get(key, default))
        except ValueError:
            return False
        return bool(val)

    @classmethod
    def set(cls, key, val):
        if val is None or val is False:
            val = 0
        elif val is True:
            val = 1
        s = Setting()
        s.path = key
        s.value = val
        if key in cls._cache:
            s.id = cls._cache[key][0]
        db.session.add(s)
        cls._cache[key] = (s.id, val)