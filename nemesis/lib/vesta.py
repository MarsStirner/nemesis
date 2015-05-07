# -*- encoding: utf-8 -*-

import requests

from nemesis.app import app
from nemesis.systemwide import cache
from nemesis.lib.utils import logger
from nemesis.models.kladr_models import KladrLocality


class Vesta(object):
    class Result(object):
        def __init__(self, success=True, msg=''):
            self.success = success
            self.message = msg

    @classmethod
    def get_url(cls):
        return u'{0}'.format(app.config['VESTA_URL'].rstrip('/'))

    @classmethod
    def _get_data(cls, url):
        try:
            response = requests.get(url)
            response_json = response.json()
        except (requests.ConnectionError, requests.exceptions.MissingSchema, ValueError) as e:
            logger.error(u'Ошибка получения данных из ПС (url {0}): {1}'.format(url, e), exc_info=True)
            return Vesta.Result(False, u'Ошибка получения данных по url {0}'.format(url)), None
        else:
            return Vesta.Result(), response_json.get('data')

    @classmethod
    @cache.memoize(86400)
    def get_kladr_locality(cls, code):
        if len(code) == 13:  # убрать после конвертации уже записанных кодов кладр
            code = code[:-2]
        url = u'{0}/kladr/city/{1}/'.format(cls.get_url(), code)
        result, data = cls._get_data(url)
        if not result.success:
            locality = KladrLocality(invalid=u'Ошибка загрузки данных кладр')
        else:
            if not data:
                locality = KladrLocality(invalid=u'Не найден адрес в кладр по коду {0}'.format(code))
            else:
                locality_info = data[0]
                name = fullname = u'{0}. {1}'.format(locality_info['shorttype'], locality_info['name'])
                if locality_info['parents']:
                    for parent in locality_info['parents']:
                        fullname = u'{0}, {1}. {2}'.format(fullname, parent['shorttype'], parent['name'])
                locality = KladrLocality(code=code, name=name, fullname=fullname)
        return locality