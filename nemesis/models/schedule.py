# -*- coding: utf-8 -*-

import datetime

from nemesis.models.client import Client
from nemesis.systemwide import db
from exists import Person, rbReasonOfAbsence, Organisation
from nemesis.models.utils import safe_current_user_id


class rbReceptionType(db.Model):
    __tablename__ = 'rbReceptionType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbAttendanceType(db.Model):
    __tablename__ = 'rbAttendanceType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbAppointmentType(db.Model):
    __tablename__ = 'rbAppointmentType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __unicode__(self):
        return u'(%s) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbTimeQuotingType(db.Model):
    __tablename__ = u'rbTimeQuotingType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, nullable=False, unique=True)
    name = db.Column(db.Text(collation=u'utf8_unicode_ci'), nullable=False)

    def __unicode__(self):
        return u'(%d) %s' % (self.code, self.name)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class Office(db.Model):
    __tablename__ = 'Office'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    orgStructure_id = db.Column(db.ForeignKey('OrgStructure.id'))

    orgStructure = db.relationship('OrgStructure')

    def __unicode__(self):
        return self.code

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'org_structure': self.orgStructure
        }


class Schedule(db.Model):
    __tablename__ = 'Schedule'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'))
    date = db.Column(db.Date, nullable=False)
    begTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    numTickets = db.Column(db.Integer, doc=u'Запланированное количество талонов на данный день')
    office_id = db.Column(db.ForeignKey('Office.id'))
    reasonOfAbsence_id = db.Column(db.Integer, db.ForeignKey('rbReasonOfAbsence.id'))
    receptionType_id = db.Column(db.Integer, db.ForeignKey('rbReceptionType.id'))
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0', default=0)

    person = db.relationship('Person', foreign_keys=person_id)
    reasonOfAbsence = db.relationship('rbReasonOfAbsence', lazy='joined')
    receptionType = db.relationship('rbReceptionType', lazy='joined')
    tickets = db.relationship(
        'ScheduleTicket', lazy=False, primaryjoin=
        "and_(ScheduleTicket.schedule_id == Schedule.id, ScheduleTicket.deleted == 0)",
        backref=db.backref('schedule'),
        order_by='ScheduleTicket.begTime'
    )
    office = db.relationship('Office', lazy='joined')


class ScheduleTicket(db.Model):
    __tablename__ = 'ScheduleTicket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('Schedule.id'), nullable=False)
    begTime = db.Column(db.Time)
    endTime = db.Column(db.Time)
    attendanceType_id = db.Column(db.Integer, db.ForeignKey('rbAttendanceType.id'), nullable=False)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0', default=0)

    attendanceType = db.relationship('rbAttendanceType', lazy=False)
    client_ticket = db.relationship(
        'ScheduleClientTicket', lazy=False, primaryjoin=
        "and_(ScheduleClientTicket.ticket_id == ScheduleTicket.id, ScheduleClientTicket.deleted == 0)",
        uselist=False)

    # schedule = db.relationship(
    #     'Schedule', lazy=True, innerjoin=True, uselist=False,
    #     primaryjoin='and_('
    #                 'Schedule.deleted == 0, ScheduleTicket.deleted == 0, ScheduleTicket.schedule_id == Schedule.id)'
    # )

    @property
    def client(self):
        ct = self.client_ticket
        return ct.client if ct else None

    @property
    def begDateTime(self):
        return datetime.datetime.combine(self.schedule.date, self.begTime) if self.begTime is not None else None

    @property
    def endDateTime(self):
        return datetime.datetime.combine(self.schedule.date, self.endTime) if self.endTime is not None else None


class ScheduleClientTicket(db.Model):
    __tablename__ = 'ScheduleClientTicket'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ScheduleTicket.id'), nullable=False)
    isUrgent = db.Column(db.Boolean)
    note = db.Column(db.Unicode(256), default=u'')
    appointmentType_id = db.Column(db.Integer, db.ForeignKey('rbAppointmentType.id'))
    infisFrom = db.Column(db.Unicode(20))
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0', default=0)
    event_id = db.Column(db.ForeignKey('Event.id'))
    
    client = db.relationship('Client', lazy='joined', uselist=False)
    appointmentType = db.relationship('rbAppointmentType', lazy=False, innerjoin=True)
    createPerson = db.relationship('Person', foreign_keys=[createPerson_id])
    event = db.relationship('Event')

    ticket = db.relationship(
        'ScheduleTicket', lazy=True, innerjoin=True, uselist=False,
        primaryjoin='and_('
                    'ScheduleClientTicket.deleted == 0, '
                    'ScheduleTicket.deleted == 0, '
                    'ScheduleClientTicket.ticket_id == ScheduleTicket.id)'
    )

    @property
    def org_from(self):
        if not self.infisFrom:
            return
        from .exists import Organisation
        org = Organisation.query.filter(Organisation.infisCode == self.infisFrom).first()
        if not org:
            return self.infisFrom
        return org.title


class QuotingByTime(db.Model):
    __tablename__ = u'QuotingByTime'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer)
    quoting_date = db.Column(db.Date, nullable=False)
    QuotingTimeStart = db.Column(db.Time, nullable=False)
    QuotingTimeEnd = db.Column(db.Time, nullable=False)
    quotingType_id = db.Column("QuotingType", db.Integer, db.ForeignKey('rbTimeQuotingType.code'))

    quotingType = db.relationship('rbTimeQuotingType', lazy='joined')