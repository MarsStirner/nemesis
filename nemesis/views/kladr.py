# -*- coding: utf-8 -*-
from nemesis.app import app
from nemesis.lib.apiutils import api_method
from nemesis.lib.vesta import Vesta
from nemesis.systemwide import cache

__author__ = 'viruzzz-kun'


@app.route('/api/kladr/city/search/')
@app.route('/api/kladr/city/search/<search_query>/')
@app.route('/api/kladr/city/search/<search_query>/<limit>/')
@api_method
def kladr_search_city(search_query=None, limit=300):
    if search_query is None:
        return []
    return Vesta.search_kladr_locality(search_query, limit)


@app.route('/api/kladr/street/search/')
@app.route('/api/kladr/street/search/<city_code>/<search_query>/')
@app.route('/api/kladr/street/search/<city_code>/<search_query>/<limit>/')
@api_method
def kladr_search_street(city_code=None, search_query=None, limit=100):
    if city_code is None or search_query is None:
        return []
    return Vesta.search_kladr_street(city_code, search_query, limit)


@app.route('/clear_cache/')
def clear_cache():
    cache.clear()
    import os
    import shutil
    nginx_cache_path = '/var/cache/nginx'
    try:
        cache_list = os.listdir(nginx_cache_path)
        for _name in cache_list:
            entity_path = os.path.join(nginx_cache_path, _name)
            if os.path.isdir(entity_path):
                shutil.rmtree(entity_path)
            elif os.path.isfile(entity_path):
                os.remove(entity_path)
    except Exception as e:
        print e
    return u'Кэш справочников удалён', 200, [('content-type', 'text/plain; charset=utf-8')]


