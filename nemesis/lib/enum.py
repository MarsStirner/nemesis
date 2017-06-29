# -*- coding: utf-8 -*-

__author__ = 'mmalkov'


class EnumMeta(type):
    def __new__(mcs, name, bases, kwargs):
        codes = {}
        names = {}

        for key, value in kwargs.iteritems():
            if name == '__tablename__':
                continue
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], basestring):
                codes[value[0]] = key
                names[value[0]] = value[1]
            elif isinstance(value, int):
                codes[value] = key
        kwargs['codes'] = codes
        kwargs['names'] = names
        cls = type.__new__(mcs, name, bases, kwargs)
        if '__tablename__' in kwargs:
            EnumBase.loadable_descendants[name] = cls
        else:
            EnumBase.descendants[name] = cls
        return cls


class EnumBase(object):
    descendants = {}
    loadable_descendants = {}

    def __init__(self, value):
        self.value = value

    def is_valid(self):
        return self.value in self.codes

    def __unicode__(self):
        return self.codes.get(self.value, None) or u'Unknown id={0}'.format(self.value)

    def __json__(self):
        result = {
            'id': self.value,
            'code': self.__unicode__(),
        }
        if hasattr(self, 'names'):
            result['name'] = self.names.get(self.value, None)
        return result

    @classmethod
    def get_class_by_name(cls, name):
        return cls.descendants.get(name)

    @classmethod
    def getId(cls, code):
        item = getattr(cls, code, None)
        return item[0] if item else None

    @classmethod
    def getName(cls, code):
        item = getattr(cls, code, None)
        return item[1] if item else None

    @classmethod
    def get_values(cls):
        return cls.codes.keys()

    @classmethod
    def get_codes(cls):
        return cls.codes.values()

    @classmethod
    def rb(cls):
        return {
            'objects': [{
                'id': key,
                'code': code,
                'name': cls.names.get(key),
            } for key, code in cls.codes.iteritems()],
        }


class EnumBaseLoadable(EnumBase):

    @classmethod
    def reload(cls):
        from nemesis.systemwide import db
        from nemesis.models.utils import get_class_by_tablename

        klass = get_class_by_tablename(cls.__tablename__)
        if klass:
            codes = {}
            names = {}
            query = db.session.query(klass)
            for record in query:
                setattr(cls, record.code, (record.id, record.name))
                codes[record.id] = record.code
                names[record.id] = record.name
            cls.codes = codes
            cls.names = names


class Enum(EnumBase):
    """Базовый класс для обёрток недо-енумов"""
    __metaclass__ = EnumMeta


class EnumLoadable(EnumBaseLoadable):
    """Базовый класс для обёрток недо-енумов, которые инициализируются
    значениями из таблиц-справочников в бд"""
    __metaclass__ = EnumMeta
