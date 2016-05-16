# -*- coding: utf-8 -*-
from flask import url_for

__author__ = 'viruzzz-kun'


def frontend_config(func):
    """
    Декоратор функций, конфигурирующих фронтенд (константа WMConfig)
    Конфигурирующая функция не должна чпринимать параметов и должна возвращать dict.
    :param func: конфигурирующая функция
    """
    from nemesis.app import app
    from nemesis.lib.utils import blend

    if not hasattr(app, 'frontend_config'):
        app.frontend_config = {}

    def deferred():
        # blend сольёт конфигурационные дикты.
        blend(app.frontend_config, func())

    # Кинфигурация будет собрана перед первым запросом, когда уже будут известны все настройки
    app.before_first_request(deferred)
    return func


def uf_placeholders(endpoint, arg_names):
    args = range(-100, -100-len(arg_names), -1)
    kwargs = {
        name: placeholder
        for name, placeholder in zip(arg_names, args)
    }
    url = url_for(endpoint, **kwargs)
    for i, a in enumerate(args):
        url = url.replace(str(a), '{%d}' % i)
    return url
