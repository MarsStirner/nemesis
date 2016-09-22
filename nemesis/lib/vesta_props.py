# -*- coding: utf-8 -*-
from weakref import WeakKeyDictionary

from nemesis.lib.vesta import Vesta

__author__ = 'viruzzz-kun'


class VestaProperty(object):
    cache = WeakKeyDictionary()

    def __init__(self, local, rb, field='code'):
        self.local = local
        self.rb = rb
        self.field = field

    def __ensure_instance(self, instance):
        if instance not in self.cache:
            self.cache[instance] = {}

    def __pull_vesta(self, value):
        if value:
            return Vesta.get_rb(self.rb, value)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        self.__ensure_instance(instance)
        if self.local not in self.cache[instance]:
            result = self.cache[instance][self.local] = self.__pull_vesta(getattr(instance, self.local))
        else:
            result = self.cache[instance][self.local]
        if isinstance(result, dict):
            result['id'] = result.get('_id')
        return result

    def __set__(self, instance, value):
        if instance is None:
            return
        self.__ensure_instance(instance)
        if isinstance(value, dict):
            raw = value.get(self.field)
        elif isinstance(value, basestring):
            raw = value
            value = self.__pull_vesta(raw)
        else:
            raw = None
            value = None
        self.cache[instance][self.local] = value
        setattr(instance, self.local, raw)
