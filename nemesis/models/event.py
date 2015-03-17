# -*- coding: utf-8 -*-

import datetime
import re

from nemesis.lib.const import PAYER_EVENT_CODES, STATIONARY_EVENT_CODES, DIAGNOSTIC_EVENT_CODES, \
    POLICLINIC_EVENT_CODES, PAID_EVENT_CODE, OMS_EVENT_CODE, DMS_EVENT_CODE, BUDGET_EVENT_CODE, DAY_HOSPITAL_CODE
from nemesis.lib.agesex import AgeSex, parseAgeSelector
from nemesis.lib.settings import Settings
from nemesis.models.client import ClientDocument
from nemesis.models.exists import Person, rbPost, rbCashOperation, rbService
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


class Event(db.Model):
    __tablename__ = u'Event'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    externalId = db.Column(db.String(30), nullable=False)
    eventType_id = db.Column(db.Integer, db.ForeignKey('EventType.id'), nullable=False, index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), index=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), index=True)
    prevEventDate = db.Column(db.DateTime)
    setDate = db.Column(db.DateTime, nullable=False, index=True)
    setPerson_id = db.Column(db.Integer, index=True)
    execDate = db.Column(db.DateTime, index=True)
    execPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    isPrimaryCode = db.Column("isPrimary", db.Integer, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    result_id = db.Column(db.Integer, db.ForeignKey('rbResult.id'), index=True)
    nextEventDate = db.Column(db.DateTime)
    payStatus = db.Column(db.Integer, nullable=False)
    typeAsset_id = db.Column(db.Integer, db.ForeignKey('rbEmergencyTypeAsset.id'), index=True)
    note = db.Column(db.Text, nullable=False, default='')
    curator_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    assistant_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    pregnancyWeek = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    MES_id = db.Column(db.Integer, index=True)
    mesSpecification_id = db.Column(db.ForeignKey('rbMesSpecification.id'), index=True)
    rbAcheResult_id = db.Column(db.ForeignKey('rbAcheResult.id'), index=True)
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    privilege = db.Column(db.Integer, server_default=u"'0'")
    urgent = db.Column(db.Integer, server_default=u"'0'")
    orgStructure_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'))
    uuid_id = db.Column(db.Integer, db.ForeignKey('UUID.id'), nullable=False, index=True, server_default=u"'0'")
    lpu_transfer = db.Column(db.String(100))
    localContract_id = db.Column(db.Integer, db.ForeignKey('Event_LocalContract.id'))

    actions = db.relationship(u'Action', primaryjoin="and_(Action.event_id == Event.id, Action.deleted == 0)")
    eventType = db.relationship(u'EventType')
    execPerson = db.relationship(u'Person', foreign_keys='Event.execPerson_id')
    curator = db.relationship(u'Person', foreign_keys='Event.curator_id')
    assistant = db.relationship(u'Person', foreign_keys='Event.assistant_id')
    contract = db.relationship(u'Contract')
    organisation = db.relationship(u'Organisation')
    orgStructure = db.relationship('OrgStructure')
    mesSpecification = db.relationship(u'rbMesSpecification')
    rbAcheResult = db.relationship(u'rbAcheResult')
    result = db.relationship(u'rbResult')
    typeAsset = db.relationship(u'rbEmergencyTypeAsset')
    localContract = db.relationship(u'EventLocalContract', backref=db.backref('event'))
    payments = db.relationship('EventPayment', backref=db.backref('event'))
    client = db.relationship(u'Client')
    diagnostics = db.relationship(
        u'Diagnostic', lazy=True, innerjoin=True,
        primaryjoin="and_(Event.id == Diagnostic.event_id, Diagnostic.deleted == 0)"
    )
    visits = db.relationship(
        u'Visit',
        primaryjoin="and_(Event.id == Visit.event_id, Visit.deleted == 0)"
    )
    uuid = db.relationship('UUID')

    @property
    def payer_required(self):
        # FIXME: перенести из application.lib.utils загрузку ролей и прав в app.py
        # тогда должны заработать нормальные импорты из utils.py
        from nemesis.lib.utils import safe_traverse_attrs
        return safe_traverse_attrs(self.eventType, 'finance', 'code') in PAYER_EVENT_CODES

    @property
    def isPrimary(self):
        return self.isPrimaryCode == 1

    @property
    def finance(self):
        return self.eventType.finance

    @property
    def departmentManager(self):
        return Person.join(rbPost).filter(
            Person.orgStructure_id == self.orgStructure_id,
            rbPost.flatCode == u'departmentManager'
        ).first()

    @property
    def current_org_structure(self):
        """ Get OrgStructure
        :return: current location of patient
        :rtype: application.models.exists.OrgStructure
        """
        from nemesis.lib.data import get_patient_location
        return get_patient_location(self)

    @property
    def date(self):
        date = self.execDate if self.execDate is not None else datetime.date.today()
        return date

    @property
    def is_closed(self):
        from nemesis.lib.data import addPeriod
        if self.is_stationary:
            # Текущая дата больше, чем дата завершения + 2 рабочих дня
            # согласно какому-то мегаприказу МЗ и главврача ФНКЦ
            # Установлен результат обращения
            return self.is_pre_closed and datetime.date.today() > addPeriod(
                self.execDate.date(),
                Settings.getInt('Event.BlockTime', 2),
                False
            )
        else:
            return self.is_pre_closed

    @property
    def is_pre_closed(self):
        return self.execDate and (self.result_id is not None)

    @property
    def is_policlinic(self):
        return self.eventType.requestType.code in POLICLINIC_EVENT_CODES

    @property
    def is_stationary(self):
        return self.eventType.requestType.code in STATIONARY_EVENT_CODES

    @property
    def is_day_hospital(self):
        return self.eventType.requestType.code == DAY_HOSPITAL_CODE

    @property
    def is_diagnostic(self):
        return self.eventType.requestType.code in DIAGNOSTIC_EVENT_CODES

    @property
    def is_paid(self):
        return self.eventType.finance.code == PAID_EVENT_CODE

    @property
    def is_oms(self):
        return self.eventType.finance.code == OMS_EVENT_CODE

    @property
    def is_dms(self):
        return self.eventType.finance.code == DMS_EVENT_CODE

    @property
    def is_budget(self):
        return self.eventType.finance.code == BUDGET_EVENT_CODE

    def __unicode__(self):
        return unicode(self.eventType)

    def __int__(self):
        return self.id


class EventType(db.Model):
    __tablename__ = u'EventType'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    purpose_id = db.Column(db.Integer, db.ForeignKey('rbEventTypePurpose.id'), index=True)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    scene_id = db.Column(db.ForeignKey('rbScene.id'), index=True)
    visitServiceModifier = db.Column(db.String(128), nullable=False)
    visitServiceFilter = db.Column(db.String(32), nullable=False)
    visitFinance = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionFinance = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    period = db.Column(db.Integer, nullable=False)
    singleInPeriod = db.Column(db.Integer, nullable=False)
    isLong = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    dateInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)
    printContext = db.Column("context", db.String(64), nullable=False)
    form = db.Column(db.String(64), nullable=False)
    minDuration = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    maxDuration = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showStatusActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    showDiagnosticActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    showCureActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    showMiscActionsInPlanner = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    limitStatusActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitDiagnosticActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitCureActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitMiscActionsInput = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showTime = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    medicalAidType_id = db.Column(db.Integer, index=True)
    eventProfile_id = db.Column(db.Integer, index=True)
    mesRequired = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    mesCodeMask = db.Column(db.String(64), server_default=u"''")
    mesNameMask = db.Column(db.String(64), server_default=u"''")
    counter_id = db.Column(db.ForeignKey('rbCounter.id'), index=True)
    isExternal = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isAssistant = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isCurator = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    canHavePayableActions = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isRequiredCoordination = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isOrgStructurePriority = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isTakenTissue = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    sex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    age = db.Column(db.String(9), nullable=False)
    rbMedicalKind_id = db.Column(db.ForeignKey('rbMedicalKind.id'), index=True)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    requestType_id = db.Column(db.Integer, db.ForeignKey('rbRequestType.id'))
    createOnlyActionsWithinPriceList = db.Column(db.SmallInteger)

    counter = db.relationship(u'rbCounter')
    rbMedicalKind = db.relationship(u'rbMedicalKind')
    purpose = db.relationship(u'rbEventTypePurpose')
    finance = db.relationship(u'rbFinance')
    service = db.relationship(u'rbService')
    requestType = db.relationship(u'rbRequestType', lazy=False)
    scene = db.relationship(u'rbScene')

    @classmethod
    def get_default_et(cls):
        """Тип события (обращения по умолчанию).
        Должно браться из настроек, а сейчас это поликлиника(пл) -
        EventType.code = '02'

        """
        return cls.query.filter_by(code='02').first()

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'purpose': self.purpose,
            'finance': self.finance,
            'print_context': self.printContext,
            'form': self.form,
            'mes': {
                'required': self.mesRequired,
                'code_mask': self.mesCodeMask,
                'name_mask': self.mesNameMask,
            },
            'restrictions': AgeSex(self),
            'medical_kind': self.rbMedicalKind,
            'service': self.service,
            'request_type': self.requestType,
            'sex': self.sex,
            'age': self.age,
            'age_tuple': parseAgeSelector(self.age)
        }

    def __int__(self):
        return self.id

    def __unicode__(self):
        return self.name


