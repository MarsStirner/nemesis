# -*- coding: utf-8 -*-
from contextlib import contextmanager
import functools
import sqlalchemy
import sqlalchemy.orm
from nemesis.lib.utils import jsonify

__author__ = 'viruzzz-kun'


class DetachedSession(object):
    """
    I provide module-level connection abstraction
    """
    def __init__(self, url):
        self.db = sqlalchemy.create_engine(url)
        self.Session = sqlalchemy.orm.sessionmaker()

    @contextmanager
    def session_context(self, auto_commit=False):
        """
        I am context manager that provides SqlAlchemy Session context with automatic commit or rollback
        :param auto_commit: Should I automatically commit session?
        :return:
        """
        s = self.Session(bind=self.db)
        s._model_changes = {}
        try:
            yield s
        except:
            s.rollback()
            raise
        else:
            if auto_commit:
                s.commit()
            else:
                s.rollback()

    def api_db_method(self, auto_commit=False):
        """
        I am decorator that injects SqlAlchemy Session context as the first argument and wraps result as JSON.
        :param auto_commit: Should I automatically commit session?
        :return:
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.session_context(auto_commit) as session:
                    try:
                        result = func(session, *args, **kwargs)
                    except Exception, e:
                        return jsonify({
                            'exception': e.__class__.__name__,
                            'value': repr(e),
                        }, 500, 'Exception')
                    else:
                        return jsonify(result)
            return wrapper
        return decorator