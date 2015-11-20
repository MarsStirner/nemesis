# -*- coding: utf-8 -*-
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


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

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id