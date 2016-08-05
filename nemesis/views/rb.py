# -*- coding: utf-8 -*-

from nemesis.app import app
from nemesis.lib.utils import safe_dict
from nemesis.lib.vesta import Vesta, VestaNotFoundException
from nemesis.models import enums, event, actions, person, organisation, exists, schedule, client, expert_protocol, \
    rls, refbooks, risar, accounting, diagnosis
from nemesis.lib.apiutils import api_method
from nemesis.systemwide import cache

__author__ = 'viruzzz-kun'


def api_refbook_int(name, code=None):
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
                return [safe_dict(rb) for rb in ref_book.query.filter_by(deleted=0).order_by(_order).all()]
            else:
                return [safe_dict(rb) for rb in ref_book.query.order_by(_order).all()]

    return map(Vesta._insert_id, Vesta.get_rb(name))


def check_rb_value_exists(rb_name, value_code, field_name=None):
    for mod in (enums,):
        if hasattr(mod, rb_name):
            ref_book = getattr(mod, rb_name)
            return value_code in ref_book.codes.values()

    for mod in (exists, schedule, actions, client, event, person, organisation, expert_protocol, rls, refbooks, risar,
                accounting, diagnosis):
        if hasattr(mod, rb_name):
            ref_book = getattr(mod, rb_name)

            args = {
                field_name or 'code': value_code
            }
            if 'deleted' in ref_book.__dict__:
                args['deleted'] = 0
            return ref_book.query.filter_by(**args).first() is not None

    try:
        rb_val = Vesta.get_rb(rb_name, value_code)
    except VestaNotFoundException:
        return False
    else:
        return rb_val and rb_val['_id'] not in (None, 'None')


@app.route('/api/rb/')
@app.route('/api/rb/<name>')
@app.route('/api/rb/<name>/<code>')
@api_method
def api_refbook(name, code=None):
    if code and ('|' in code):
        code = code.split('|')
    return api_refbook_int(name, code)


@cache.memoize(86400)
def int_api_thesaurus(code):
    from nemesis.models.exists import rbThesaurus
    flat = []

    def make(item):
        """
        :type item: rbThesaurus
        :return:
        """
        flat.append((
            item.id,
            item.group_id,
            item.code,
            item.name,
            item.template,
        ))
        map(make, rbThesaurus.query.filter(rbThesaurus.group_id == item.id))
    map(make, rbThesaurus.query.filter(rbThesaurus.code == code))
    return flat


@app.route('/api/rbThesaurus/')
@app.route('/api/rbThesaurus/<code>')
@api_method
def api_thesaurus(code=None):
    if code:
        return int_api_thesaurus(code)


