# -*- coding: utf-8 -*-

import datetime
from nemesis.systemwide import db


class rbPerinatalRiskRate(db.Model):
    __tablename__ = u'rbPerinatalRiskRate'
    _table_description = u'Степень перинатального риска'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    prr_mkbs = db.relationship('rbPerinatalRiskRateMkb', backref='rbPerinatalRiskRate', cascade_backrefs=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class rbPerinatalRiskRateMkb(db.Model):
    __tablename__ = u'rbPerinatalRiskRateMkb'

    id = db.Column(db.Integer, primary_key=True)
    riskRate_id = db.Column(db.Integer, db.ForeignKey('rbPerinatalRiskRate.id'), nullable=False, index=True)
    mkb_id = db.Column(db.Integer, db.ForeignKey('MKB.id'), nullable=False, index=True)

    mkb = db.relationship('MKB')


class rbRateType(db.Model):
    __tablename__ = u'rbRateType'
    _table_description = u'типы коэффициентов'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(45), index=True, nullable=False)
    name = db.Column(db.Unicode(45), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class TerritorialRate(db.Model):
    __tablename__ = u'TerritorialRate'
    _table_description = u'значения коэффициентов по территориям'

    id = db.Column(db.Integer, primary_key=True)
    kladr_code = db.Column(db.Unicode(13))
    rate_type_id = db.Column(db.Integer, db.ForeignKey('rbRateType.id'))
    year = db.Column(db.Integer)
    value = db.Column(db.Float)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    rate_type = db.relationship('rbRateType')


class Errand(db.Model):
    __tablename__ = u'Errand'
    _table_description = u'поручения'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    number = db.Column(db.String(30), nullable=False)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    setPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    execPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    text = db.Column(db.Text, nullable=False)
    plannedExecDate = db.Column(db.DateTime, nullable=False)
    execDate = db.Column(db.DateTime, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), index=True)
    result = db.Column(db.Text, nullable=False)
    readingDate = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)

    event = db.relationship('Event')
    setPerson = db.relationship('Person', foreign_keys=[setPerson_id])
    execPerson = db.relationship('Person', foreign_keys=[execPerson_id])

    def __json__(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'create_datetime':self.createDatetime,
            'number': self.number,
            'set_person': self.setPerson,
            'exec_person': self.execPerson,
            'text': self.text,
            'planned_exec_date': self.plannedExecDate,
            'exec_date': self.execDate,
            'result': self.result,
            'reading_date': self.readingDate
        }
