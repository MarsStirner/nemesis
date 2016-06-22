# -*- encoding: utf-8 -*-
import logging

import requests

from nemesis.app import app
from nemesis.systemwide import cache
from nemesis.models.kladr_models import InvalidKladrLocality, KladrLocality, InvalidKladrStreet, KladrStreet


logger = logging.getLogger('simple')


class VestaException(Exception):
    pass


class Vesta(object):
    @classmethod
    def get_url(cls):
        return u'{0}'.format(app.config['VESTA_URL'].rstrip('/'))

    @classmethod
    def _get_data(cls, url):
        try:
            response = requests.get(url)
            response_json = response.json()['data']
        except (requests.ConnectionError, requests.exceptions.MissingSchema, ValueError, KeyError) as e:
            logger.exception(u'Ошибка получения данных из ПС (url {0}): {1}'.format(url, e))
            raise VestaException(u'Ошибка получения данных по url {0}'.format(url))
        else:
            return response_json

    @classmethod
    def _post_data(cls, url, data):
        try:
            response = requests.post(url, json=data)
            response_json = response.json()['data']
        except (requests.ConnectionError, requests.exceptions.MissingSchema, ValueError, KeyError) as e:
            logger.exception(u'Ошибка получения данных из ПС (url {0}): {1}'.format(url, e))
            raise VestaException(u'Ошибка получения данных по url {0}'.format(url))
        else:
            return response_json

    # Locality

    @classmethod
    @cache.memoize(86400)
    def get_kladr_locality(cls, code):
        if len(code) == 13:  # убрать после конвертации уже записанных кодов кладр
            code = code[:-2]
        url = u'{0}/kladr/city/{1}/'.format(cls.get_url(), code)
        try:
            data = cls._get_data(url)
            if not data:
                return InvalidKladrLocality(u'Не найден адрес в кладр по коду {0}'.format(code))
            return KladrLocality(data[0])
        except VestaException as e:
            return InvalidKladrLocality(e.message)
        except Exception:
            return InvalidKladrLocality(u'Ошибка загрузки данных КЛАДР')

    @classmethod
    @cache.memoize(86400)
    def get_kladr_locality_list(cls, level, parent_code):
        if len(parent_code) == 13:  # убрать после конвертации уже записанных кодов кладр
            parent_code = parent_code[:-2]
        url = u'{0}/find/KLD172/'.format(cls.get_url())
        try:
            return map(
                KladrLocality,
                cls._post_data(url, {"level": level, "identparent": parent_code, "is_actual": "1"})
            )
        except VestaException as e:
            return [InvalidKladrLocality(e.message)]
        except Exception:
            return [InvalidKladrLocality(u'Ошибка загрузки данных КЛАДР')]

    @classmethod
    @cache.memoize(86400)
    def search_kladr_locality(cls, query, limit=300):
        url = u'{0}/kladr/psg/search/{1}/{2}/'.format(cls.get_url(), query, limit)
        try:
            return map(KladrLocality, cls._get_data(url))
        except VestaException as e:
            return [InvalidKladrLocality(e.message)]
        except Exception:
            return [InvalidKladrLocality(u'Ошибка загрузки данных КЛАДР')]

    # Street

    @classmethod
    @cache.memoize(86400)
    def get_kladr_street(cls, code):
        if len(code) == 17:  # убрать после конвертации уже записанных кодов кладр
            code = code[:-2]
        url = u'{0}/kladr/street/{1}/'.format(cls.get_url(), code)
        try:
            data = cls._get_data(url)
            if not data:
                return InvalidKladrStreet(u'Не найдена улица в кладр по коду {0}'.format(code))
            return KladrStreet(data[0])
        except VestaException as e:
            return InvalidKladrStreet(e.message)
        except Exception:
            return InvalidKladrStreet(u'Ошибка загрузки данных кладр')

    @classmethod
    @cache.memoize(86400)
    def search_kladr_street(cls, locality_code, query, limit=100):
        url = u'{0}/kladr/street/search/{1}/{2}/{3}/'.format(cls.get_url(), locality_code, query, limit)
        try:
            return map(KladrStreet, cls._get_data(url))
        except VestaException as e:
            return InvalidKladrStreet(e.message)
        except Exception:
            return InvalidKladrStreet(u'Ошибка загрузки данных кладр')
