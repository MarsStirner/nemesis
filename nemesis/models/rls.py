# -*- coding: utf-8 -*-
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class rlsNomen(db.Model):
    __tablename__ = u'rlsNomen'

    id = db.Column(db.Integer, primary_key=True)
    actMatters_id = db.Column(db.ForeignKey('rlsActMatters.id'), index=True)
    tradeName_id = db.Column(db.ForeignKey('rlsTradeName.id'), nullable=False, index=True)
    form_id = db.Column(db.ForeignKey('rlsForm.id'), index=True)
    packing_id = db.Column(db.ForeignKey('rlsPacking.id'), index=True)
    filling_id = db.Column(db.ForeignKey('rlsFilling.id'), index=True)
    unit_id = db.Column(db.ForeignKey('rbUnit.id'), index=True)
    dosageValue = db.Column(db.String(128))
    dosageUnit_id = db.Column(db.ForeignKey('rbUnit.id'), index=True)
    drugLifetime = db.Column(db.Integer)
    regDate = db.Column(db.Date)
    annDate = db.Column(db.Date)

    actMatters = db.relationship(u'rlsActMatters', lazy=False)
    dosageUnit = db.relationship(u'rbUnit', primaryjoin='rlsNomen.dosageUnit_id == rbUnit.id', lazy=False)
    filling = db.relationship(u'rlsFilling', lazy=False)
    form = db.relationship(u'rlsForm', lazy=False)
    packing = db.relationship(u'rlsPacking', lazy=False)
    tradeName = db.relationship(u'rlsTradeName', lazy=False)
    unit = db.relationship(u'rbUnit', primaryjoin='rlsNomen.unit_id == rbUnit.id', lazy=False)

    def __json__(self):
        return {
            'id': self.id,
            'act_matters': unicode(self.actMatters),
            'trade_name': unicode(self.tradeName),
            'form': unicode(self.form),
            'packing': unicode(self.packing),
            'filling': unicode(self.filling),
            'dosage': {
                'value': self.dosageValue,
                'unit': self.dosageUnit,
            },
            'reg_date': self.regDate,
            'ann_date': self.annDate,
            'drug_lifetime': self.drugLifetime,
            'unit': self.unit,
        }


class rlsBalanceOfGoods(db.Model):
    __tablename__ = u'rlsBalanceOfGoods'

    id = db.Column(db.Integer, primary_key=True)
    rlsNomen_id = db.Column(db.ForeignKey('rlsNomen.id'), nullable=False, index=True)
    value = db.Column(db.Float(asdecimal=True), nullable=False)
    bestBefore = db.Column(db.Date, nullable=False)
    disabled = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    updateDateTime = db.Column(db.DateTime)
    storage_id = db.Column(db.ForeignKey('rbStorage.id'), index=True)

    rlsNomen = db.relationship(u'rlsNomen')
    storage = db.relationship(u'rbStorage')


class rbStorage(db.Model):
    __tablename__ = u'rbStorage'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(256))
    orgStructure_id = db.Column(db.ForeignKey('OrgStructure.id'), index=True)

    orgStructure = db.relationship(u'OrgStructure')


class rlsActMatters(db.Model):
    __tablename__ = u'rlsActMatters'
    __table_args__ = (
        db.Index(u'name_localName', u'name', u'localName'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    localName = db.Column(db.String(255))

    def __unicode__(self):
        return self.localName

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'local_name': self.localName,
        }


class rlsTradeName(db.Model):
    __tablename__ = u'rlsTradeName'
    __table_args__ = (
        db.Index(u'name_localName', u'name', u'localName'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    localName = db.Column(db.String(255))

    def __unicode__(self):
        return self.localName

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'local_name': self.localName,
        }


class rlsFilling(db.Model):
    __tablename__ = u'rlsFilling'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class rlsForm(db.Model):
    __tablename__ = u'rlsForm'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class rlsPacking(db.Model):
    __tablename__ = u'rlsPacking'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class v_Nomen(db.Model):
    __tablename__ = u'vNomen'

    id = db.Column(u'id', db.Integer, primary_key=True)
    tradeName = db.Column(u'tradeName', db.String(255))
    tradeLocalName = db.Column(u'tradeLocalName', db.String(255))
    tradeName_id = db.Column(u'tradeName_id', db.Integer)
    actMattersName = db.Column(u'actMattersName', db.String(255))
    actMattersLocalName = db.Column(u'actMattersLocalName', db.String(255))
    actMatters_id = db.Column(u'actMatters_id', db.Integer)
    form = db.Column(u'form', db.String(128))
    packing = db.Column(u'packing', db.String(128))
    filling = db.Column(u'filling', db.String(128))
    unit_id = db.Column(u'unit_id', db.Integer)
    unitCode = db.Column(u'unitCode', db.String(256))
    unitName = db.Column(u'unitName', db.String(256))
    dosageValue = db.Column(u'dosageValue', db.String(128))
    dosageUnit_id = db.Column(u'dosageUnit_id', db.Integer)
    dosageUnitCode = db.Column(u'dosageUnitCode', db.String(256))
    dosageUnitName = db.Column(u'dosageUnitName', db.String(256))
    regDate = db.Column(u'regDate', db.Date)
    annDate = db.Column(u'annDate', db.Date)
    drugLifetime = db.Column(u'drugLifetime', db.Integer)

    def __unicode__(self):
        return ', '.join(unicode(field) for field in (self.tradeName, self.form, self.dosageValue, self.filling))

    def __json__(self):
        return {
            'id': self.id,
            'act_matters': unicode(self.actMattersName),
            'trade_name': unicode(self.tradeLocalName),
            'form': unicode(self.form),
            'packing': unicode(self.packing),
            'filling': unicode(self.filling),
            'dosage': {
                'value': self.dosageValue,
                'unit': {
                    'name': self.dosageUnitName,
                    'code': self.dosageUnitCode,
                },
            },
            'reg_date': self.regDate,
            'ann_date': self.annDate,
            'drug_lifetime': self.drugLifetime,
            'unit': self.unitName,
        }