# -*- coding: utf-8 -*-
import datetime

from blinker._utilities import lazy_property
from sqlalchemy import Table

from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class DiagnosisStates(object):
    def __init__(self, moment):
        self.moment = moment

    def _diagnostic_sub_select(self):
        q = db.select()

    def get_client_state(self, client):
        q = Diagnosis.query.join(Diagnostic).filter(
            Diagnosis.client == client,
            Diagnosis.setDate <= self.moment,
            db.or_(
                Diagnosis.endDate.is_(None),
                Diagnosis.endDate > self.moment,
            ),
        )


class DiagnosisRole(object):
    def __init__(self, diagnosis):
        self.diagnosis = diagnosis


class DiagnosisEventRole(DiagnosisRole):
    def __init__(self, diagnosis, event):
        super(DiagnosisEventRole, self).__init__(diagnosis)
        self.event = event
        self._data_by_type = {}
        self._data_by_kind = {}
        self._data_by_tk = {}

    def select(self):
        diagnostic = self.diagnosis.get_diagnostic()
        for ed in Event_Diagnosis.query.filter(
            Event_Diagnosis.diagnosis == self.diagnosis,
            Event_Diagnosis.event == self.event,
        ):

            self._data_by_type[ed.diagnosisType.code] = None  # FIXME: Later


class Diagnosis(db.Model):
    __tablename__ = u'Diagnosis'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)

    client_id = db.Column(db.ForeignKey('Client.id'), index=True, nullable=False)
    person_id = db.Column(db.ForeignKey('Person.id'), index=True)
    setDate = db.Column(db.Date, default=datetime.date.today)
    endDate = db.Column(db.Date)

    client = db.relationship('Client')
    person = db.relationship('Person', foreign_keys=[person_id], lazy=False, innerjoin=True)
    modifyPerson = db.relationship('Person', foreign_keys=[modifyPerson_id])
    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])

    def get_diagnostic(self, date=None):
        from .actions import Action
        if date is None:
            date = datetime.datetime.now()
        return Diagnostic.query.outerjoin(Action).filter(
            Diagnostic.deleted == 0,
            Diagnostic.diagnosis == self,
            Action.begDate <= date,
        ).order_by(Diagnostic.createDatetime.desc()).first()

    @lazy_property
    def _diagnostic(self):
        return self.get_diagnostic()

    def get_state_for_event(self, event, date=None):
        """
        :type event: nemesis.models.event.Event
        :type date: datetime.datetime | NoneType
        :param event:
        :param date:
        :return:
        """
        if date is None:
            date = event.execDate
        diagnostics = Diagnostic.query.join(Diagnosis).filter(
            Diagnosis.client == event.client,
            Diagnostic.diagnosis == self,
        )
        if date is not None:
            diagnostics = diagnostics.filter(Diagnostic.setDate <= date)
        diagnostics = diagnostics.order_by(Diagnosis.setDate.desc())
        return diagnostics.first()

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'character': self.character
        }


