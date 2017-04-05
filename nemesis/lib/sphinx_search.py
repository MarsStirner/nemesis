# -*- encoding: utf-8 -*-

import re
from collections import namedtuple

from sphinxit.core.helpers import BaseSearchConfig
from sphinxit.core.processor import Search
from nemesis.app import app


ESCAPED_CHARS = namedtuple('EscapedChars', ['single_escape', 'double_escape'])(
    single_escape=("'", '+', '[', ']', '=', '*'),
    double_escape=('@', '!', '^', '(', ')', '~', '-', '|', '/', '<<', '$', '"')
)


def escape_sphinx_query(query):
    # from sphintit/core/convertors.py MatchQueryCtx
    single_escape_chars_re = '|\\'.join(ESCAPED_CHARS.single_escape)
    query = re.sub(
        single_escape_chars_re,
        lambda m: r'\%s' % m.group(),
        query
    )
    double_escape_chars_re = '|\\'.join(ESCAPED_CHARS.double_escape)
    query = re.sub(
        double_escape_chars_re,
        lambda m: r'\\%s' % m.group(),
        query
    )
    return query


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
        words_count = len(name.split())
        if words_count in [2, 3] and not any(ch.isdigit() for ch in name):
            return SearchPatient.search_by_initials(name, limit, paginated, page, per_page, max_matches)
        else:
            return SearchPatient.full_search(name, limit, paginated, page, per_page, max_matches)

    @staticmethod
    def full_search(name, limit=100, paginated=False, page=1, per_page=70, max_matches=10000):
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
        # fixme: after sphinxit merge https://github.com/semirook/sphinxit/pull/20
        search = search.order_by('@weight desc, lastName asc, firstName asc, patrName', 'asc')
        return SearchPatient.make_paginated(search, paginated, page, per_page, limit, max_matches)

    @staticmethod
    def search_by_initials(query_string, limit=100, paginated=False, page=1, per_page=70, max_matches=10000):
        splitted = query_string.split()
        sp_len = len(splitted)
        esq = escape_sphinx_query
        if sp_len == 2:
            st = u'@lastName {0} @firstName {1}'.format(esq(splitted[0]), esq(splitted[1]))
        elif sp_len == 3:
            st = u'@lastName {0} @firstName {1} @patrName {2}'.format(esq(splitted[0]), esq(splitted[1]), esq(splitted[2]))
        else:
            st = query_string
        search = Search(indexes=['patient'], config=SearchConfig)
        search = search.match(st, raw=True)
        search = search.order_by('@weight desc, lastName asc, firstName asc, patrName', 'asc')
        return SearchPatient.make_paginated(search, paginated, page, per_page, limit, max_matches)

    @staticmethod
    def make_paginated(search, paginated, page, per_page, limit, max_matches):
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
