# -*- coding: utf-8 -*-
import functools

__author__ = 'viruzzz-kun'


class Permission(object):
    """
    Мини-костыль для работоспособности имеющегося кода про admin_permission в реалиях нашей БД и нашей парадигмы ролей.
    """
    def __init__(self, code):
        self.code = code

    def require(self, http_exception):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                from flask.ext.login import current_user
                from flask import abort
                if (current_user
                    and current_user.is_authenticated
                    and getattr(current_user, 'current_role') == self.code):

                    return func(*args, **kwargs)
                return abort(http_exception)
            return wrapper
        return decorator

