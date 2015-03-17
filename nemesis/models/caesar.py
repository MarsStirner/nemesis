# -*- coding: utf-8 -*-
from nemesis.systemwide import db
from flask_login import UserMixin

TABLE_PREFIX = 'app'


class Settings(db.Model):
    __bind_key__ = 'caesar'
    __tablename__ = '%s_settings' % TABLE_PREFIX

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(25), unique=True, nullable=False)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)
    value = db.Column(db.Unicode(100))

    def __unicode__(self):
        return self.name


class Roles(db.Model):
    __bind_key__ = 'caesar'
    __tablename__ = '%s_roles' % TABLE_PREFIX

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), unique=True)
    name = db.Column(db.Unicode(80), unique=True)
    description = db.Column(db.Unicode(255))


class Users(db.Model, UserMixin):
    __bind_key__ = 'caesar'
    __tablename__ = '%s_users' % TABLE_PREFIX

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    roles = db.relationship(Roles,
                            secondary='%s_users_roles' % TABLE_PREFIX,
                            backref=db.backref('users', lazy='dynamic'))

    def __init__(self, login, password):
        self.login = login
        self.password = password


class UsersRoles(db.Model):
    __bind_key__ = 'caesar'
    __tablename__ = '%s_users_roles' % TABLE_PREFIX

    user_id = db.Column(db.Integer, db.ForeignKey(Users.id), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey(Roles.id), primary_key=True)