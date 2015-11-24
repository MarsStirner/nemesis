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


class RawApiResult(object):
    """
    Способ управления процессом json-ификации объекта с передачей параметров в
    nemesis.lib.utils.jsonify()
    :ivar obj: arbitrary object
    :ivar result_code: HTTP response code and meta.code
    :ivar result_name: meta.name
    :ivar extra_headers: extra headers
    :ivar indent: indent size for jsonification
    """
    def __init__(self, obj, result_code=200, result_name='OK', extra_headers=None, indent=None):
        if isinstance(obj, RawApiResult):
            self.obj = obj.obj
            self.result_code = obj.result_code
            self.result_name = obj.result_name
            self.extra_headers = obj.extra_headers
            self.indent = obj.indent
        else:
            self.obj = obj
            self.result_code = result_code
            self.result_name = result_name
            self.extra_headers = extra_headers
            self.indent = indent


def api_method(func):
    """Декоратор API-функции. Автомагически оборачивает результат или исключение в jsonify-ответ
    :param func: декорируемая функция
    :type func: callable
    """
    from nemesis.lib.utils import jsonify

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = RawApiResult(func(*args, **kwargs))
        except ApiException, e:
            traceback.print_exc()
            return jsonify(None, e.code, e.message)
        except Exception, e:
            traceback.print_exc()
            return jsonify(None, 500, repr(e))
        else:
            return jsonify(result.obj, result.result_code, result.result_name, result.extra_headers, result.indent)
    return wrapper
