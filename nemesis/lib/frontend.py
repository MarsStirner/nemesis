# -*- coding: utf-8 -*-
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


