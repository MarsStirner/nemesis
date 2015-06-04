# -*- encoding: utf-8 -*-

import requests
import json

from nemesis.app import app
from nemesis.systemwide import cache
from nemesis.lib.utils import logger
from nemesis.models.kladr_models import KladrLocality, KladrStreet


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
                loc_info = data[0]
                locality = _make_kladr_locality(loc_info)
        return locality

    @classmethod
    @cache.memoize(86400)
    def get_kladr_locality_list(cls, level, parent_code):
        locality_list = []
        if len(parent_code) == 13:  # убрать после конвертации уже записанных кодов кладр
            parent_code = parent_code[:-2]
        url = u'{0}/find/KLD172/'.format(cls.get_url())
        try:
            response = requests.post(url, data=json.dumps({"level": level,
                                                           "identparent": parent_code,
                                                           "is_actual": "1"}))
            response_json = response.json()
        except (requests.ConnectionError, requests.exceptions.MissingSchema, ValueError) as e:
            logger.error(u'Ошибка получения данных из ПС (url {0}): {1}'.format(url, e), exc_info=True)
            result = Vesta.Result(False, u'Ошибка получения данных по url {0}'.format(url)), None
        else:
            result, data = Vesta.Result(), response_json.get('data')

        if not result.success:
            locality_list = [KladrLocality(invalid=u'Ошибка загрузки данных кладр')]
        else:
            if not data:
                locality_list = [KladrLocality(invalid=u'Не найдены адреса в кладр уровня {0} по коду {1}'.format(level, parent_code))]
            else:
                for loc_info in data:
                    name = fullname = u'{0}. {1}'.format(loc_info['shorttype'], loc_info['name'])
                    locality_list.append(KladrLocality(code=loc_info['identcode'], name=name, fullname=fullname,
                                                       parent_code=loc_info['identparent']))
        return locality_list

    @classmethod
    @cache.memoize(86400)
    def get_kladr_street(cls, code):
        if len(code) == 17:  # убрать после конвертации уже записанных кодов кладр
            code = code[:-2]
        url = u'{0}/kladr/street/{1}/'.format(cls.get_url(), code)
        result, data = cls._get_data(url)
        if not result.success:
            locality = KladrStreet(invalid=u'Ошибка загрузки данных кладр')
        else:
            if not data:
                locality = KladrStreet(invalid=u'Не найдена улица в кладр по коду {0}'.format(code))
            else:
                street_info = data[0]
                locality = _make_kladr_street(street_info)
        return locality

    @classmethod
    @cache.memoize(86400)
    def search_kladr_locality(cls, query, limit=300):
        url = u'{0}/kladr/psg/search/{1}/{2}/'.format(cls.get_url(), query, limit)
        result, data = cls._get_data(url)
        if result.success and data:
            return [_make_kladr_locality(loc_info) for loc_info in data]
        else:
            return []

    @classmethod
    @cache.memoize(86400)
    def search_kladr_street(cls, locality_code, query, limit=100):
        url = u'{0}/kladr/street/search/{1}/{2}/{3}/'.format(cls.get_url(), locality_code, query, limit)
        result, data = cls._get_data(url)
        if result.success and data:
            return [_make_kladr_street(street_info) for street_info in data]
        else:
            return []


def _make_kladr_locality(loc_info):
    code = loc_info['identcode']
    name = fullname = u'{0}. {1}'.format(loc_info['shorttype'], loc_info['name'])
    if loc_info['parents']:
        for parent in loc_info['parents']:
            fullname = u'{0}, {1}. {2}'.format(fullname, parent['shorttype'], parent['name'])
    return KladrLocality(code=code, name=name, fullname=fullname)


def _make_kladr_street(street_info):
    code = street_info['identcode']
    name = u'{0} {1}'.format(street_info['fulltype'], street_info['name'])
    return KladrStreet(code=code, name=name)