class Diagnostic(db.Model):
    __tablename__ = u'Diagnostic'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)

    # Roots
    diagnosis_id = db.Column(db.ForeignKey('Diagnosis.id'), index=True)
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'), index=True)

    # Basic data
    MKB = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    MKB2 = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    MKBEx = db.Column(db.String(8), db.ForeignKey('MKB.DiagID'), index=True)
    notes = db.Column(db.Text, nullable=False, default='')
    diagnosis_description = db.Column(db.Text)
    setDate = db.Column(db.Date, default=datetime.date.today)
    endDate = db.Column(db.Date)

    # Extended data
    character_id = db.Column(db.ForeignKey('rbDiseaseCharacter.id'), index=True)
    stage_id = db.Column(db.ForeignKey('rbDiseaseStage.id'), index=True)
    phase_id = db.Column(db.ForeignKey('rbDiseasePhases.id'), index=True)
    traumaType_id = db.Column(db.ForeignKey('rbTraumaType.id'), index=True)
    rbAcheResult_id = db.Column(db.ForeignKey('rbAcheResult.id'), index=True)

    # Auxiliary data
    person_id = db.Column(db.ForeignKey('Person.id'), index=True)
    dispanser_id = db.Column(db.ForeignKey('rbDispanser.id'), index=True)
    healthGroup_id = db.Column(db.ForeignKey('rbHealthGroup.id'), nullable=False)
    sanatorium = db.Column(db.Integer, nullable=False, default=0)
    hospital = db.Column(db.Integer, nullable=False, default=0)
    version = db.Column(db.Integer, nullable=False, default=0)

    action = db.relationship('Action', backref='diagnostics')
    diagnosis = db.relationship('Diagnosis', backref='diagnostics')

    mkb = db.relationship('MKB', foreign_keys=[MKB])
    mkb2 = db.relationship('MKB', foreign_keys=[MKB2])
    mkb_ex = db.relationship('MKB', foreign_keys=[MKBEx])

    character = db.relationship('rbDiseaseCharacter', lazy=False)
    stage = db.relationship('rbDiseaseStage', lazy=False)
    phase = db.relationship('rbDiseasePhases', lazy=False)
    traumaType = db.relationship('rbTraumaType', lazy=False)
    rbAcheResult = db.relationship(u'rbAcheResult', lazy=False)

    person = db.relationship('Person', foreign_keys=[person_id])
    dispanser = db.relationship('rbDispanser')
    healthGroup = db.relationship('rbHealthGroup', lazy=False)
    modifyPerson = db.relationship('Person', foreign_keys=[modifyPerson_id])
    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])

    def __int__(self):
        return self.id

    @property
    def date(self):
        return self.action.begDate


class Event_Diagnosis(db.Model):
    __tablename__ = "Event_Diagnosis"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.ForeignKey('Event.id'), nullable=False)
    diagnosis_id = db.Column(db.ForeignKey('Diagnosis.id'), nullable=False)
    diagnosisType_id = db.Column(db.ForeignKey('rbDiagnosisTypeN.id'), nullable=False)
    diagnosisKind_id = db.Column(db.ForeignKey('rbDiagnosisKind.id'), nullable=False)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)

    event = db.relationship('Event', lazy=True, backref="diagnoses")
    diagnosis = db.relationship('Diagnosis')
    diagnosisType = db.relationship('rbDiagnosisTypeN', lazy=False)
    diagnosisKind = db.relationship('rbDiagnosisKind', lazy=False)


class Action_Diagnosis(db.Model):
    __tablename__ = "Action_Diagnosis"

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), nullable=False)
    diagnosis_id = db.Column(db.ForeignKey('Diagnosis.id'), nullable=False)
    diagnosisType_id = db.Column(db.ForeignKey('rbDiagnosisTypeN.id'), nullable=False)
    diagnosisKind_id = db.Column(db.ForeignKey('rbDiagnosisKind.id'), nullable=False)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)

    action = db.relationship('Action', lazy=True, backref="diagnoses")
    diagnosis = db.relationship('Diagnosis')
    diagnosisType = db.relationship('rbDiagnosisTypeN', lazy=False)
    diagnosisKind = db.relationship('rbDiagnosisKind', lazy=False)


class rbDiagnosisTypeN(db.Model):
    __tablename__ = "rbDiagnosisTypeN"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=False)
    requireResult = db.Column(db.Integer)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'require_result': self.requireResult
        }


class rbDiagnosisKind(db.Model):
    __tablename__ = "rbDiagnosisKind"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=False)

    def __unicode__(self):
        return self.name

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


EventType_rbDiagnosisType = Table(
    "EventType_DiagnosisType", db.metadata,
    db.Column('eventType_id', db.ForeignKey('EventType.id')),
    db.Column('diagnosisType_id', db.ForeignKey('rbDiagnosisTypeN.id')),
)


ActionType_rbDiagnosisType = Table(
    "ActionType_DiagnosisType", db.metadata,
    db.Column('actionType_id', db.ForeignKey('ActionType.id')),
    db.Column('diagnosisType_id', db.ForeignKey('rbDiagnosisTypeN.id')),
)


