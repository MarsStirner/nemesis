# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


class UIException(Exception):
    def __init__(self, code, message, title=None, **kwargs):
        self.code = code
        self.message = message
        self.title = title or message
        self.kwargs = kwargs

    def __str__(self):
        return '<UIException (%s)>\n%s\n%s' % (self.code, self.title, self.message)

    def __unicode__(self):
        return u'<UIException (%s)>\n%s\n%s' % (self.code, self.title, self.message)