class EventType_Action(db.Model):
    __tablename__ = u'EventType_Action'

    id = db.Column(db.Integer, primary_key=True)
    eventType_id = db.Column(db.Integer, db.ForeignKey('EventType.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), nullable=False, index=True)
    speciality_id = db.Column(db.Integer, index=True)
    tissueType_id = db.Column(db.Integer, db.ForeignKey('rbTissueType.id'), index=True)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    selectionGroup = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actuality = db.Column(db.Integer, nullable=False)
    expose = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    payable = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    academicDegree_id = db.Column(db.Integer, db.ForeignKey('rbAcademicDegree.id'))

    actionType = db.relationship('ActionType')

    def __json__(self):
        return {
            'id': self.id
        }

    def __int__(self):
        return self.id


class EventLocalContract(db.Model):
    __tablename__ = u'Event_LocalContract'
    __table_args__ = (
        db.Index(u'lastName', u'lastName', u'firstName', u'patrName', u'birthDate', u'id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    master_id = db.Column(db.Integer)
    coordDate = db.Column(db.DateTime)
    coordAgent = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordInspector = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordText = db.Column(db.String, nullable=False)
    dateContract = db.Column(db.Date, nullable=False)
    numberContract = db.Column(db.Unicode(64), nullable=False)
    sumLimit = db.Column(db.Float(asdecimal=True), nullable=False)
    lastName = db.Column(db.Unicode(30), nullable=False)
    firstName = db.Column(db.Unicode(30), nullable=False)
    patrName = db.Column(db.Unicode(30), nullable=False)
    birthDate = db.Column(db.Date, nullable=False, index=True)
    documentType_id = db.Column(db.Integer, db.ForeignKey('rbDocumentType.id'), index=True)
    serialLeft = db.Column(db.Unicode(8), nullable=False)
    serialRight = db.Column(db.Unicode(8), nullable=False)
    number = db.Column(db.String(16), nullable=False)
    regAddress = db.Column(db.Unicode(64), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)

    org = db.relationship(u'Organisation')
    documentType = db.relationship(u'rbDocumentType')
    # payments = db.relationship('EventPayment', backref=db.backref('local_contract'))

    # Это что вообще?!
    @property
    def document(self):
        document = ClientDocument()
        document.documentType = self.documentType
        document.serial = u'%s %s' % (self.serialLeft, self.serialRight)
        document.number = self.number
        return document

    def __unicode__(self):
        parts = []
        if self.coordDate:
            parts.append(u'согласовано ' + self.coordDate)
        if self.coordText:
            parts.append(self.coordText)
        if self.number:
            parts.append(u'№ ' + self.number)
        if self.date:
            parts.append(u'от ' + self.date)
        if self.org:
            parts.append(unicode(self.org))
        else:
            parts.append(self.lastName)
            parts.append(self.firstName)
            parts.append(self.patrName)
        return ' '.join(parts)

    def __json__(self):
        return {
            'id': self.id,
            'number_contract': self.numberContract,
            'date_contract': self.dateContract,
            'first_name': self.firstName,
            'last_name': self.lastName,
            'patr_name': self.patrName,
            'birth_date': self.birthDate,
            'doc_type_id': self.documentType_id,
            'doc_type': self.documentType,
            'serial_left': self.serialLeft,
            'serial_right': self.serialRight,
            'number': self.number,
            'reg_address': self.regAddress,
            'payer_org_id': self.org_id,
            'payer_org': self.org,
        }

    def __int__(self):
        return self.id


class EventPayment(db.Model):
    __tablename__ = 'Event_Payment'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, default=0)
    master_id = db.Column(db.Integer, db.ForeignKey('Event.id'))
    date = db.Column(db.Date, nullable=False)
    cashOperation_id = db.Column(db.ForeignKey('rbCashOperation.id'), index=True)
    sum = db.Column(db.Float(asdecimal=True), nullable=False)
    typePayment = db.Column(db.Integer, nullable=False)
    settlementAccount = db.Column(db.String(64))
    bank_id = db.Column(db.Integer, index=True)
    numberCreditCard = db.Column(db.String(64))
    cashBox = db.Column(db.String(32), nullable=False)
    sumDiscount = db.Column(db.Float(asdecimal=True), nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'))
    localContract_id = db.Column(db.Integer, db.ForeignKey('Event_LocalContract.id'))

    createPerson = db.relationship('Person')
    cashOperation = db.relationship(u'rbCashOperation')

    def __json__(self):
        return {
            'id': self.id,
            'date': self.date,
            'sum': self.sum,
            'sum_discount': self.sumDiscount,
            'action_id': self.action_id,
            'service_id': self.service_id,
            'localContract_id': self.localContract_id,
        }


class Diagnosis(db.Model):
    __tablename__ = u'Diagnosis'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    client_id = db.Column(db.ForeignKey('Client.id'), index=True, nullable=False)
    diagnosisType_id = db.Column(db.ForeignKey('rbDiagnosisType.id'), index=True, nullable=False)
    character_id = db.Column(db.ForeignKey('rbDiseaseCharacter.id'), index=True)
    MKB = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    MKBEx = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    dispanser_id = db.Column(db.ForeignKey('rbDispanser.id'), index=True)
    traumaType_id = db.Column(db.ForeignKey('rbTraumaType.id'), index=True)
    setDate = db.Column(db.Date)
    endDate = db.Column(db.Date)
    mod_id = db.Column(db.ForeignKey('Diagnosis.id'), index=True)
    person_id = db.Column(db.ForeignKey('Person.id'), index=True)
    # diagnosisName = db.Column(db.String(64), nullable=False)

    person = db.relationship('Person', foreign_keys=[person_id], lazy=False, innerjoin=True)
    client = db.relationship('Client')
    diagnosisType = db.relationship('rbDiagnosisType', lazy=False, innerjoin=True)
    character = db.relationship('rbDiseaseCharacter', lazy=False)
    mkb = db.relationship('MKB', foreign_keys=[MKB])
    mkb_ex = db.relationship('MKB', foreign_keys=[MKBEx])
    dispanser = db.relationship('rbDispanser', lazy=False)
    mod = db.relationship('Diagnosis', remote_side=[id])
    traumaType = db.relationship('rbTraumaType', lazy=False)

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'diagnosisType': self.diagnosisType,
            'character': self.character
        }


class Diagnostic(db.Model):
    __tablename__ = u'Diagnostic'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False, index=True)
    diagnosis_id = db.Column(db.ForeignKey('Diagnosis.id'), index=True)
    diagnosisType_id = db.Column(db.ForeignKey('rbDiagnosisType.id'), index=True, nullable=False)
    character_id = db.Column(db.ForeignKey('rbDiseaseCharacter.id'), index=True)
    stage_id = db.Column(db.ForeignKey('rbDiseaseStage.id'), index=True)
    phase_id = db.Column(db.ForeignKey('rbDiseasePhases.id'), index=True)
    dispanser_id = db.Column(db.ForeignKey('rbDispanser.id'), index=True)
    sanatorium = db.Column(db.Integer, nullable=False)
    hospital = db.Column(db.Integer, nullable=False)
    traumaType_id = db.Column(db.ForeignKey('rbTraumaType.id'), index=True)
    speciality_id = db.Column(db.Integer, nullable=False, index=True)
    person_id = db.Column(db.ForeignKey('Person.id'), index=True)
    healthGroup_id = db.Column(db.ForeignKey('rbHealthGroup.id'), index=True)
    result_id = db.Column(db.ForeignKey('rbResult.id'), index=True)
    setDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime)
    notes = db.Column(db.Text, nullable=False, default='')
    rbAcheResult_id = db.Column(db.ForeignKey('rbAcheResult.id'), index=True)
    version = db.Column(db.Integer, nullable=False, default=0)
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'), index=True)
    diagnosis_description = db.Column(db.Text)

    rbAcheResult = db.relationship(u'rbAcheResult', innerjoin=True)
    result = db.relationship(u'rbResult', innerjoin=True)
    person = db.relationship('Person', foreign_keys=[person_id])
    event = db.relationship('Event', innerjoin=True)
    diagnoses = db.relationship(
        'Diagnosis', innerjoin=True, lazy=False, uselist=True,
        primaryjoin='and_(Diagnostic.diagnosis_id == Diagnosis.id, Diagnosis.deleted == 0)'
    )
    diagnosis = db.relationship('Diagnosis')
    diagnosisType = db.relationship('rbDiagnosisType', lazy=False, innerjoin=True)
    character = db.relationship('rbDiseaseCharacter')
    stage = db.relationship('rbDiseaseStage', lazy=False)
    phase = db.relationship('rbDiseasePhases', lazy=False)
    dispanser = db.relationship('rbDispanser')
    traumaType = db.relationship('rbTraumaType')
    healthGroup = db.relationship('rbHealthGroup', lazy=False)
    action = db.relationship('Action')
    modifyPerson = db.relationship('Person', foreign_keys=[modifyPerson_id])

    def __int__(self):
        return self.id


def modify_service_code(original, *args):
    def apply_modifier(o, m):
        if not m:
            return o
        elif m.startswith('-'):
            return u''
        elif m.startswith('+'):
            return m[1:]
        elif m.startswith('~'):
            return m[1:] + o[1:]
        else:
            parts = m.split(m[0]) if m else []
            if len(parts) != 4:
                raise Exception(u'invalid service regexp modifier (%s)' % m)
            return re.sub(parts[1], parts[2], o, flags=re.I if 'I' in parts[3].upper() else 0)
    # for modifier in args:
    #     original = apply_modifier(original, modifier)
    return reduce(apply_modifier, args, original)


class Visit(db.Model):
    __tablename__ = u'Visit'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False, index=True)
    scene_id = db.Column(db.ForeignKey('rbScene.id'), nullable=False, index=True)
    date = db.Column(db.DateTime, nullable=False)
    visitType_id = db.Column(db.ForeignKey('rbVisitType.id'), nullable=False, index=True)
    person_id = db.Column(db.ForeignKey('Person.id'), nullable=False, index=True)
    isPrimary = db.Column(db.Integer, nullable=False)
    finance_id = db.Column(db.ForeignKey('rbFinance.id'), nullable=False, index=True)
    service_id = db.Column(db.ForeignKey('rbService.id'), index=True)
    payStatus = db.Column(db.Integer, nullable=False)

    service = db.relationship(u'rbService')
    person = db.relationship(u'Person')
    finance = db.relationship(u'rbFinance')
    scene = db.relationship(u'rbScene')
    visitType = db.relationship(u'rbVisitType')
    event = db.relationship(u'Event')

    @classmethod
    def make_default(cls, event):
        from nemesis.lib.utils import safe_traverse_attrs
        visit = cls()
        visit.date = event.setDate
        visit.event = event
        visit.person = event.execPerson
        visit.scene = event.eventType.scene or rbScene.query.filter(rbScene.code == '1').first()
        visit.visitType = rbVisitType.query.filter(rbVisitType.code == '').first()
        if event.eventType.visitFinance:
            visit.finance = event.execPerson.finance
        else:
            visit.finance = event.eventType.finance
        base_service = event.eventType.service or safe_traverse_attrs(event.execPerson, 'speciality', 'service')
        if base_service:
            bsc = modify_service_code(
                base_service.code,
                event.eventType.visitServiceModifier,
                visit.visitType.serviceModifier,
                visit.scene.serviceModifier
            )
            visit.service = rbService.query.filter(rbService.code == bsc).first()
        visit.payStatus = 0
        visit.isPrimary = 0
        return visit


class rbScene(db.Model):
    __tablename__ = u'rbScene'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    serviceModifier = db.Column(db.Unicode(128), nullable=False)


class rbVisitType(db.Model):
    __tablename__ = u'rbVisitType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    serviceModifier = db.Column(db.Unicode(128), nullable=False)


class Event_Persons(db.Model):
    __tablename__ = u'Event_Persons'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False, index=True)
    person_id = db.Column(db.ForeignKey('Person.id'), nullable=False, index=True)
    begDate = db.Column(db.DateTime, nullable=False)
    endDate = db.Column(db.DateTime)

    event = db.relationship('Event')
    person = db.relationship('Person')