# -*- coding: utf-8 -*-
import functools
from weakref import WeakKeyDictionary

__author__ = 'viruzzz-kun'


class lazy(object):
    cache = WeakKeyDictionary()

    def __init__(self, func):
        """
        :type func: types.MethodType
        :param func:
        :return:
        """
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if instance not in self.cache:
            self.cache[instance] = {}
        if self.name not in self.cache[instance]:
            result = self.func(instance)
            self.cache[instance][self.name] = result
            return result
        return self.cache[instance][self.name]


class LocalCache(object):
    def __init__(self):
        self._cache = WeakKeyDictionary()

    def cached_call(self, func):
        name = func.__name__

        @functools.wraps(func)
        def wrapper(this, *args, **kwargs):

            if this not in self._cache:
                cache = self._cache[this] = {}
            else:
                cache = self._cache[this]

            frozen_kwargs = tuple(kwargs.items())
            if (name, args, frozen_kwargs) not in cache:
                result = cache[(name, args, frozen_kwargs)] = func(this, *args, **kwargs)
            else:
                result = cache[(name, args, frozen_kwargs)]
            return result

        return wrapper

    def clean(self, this):
        self._cache[this] = {}
