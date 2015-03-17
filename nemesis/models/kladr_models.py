# -*- coding: utf-8 -*-
from nemesis.systemwide import db


class Kladr(db.Model):
    __bind_key__ = 'kladr'
    __tablename__ = 'KLADR'
    __table_args__ = (
        db.Index('long_name', 'prefix', 'NAME', 'SOCR', 'STATUS'),
        db.Index('NAME', 'NAME', 'SOCR'),
        db.Index('parent', 'parent', 'NAME', 'SOCR', 'CODE')
    )

    NAME = db.Column(db.Unicode(40), nullable=False)
    SOCR = db.Column(db.Unicode(10), nullable=False)
    CODE = db.Column(db.String(13), primary_key=True)
    INDEX = db.Column(db.String(6), nullable=False)
    GNINMB = db.Column(db.String(4), nullable=False)
    UNO = db.Column(db.String(4), nullable=False)
    OCATD = db.Column(db.String(11), nullable=False, index=True)
    STATUS = db.Column(db.String(1), nullable=False)
    parent = db.Column(db.String(13), nullable=False)
    infis = db.Column(db.String(5), nullable=False, index=True)
    prefix = db.Column(db.String(2), nullable=False)
    id = db.Column(db.Integer, nullable=False, unique=True)


class Street(db.Model):
    __bind_key__ = 'kladr'
    __tablename__ = 'STREET'
    __table_args__ = (
        db.Index('NAME_SOCR', 'NAME', 'SOCR', 'CODE'),
    )

    NAME = db.Column(db.Unicode(40), nullable=False)
    SOCR = db.Column(db.Unicode(10), nullable=False)
    CODE = db.Column(db.String(17), primary_key=True)
    INDEX = db.Column(db.String(6), nullable=False)
    GNINMB = db.Column(db.String(4), nullable=False)
    UNO = db.Column(db.String(4), nullable=False)
    OCATD = db.Column(db.String(11), nullable=False)
    infis = db.Column(db.String(5), nullable=False, index=True)