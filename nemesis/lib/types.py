# -*- coding: utf-8 -*-

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
