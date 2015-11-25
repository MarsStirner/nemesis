# -*- coding: utf-8 -*-

import datetime

from nemesis.systemwide import db
from nemesis.models.utils import safe_current_user_id


class Contract(db.Model):
    __tablename__ = u'Contract'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    number = db.Column(db.String(64), nullable=False)
    date = db.Column(db.Date, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('Contract_Contragent.id'), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('Contract_Contragent.id'), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), nullable=False)
    contractType_id = db.Column(db.Integer, db.ForeignKey('rbContractType.id'), nullable=False)
    resolution = db.Column(db.String(512), nullable=False)
    draft = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    recipient = db.relationship('Contract_Contragent', foreign_keys=[recipient_id])
    payer = db.relationship('Contract_Contragent', foreign_keys=[payer_id])
    finance = db.relationship('rbFinance')
    contract_type = db.relationship('rbContractType')
    contingent_list = db.relationship('Contract_Contingent', backref='contract')
    pricelist_list = db.relationship('PriceList', secondary='Contract_PriceList')
    # tariff = db.relationship('ContractTariff',
    #                          primaryjoin='and_(ContractTariff.master_id == Contract.id, ContractTariff.deleted == 0)')

    def __unicode__(self):
        return u'%s %s' % (self.number, self.date)

    def __json__(self):
        return {
            'id': self.id,
            'number': self.number,
            'date': self.date,
            'begDate': self.begDate,
            'endDate': self.endDate,
        }

    def __int__(self):
        return self.id


class Contract_Contragent(db.Model):
    __tablename__ = u'Contract_Contragent'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'))
    organisation_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'))
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    client = db.relationship('Client')
    org = db.relationship('Organisation')


class Contract_Contingent(db.Model):
    __tablename__ = u'Contract_Contingent'

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    client = db.relationship('Client')

    def __json__(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'client_id': self.client_id,
        }


class PriceList(db.Model):
    __tablename__ = u'PriceList'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    code = db.Column(db.Unicode(16), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default=u"'0'")
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    draft = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    finance = db.relationship(u'rbFinance')


class PriceListItem(db.Model):
    __tablename__ = u'PriceListItem'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    priceList_id = db.Column(db.Integer, db.ForeignKey('PriceList.id'), nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default=u"'0'")
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), nullable=False)
    serviceCodeOW = db.Column(db.Unicode(64))
    serviceNameOW = db.Column(db.Unicode(256))
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    price = db.Column(db.Numeric(15, 2), nullable=False)

    service = db.relationship(u'rbService')


class Contract_PriceListAssoc(db.Model):
    __tablename__ = u'Contract_PriceList'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), nullable=False)
    priceList_id = db.Column(db.Integer, db.ForeignKey('PriceList.id'), nullable=False)


class ContractTariff(db.Model):
    __tablename__ = u'Contract_Tariff'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), nullable=False, default='0', index=True)
    eventType_id = db.Column(db.ForeignKey('EventType.id'), index=True)
    tariffType = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.ForeignKey('rbService.id'), index=True)
    code = db.Column(db.Unicode(64), nullable=True)
    name = db.Column(db.Unicode(256), nullable=True)
    tariffCategory_id = db.Column(db.Integer, index=True)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    unit_id = db.Column(db.Integer, index=True)
    amount = db.Column(db.Float(asdecimal=True), nullable=False)
    uet = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    price = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    limitationExceedMode = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitation = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    priceEx = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    MKB = db.Column(db.String(8), nullable=False)
    rbServiceFinance_id = db.Column(db.ForeignKey('rbServiceFinance.id'), index=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer)
    priceList_id = db.Column(db.Integer, db.ForeignKey('PriceList.id'), index=True)

    rbServiceFinance = db.relationship(u'rbServiceFinance')
    price_list = db.relation('PriceList')
    event_type = db.relation('EventType')
    service = db.relation('rbService')


class rbContractType(db.Model):
    __tablename__ = 'rbContractType'
    _table_description = u'Тип контракта'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    counterPartyOne = db.Column(db.SmallInteger, nullable=False)
    counterPartyTwo = db.Column(db.SmallInteger, nullable=False)
    usingInsurancePolicy = db.Column(db.SmallInteger, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'using_insurance_policy': self.usingInsurancePolicy
        }

    def __int__(self):
        return self.id