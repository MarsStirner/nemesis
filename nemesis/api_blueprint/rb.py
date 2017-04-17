# -*- coding: utf-8 -*-
import logging
import six
import functools

from copy import copy
from flask import request
from sqlalchemy import or_
from sqlalchemy.orm import noload

from .blueprint import module, rb_cache
from nemesis.lib.apiutils import api_method, ApiException

__author__ = 'viruzzz-kun'


@module.record_once
def initialize_rb(state):
    app = state.app
    config = copy(app.config)
    config['CACHE_KEY_PREFIX'] = config.get('CACHE_KEY_PREFIX_FOR_REFBOOKS', 'flask_cache_refbooks_')
    rb_cache.init_app(state.app, config)


def clears_rb_cache(func):
    """A Decorator which clears the cache of RefBooks after function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        rb_cache.clear()
        return result
    return wrapper


@rb_cache.memoize(300)
def api_refbook_int(name, code=None):
    from nemesis.lib.utils import safe_dict
    from nemesis.lib.vesta import Vesta
    from nemesis.models import enums, event, actions, person, organisation, exists, schedule, client, expert_protocol, \
        rls, refbooks, risar, accounting, diagnosis

    if name is None:
        return []

    if name == 'rbUnitsGroup':
        if code:
            if isinstance(code, list):
                result = []
                for rb in refbooks.rbUnitsGroup.query.filter(refbooks.rbUnitsGroup.code.in_(code)):
                    result.extend(map(safe_dict, rb.children))
                return result
            else:
                obj = refbooks.rbUnitsGroup.query.filter(refbooks.rbUnitsGroup.code == code).first()
                if obj:
                    return map(safe_dict, obj.children)
                else:
                    return []

    for mod in (enums,):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)
            return ref_book.rb()['objects']

    for mod in (exists, schedule, actions, client, event, person, organisation, expert_protocol, rls, refbooks, risar,
                accounting, diagnosis):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)

            _order = ref_book.id
            if hasattr(ref_book, '__mapper_args__') and 'order_by' in ref_book.__mapper_args__:
                _order = ref_book.__mapper_args__['order_by']

            if 'deleted' in ref_book.__dict__:
                return [safe_dict(rb) for rb in ref_book.query.filter_by(deleted=0).order_by(_order)]
            else:
                return [safe_dict(rb) for rb in ref_book.query.order_by(_order)]

    return [
        {'id': item['_id'], 'name': item['name'], 'code': item['code']}
        for item in Vesta.get_rb(name)
    ]


@rb_cache.memoize(600)
def int_thesaurus():
    from nemesis.models.exists import rbThesaurus
    l = [
        (item + (set(),))
        for item in rbThesaurus.query.with_entities(
            rbThesaurus.id,
            rbThesaurus.group_id,
            rbThesaurus.code,
        )
    ]
    d = {
        item[0]: item
        for item in l
    }
    for (id_, gid, code, children) in six.itervalues(d):
        if gid:
            if gid not in d:
                logging.error(u'rbThesaurus.id = %s references not existing rbThesaurus.id = %s', id_, gid)
            else:
                d[gid][3].add(id_)
    c = {
        item[2]: item
        for item in six.itervalues(d)
    }
    return c, d


@rb_cache.memoize(600)
def int_api_thesaurus(code):
    from nemesis.models.exists import rbThesaurus
    c, d = int_thesaurus()
    root = c.get(code)
    if not root:
        return []

    def rec(id_):
        node = d.get(id_)
        if not node:
            return set()
        result = {id_}
        for i in node[3]:
            result.update(rec(i))
        return result

    id_list = rec(root[0])

    return [
        (
            item.id,
            item.group_id,
            item.code,
            item.name,
            item.template,
        )
        for item in rbThesaurus.query.filter(rbThesaurus.id.in_(id_list))
    ]


@rb_cache.memoize(600)
def int_api_symbols(code):
    from nemesis.models.exists import rbSymbol
    from itertools import groupby
    grouped_by_group = groupby(rbSymbol.query.order_by('group_name').all(), lambda row: row.group_name)
    return dict((symb_group, represent_symbols(items))
            for symb_group, items in grouped_by_group)



def represent_symbols(symbols_list):
    return [{
        'id': symbol.id,
        'code': symbol.code,
        'name': symbol.name,
    } for symbol in symbols_list]


@module.route('/rbThesaurus/')
@module.route('/rbThesaurus/<code>')
@api_method
def api_thesaurus(code=None):
    if code:
        return int_api_thesaurus(code)

@module.route('/rbSymbols/')
@module.route('/rbSymbols/<code>')
@api_method
def api_symbols(code=None):
    return int_api_symbols(code)


@module.route('/rb/')
@module.route('/rb/<name>')
@module.route('/rb/<name>/<code>')
@api_method
def api_refbook(name, code=None):
    if code and ('|' in code):
        code = code.split('|')
    return api_refbook_int(name, code or None)


@module.route('/api/rb/search/')
@module.route('/api/rb/search/<name>')
@api_method
def api_refbook_search(name):
    from nemesis.lib.utils import safe_dict
    from nemesis.models import event, actions, person, organisation, exists, schedule, client, expert_protocol, \
        rls, refbooks, risar, accounting, diagnosis
    from nemesis.lib.vesta import Vesta, VestaException

    args = request.args.to_dict()
    query = args.get('query')
    if not query:
        raise ApiException(422, u'Не передан запрос для поиска')

    for mod in (exists, schedule, actions, client, event, person, organisation, expert_protocol, rls, refbooks, risar,
                accounting, diagnosis):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)

            _order = ref_book.id
            if hasattr(ref_book, '__mapper_args__') and 'order_by' in ref_book.__mapper_args__:
                _order = ref_book.__mapper_args__['order_by']

            query = u'%{0}%'.format(query)
            query = ref_book.query.filter(or_(
                ref_book.code.like(query),
                ref_book.name.like(query),
            )).order_by(_order)
            if 'deleted' in ref_book.__dict__:
                query = query.filter_by(deleted=0)
            query = query.options(noload('*')).limit(100)
            return [safe_dict(rb) for rb in query]

    try:
        return map(Vesta._insert_id, Vesta.search_rb(name, args))
    except VestaException, e:
        raise ApiException(404, e.message)
