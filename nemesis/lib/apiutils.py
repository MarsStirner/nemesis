# -*- coding: utf-8 -*-
import functools
import traceback

__author__ = 'viruzzz-kun'


class ApiException(Exception):
    """Исключение в API-функции
    :ivar code: HTTP-код ответа и соответствующий код в метаданных
    :ivar message: текстовое пояснение ошибки
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return u'%s %s' % (self.code, self.message)


def api_method(func):
    """Декоратор API-функции. Автомагически оборачивает результат или исключение в jsonify-ответ
    :param func: декорируемая функция
    :type func: callable
    """
    from nemesis.lib.utils import jsonify

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except ApiException, e:
            traceback.print_exc()
            return jsonify(None, e.code, e.message)
        except Exception, e:
            traceback.print_exc()
            return jsonify(None, 500, repr(e))
        else:
            return jsonify(result)
    return wrapper