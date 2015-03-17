# -*- coding: utf-8 -*-

__author__ = 'mmalkov'


class EnumMeta(type):
    def __new__(mcs, name, bases, kwargs):
        codes = {}
        names = {}
        for key, value in kwargs.iteritems():
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], basestring):
                codes[value[0]] = key
                names[value[0]] = value[1]
            elif isinstance(value, int):
                codes[value] = key
        kwargs['codes'] = codes
        kwargs['names'] = names
        cls = type.__new__(mcs, name, bases, kwargs)
        EnumBase.descendants[name] = cls
        return cls


class EnumBase(object):
    descendants = {}

    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return self.codes.get(self.value, None)

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
    def rb(cls):
        return {
            'objects': [{
                'id': key,
                'code': code,
                'name': cls.names.get(key),
            } for key, code in cls.codes.iteritems()],
        }


class Enum(EnumBase):
    """Базовый класс для обёрток недо-енумов"""
    __metaclass__ = EnumMeta