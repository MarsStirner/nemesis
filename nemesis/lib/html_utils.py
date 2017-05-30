# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


class UIException(Exception):
    def __init__(self, code, message, title=None, **kwargs):
        self.code = code
        self.message = message
        self.title = title or message
        self.kwargs = kwargs

    def __str__(self):
        return '<%s (%s)>\n%s\n%s' % (self.__class__.__name__, self.code, self.title, self.message)

    def __unicode__(self):
        return u'<%s (%s)>\n%s\n%s' % (self.__class__.__name__, self.code, self.title, self.message)
