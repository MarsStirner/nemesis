# -*- coding: utf-8 -*-

from flask import abort

from nemesis.lib.data_ctrl.model_provider import ApplicationModelProvider
from nemesis.systemwide import db
from nemesis.lib.utils import safe_int
from nemesis.lib.pagination import Pagination


class BaseModelController(object):

    session = db.session

    def __init__(self):
        pass

    @classmethod
    def set_session(cls, new_session):
        cls.session = new_session

    @classmethod
    def get_selecter(cls):
        raise NotImplementedError()

    def get_listed_data(self, args):
        selecter = self.get_selecter()
        selecter.apply_filter(**args)
        selecter.apply_sort_order(**args)
        listed_data = selecter.get_all()
        return listed_data

    def get_paginated_data(self, args):
        per_page = safe_int(args.get('per_page')) or 20
        page = safe_int(args.get('page')) or 1
        selecter = self.get_selecter()
        selecter.apply_filter(**args)
        selecter.apply_sort_order(**args)
        paginated_data = selecter.paginate(page, per_page)
        return paginated_data

    def store(self, *entity_list):
        self.session.add_all(entity_list)
        self.session.commit()


class BaseSelecter(object):

    session = db.session
    model_provider = ApplicationModelProvider

    def __init__(self, query):
        self.query = query

    @classmethod
    def set_model_provider(cls, provider):
        cls.model_provider = provider

    def set_base_query(self):
        self.query = None

    def reset(self):
        self.set_base_query()

    def apply_filter(self, **flt_args):
        pass

    def apply_sort_order(self, **order_args):
        pass

    def get_by_id(self, item_id):
        return self.query.get(item_id)

    def get_all(self):
        return self.query.all()

    def get_first(self):
        result = self.query.first()
        return result[0] if result else None

    def get_one(self):
        return self.query.first()

    def paginate(self, page, per_page=20, error_out=False):
        """Returns `per_page` items from page `page`.  By default it will
        abort with 404 if no items were found and the page was larger than
        1.  This behavor can be disabled by setting `error_out` to `False`.

        Returns an :class:`Pagination` object.
        """
        if error_out and page < 1:
            abort(404)
        items = self.query.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)

        # No need to count if we're on the first page and there are fewer
        # items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = self.query.order_by(None).count()

        return Pagination(self, page, per_page, total, items)


class BaseSphinxSearchSelecter(object):

    def __init__(self, search):
        self.search = search

    def apply_filter(self, **flt_args):
        pass

    def apply_sort_order(self, **order_args):
        pass

    def apply_limit(self, **limit_args):
        pass

    def get_all(self):
        return self.search.ask()

    def paginate(self, page, per_page=20, error_out=False):
        raise NotImplementedError()
