# -*- coding: utf-8 -*-

from nemesis.systemwide import db


class rbPerinatalRiskRate(db.Model):
    __tablename__ = u'rbPerinatalRiskRate'
    _table_description = u'Степень перинатального риска'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

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

    perinatal_risk_rate = db.relationship('rbPerinatalRiskRate')
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