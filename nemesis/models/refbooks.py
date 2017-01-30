# -*- coding: utf-8 -*-
from flask import g
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class RefBookCache(object):
    def __init__(self, data):
        self.__data = data

    def dict(self, key):
        return {getattr(item, key): item for item in self.__data}

    def by_code(self):
        return {item.code: item for item in self.__data}


class RefBookMixin(object):
    @classmethod
    def cache(cls):
        if not hasattr(g, 'rb_cache'):
            g.rb_cache = {}
        if cls.__name__ not in g.rb_cache:
            result = g.rb_cache[cls.__name__] = RefBookCache(cls.query.all())
        else:
            result = g.rb_cache[cls.__name__]
        return result


class rbUnitsGroup(db.Model):
    __tablename__ = "rbUnitsGroup"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    shortname = db.Column(db.String(32), nullable=False)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'short_name': self.shortname,
            'children': self.children,
        }


class rbUnits(db.Model):
    __tablename__ = "rbUnits"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    shortname = db.Column(db.String(32), nullable=False)
    group_id = db.Column(db.ForeignKey("rbUnitsGroup.id"), index=True, nullable=False)

    group = db.relationship('rbUnitsGroup', backref='children')

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'short_name': self.shortname,
            'group_id': self.group_id
        }


class rbFinance(db.Model):
    __tablename__ = 'rbFinance'
    _table_description = u'Источники финансирования'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')
    regionalCode = db.Column(db.String(64), nullable=False, server_default='')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbReserveType(db.Model):
    __tablename__ = 'rbReserveType'
    _table_description = u'Тип резерва'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    color = db.Column(db.String(16), nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')
    regionalCode = db.Column(db.String(64), nullable=False, server_default='')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'deleted': self.deleted,
            'color': self.color,
        }

    def __int__(self):
        return self.id
