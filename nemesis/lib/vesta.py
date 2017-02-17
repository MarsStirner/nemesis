# -*- encoding: utf-8 -*-
import logging
import requests
import urllib

from nemesis.app import app
from nemesis.systemwide import cache
from nemesis.models.kladr_models import KladrLocality, KladrStreet


logger = logging.getLogger('simple')


class VestaException(Exception):
    pass


class VestaNotFoundException(Exception):
    pass


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
        flt = {
            'identparent': parent_code,
            'is_actual': '1'
        }
        if level is not None:
            flt['level'] = level
        try:
            response = requests.post(url, json=flt)
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
                locality_list = []
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

    @classmethod
    @cache.memoize(60)
    def get_rb(cls, name, code=None):
        if code is not None:
            if code == '':
                raise VestaNotFoundException(u'`code` cannot be an empty string')
            url = u'{0}/v2/rb/{1}/data/code/{2}/'.format(cls.get_url(), name, code)
        else:
            url = u'{0}/v2/rb/{1}/data/'.format(cls.get_url(), name)
        response = requests.get(url)
        if response.status_code != 200:
            raise VestaException(u'Error in Vesta server')
        j = response.json()
        if 'result' not in j:
            raise VestaNotFoundException(u'No result from Vesta')
        if '_id' in j['result'] and j['result']['_id'] == 'None':
            raise VestaNotFoundException(u'Empty result from Vesta')
        return j['result']

    @classmethod
    @cache.memoize(60)
    def search_rb(cls, collection_name, kwargs):
        url = u'{0}/v2/rb/{1}/data/?{2}'.format(
            cls.get_url(),
            collection_name,
            u'&'.join([u'{0}={1}'.format(urllib.quote_plus(name.encode('utf-8')),
                                         urllib.quote_plus(val.encode('utf-8')))
                       for name, val in kwargs.iteritems()])
        )
        response = requests.get(url)
        if response.status_code != 200:
            raise VestaException(u'Error in Vesta server')
        j = response.json()
        if 'result' not in j:
            raise VestaNotFoundException(u'No result from Vesta')
        return j['result']

    @classmethod
    def _insert_id(cls, item):
        if 'id' not in item:
            item['id'] = item.get('_id')
        return item


def _make_kladr_locality(loc_info):
    code = loc_info['identcode']
    name = u'{0}. {1}'.format(loc_info['shorttype'], loc_info['name'])
    level = loc_info['level']
    parents = map(_make_kladr_locality, loc_info.get('parents', []))
    return KladrLocality(code=code, name=name, level=level, parents=parents)


def _make_kladr_street(street_info):
    code = street_info['identcode']
    name = u'{0} {1}'.format(street_info['fulltype'], street_info['name'])
    return KladrStreet(code=code, name=name)