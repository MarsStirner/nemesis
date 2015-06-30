# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import Table

from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


organisation_mkb_assoc = Table(
    'Organisation_MKB', db.metadata,
    db.Column('mkb_id', db.ForeignKey('MKB.id')),
    db.Column('org_id', db.ForeignKey('Organisation.id')),
)


class Organisation(db.Model):
    __tablename__ = 'Organisation'
    __table_args__ = (
        db.Index(u'shortName', u'shortName', u'INN', u'OGRN'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    fullName = db.Column(db.String(255), nullable=False)
    shortName = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False, index=True)
    net_id = db.Column(db.Integer, db.ForeignKey('rbNet.id'), index=True)
    infisCode = db.Column(db.String(12), nullable=False, index=True)
    obsoleteInfisCode = db.Column(db.String(60), nullable=False)
    OKVED = db.Column(db.String(64), nullable=False, index=True)
    INN = db.Column(db.String(15), nullable=False, index=True)
    KPP = db.Column(db.String(15), nullable=False)
    OGRN = db.Column(db.String(15), nullable=False, index=True)
    OKATO = db.Column(db.String(15), nullable=False)
    OKPF_code = db.Column(db.String(4), nullable=False)
    OKPF_id = db.Column(db.Integer, db.ForeignKey('rbOKPF.id'), index=True)
    OKFS_code = db.Column(db.Integer, nullable=False)
    OKFS_id = db.Column(db.Integer, db.ForeignKey('rbOKFS.id'), index=True)
    OKPO = db.Column(db.String(15), nullable=False)
    FSS = db.Column(db.String(10), nullable=False)
    region = db.Column(db.String(40), nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    chief = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    accountant = db.Column(db.String(64), nullable=False)
    isInsurer = db.Column(db.Integer, nullable=False, index=True)
    compulsoryServiceStop = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    voluntaryServiceStop = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    area = db.Column(db.String(13), nullable=False)
    isHospital = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    notes = db.Column(db.String, nullable=False)
    head_id = db.Column(db.Integer, index=True)
    miacCode = db.Column(db.String(10), nullable=False)
    isOrganisation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    uuid_id = db.Column(db.Integer, db.ForeignKey('UUID.id'), nullable=False, index=True, server_default=u"'0'")

    net = db.relationship('rbNet')
    OKPF = db.relationship('rbOKPF')
    OKFS = db.relationship('rbOKFS')
    uuid = db.relationship('UUID')
    mkbs = db.relationship('MKB', secondary=organisation_mkb_assoc)
    org_ohcls = db.relationship('Organisation_OrganisationHCL', backref='organisation', cascade_backrefs=False)

    @property
    def is_insurer(self):
        return bool(self.isInsurer)

    @property
    def is_hospital(self):
        return bool(self.isHospital)

    @property
    def kladr_locality(self):
        if self.area:
            if not hasattr(self, '_kladr_locality'):
                from nemesis.lib.vesta import Vesta
                self._kladr_locality = Vesta.get_kladr_locality(self.area)
            return self._kladr_locality
        else:
            return None

    @kladr_locality.setter
    def kladr_locality(self, value):
        self.area = value
        if hasattr(self, '_kladr_locality'):
            delattr(self, '_kladr_locality')

    def __unicode__(self):
        return self.fullName

    def __json__(self):
        return {
            'id': self.id,
            'full_name': self.fullName,
            'short_name': self.shortName,
            'title': self.title,
            'infis': self.infisCode,
            'is_insurer': bool(self.isInsurer),
            'is_hospital': bool(self.isHospital),
            'address': self.Address,
            'phone': self.phone,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class OrganisationAccount(db.Model):
    __tablename__ = u'Organisation_Account'

    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    bankName = db.Column(db.Unicode(128), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String, nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('Bank.id'), nullable=False, index=True)
    cash = db.Column(db.Integer, nullable=False)

    org = db.relationship(u'Organisation')
    bank = db.relationship(u'Bank')

    def __json__(self):
        return {
            'id': self.id,
            'bank_name': self.bankName,
            'name': self.name,
            'notes': self.notes,
            'cash': self.cash,
            'bank': self.bank,
        }

    def __int__(self):
        return self.id


class OrganisationHealthCareLevel(db.Model):
    __tablename__ = u'OrganisationHealthCareLevel'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    code = db.Column(db.Unicode(16))
    name = db.Column(db.Unicode(255), nullable=False)
    description = db.Column(db.Unicode(512))
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    idx = db.Column(db.Integer, nullable=False, server_default="'0'")
    perinatalRiskRate_id = db.Column(db.Integer, db.ForeignKey('rbPerinatalRiskRate.id'), nullable=False, index=True)

    perinatal_risk_rate = db.relationship('rbPerinatalRiskRate')


class Organisation_OrganisationHCL(db.Model):
    __tablename__ = u'Organisation_OrganisationHCL'

    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    orgHCL_id = db.Column(db.Integer, db.ForeignKey('OrganisationHealthCareLevel.id'), nullable=False, index=True)

    ohcl = db.relationship(
        'OrganisationHealthCareLevel',
        backref='org_ohcl', cascade_backrefs=False
    )
