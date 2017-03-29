# -*- encoding: utf-8 -*-
from sphinxit.core.helpers import BaseSearchConfig
from sphinxit.core.nodes import Count, OR, RawAttr
from sphinxit.core.processor import Search, Snippet
from nemesis.app import app


class SearchConfig(BaseSearchConfig):
    DEBUG = app.config['DEBUG']
    WITH_META = True
    WITH_STATUS = DEBUG
    if app.config['SEARCHD_CONNECTION']:
        SEARCHD_CONNECTION = app.config['SEARCHD_CONNECTION']


class SearchPerson():

    @staticmethod
    def search(name):
        search = Search(indexes=['person'], config=SearchConfig)
        search = search.match(name).limit(0, 100)
        result = search.ask()
        return result


class SearchPatient():

    @staticmethod
    def search(name, limit=100, paginated=False, page=1, per_page=70, max_matches=10000):
        search = Search(indexes=['patient'], config=SearchConfig)
        search = search.match(name)
        search = search.options(field_weights={'code': 100,
                                               'lastName': 90,
                                               'birthDate_f1': 80,
                                               'birthDate_f2': 80,
                                               'firstName': 70,
                                               'patrName': 60,
                                               'SNILS': 50,
                                               'document': 50,
                                               'policy': 50})
        #fixme: after sphinxit merge https://github.com/semirook/sphinxit/pull/20
        search = search.order_by('@weight desc, lastName asc, firstName asc, patrName', 'asc')
        if paginated:
            from_ = (page - 1) * per_page
            search = search.limit(from_, per_page)
            search = search.options(max_matches=max_matches)
        else:
            search = search.limit(0, limit)
        result = search.ask()
        return result


class SearchEventService(object):

    @classmethod
    def get_search(cls):
        return Search(indexes=['event_service'], config=SearchConfig)


class SearchEvent():

    @staticmethod
    def search(query):
        search = Search(indexes=['events'], config=SearchConfig)
        search = search.match(query)
        # sphinxit uses set - an unordered data structure - for storing query order params
        search = search.limit(0, 50).order_by('@weight DESC, event_date', 'DESC')
        result = search.ask()
        return result


if __name__ == '__main__':
    data = SearchPerson.search(u'аллерг')
    data = SearchPatient.search(u'Тапка')
    data = SearchEventService.search(u'11.')