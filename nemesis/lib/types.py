# -*- coding: utf-8 -*-
from nemesis.lib.utils import safe_traverse_attrs

__author__ = 'viruzzz-kun'


class Undefined(object):
    pass


class CalculatedProperty(object):
    """
    Класс для простых свойств, которые надо считать, кешировать и иногда забывать
    """
    def __init__(self, name):
        """
        @param name: имя поля класса, в котором будут записываться фактические данные
        """
        self.__name = name
        self.__func = None

    def __call__(self, function):
        self.__func = function
        return self

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not hasattr(instance, self.__name):
            setattr(instance, self.__name, self.__func(instance))
        return getattr(instance, self.__name)

    def __set__(self, instance, value):
        setattr(instance, self.__name, value)

    def __delete__(self, instance):
        if hasattr(instance, self.__name):
            delattr(instance, self.__name)


class CalculatedPropertyRO(CalculatedProperty):
    def __set__(self, instance, value):
        raise RuntimeError(u'Cannot set read-only property')


def NOP(a):
    return a


class ProxyField(object):
    _set_converter = NOP
    _get_converter = NOP

    def __init__(self, field_path, default_value=None, ro=False):
        self._field_path = field_path.split('.') if isinstance(field_path, basestring) else field_path
        self._default = default_value
        self._ro = ro

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._get_converter(safe_traverse_attrs(instance, *self._field_path, default=self._default))

    def __set__(self, instance, value):
        if self._ro:
            raise AttributeError('%s.%s is read only' % (instance.__class__, '.'.join(self._field_path)))
        o = instance
        for item in self._field_path[:-1]:
            o = getattr(o, item, Undefined)
            if o is Undefined:
                raise AttributeError('Cannot access property %s.%s' % (instance, '.'.join(self._field_path)))
        setattr(o, self._field_path[-1], self._set_converter(value))

