# -*- coding: utf-8 -*-

import datetime

from nemesis.models.utils import safe_current_user_id, UUIDColumn
from nemesis.models.enums import MeasureStatus
from nemesis.systemwide import db


class ExpertProtocol(db.Model):
    __tablename__ = u'ExpertProtocol'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True)
    name = db.Column(db.Unicode(255), nullable=False)
    deleted = db.Column(db.Integer, nullable=False, server_default="'0'")

    schemes = db.relationship('ExpertScheme', backref='protocol')


class ExpertScheme(db.Model):
    __tablename__ = u'ExpertScheme'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    name = db.Column(db.Unicode(255), nullable=False)
    code = db.Column(db.Unicode(16), index=True)
    number = db.Column(db.Unicode(16), nullable=False, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default="'0'")
    protocol_id = db.Column(db.Integer, db.ForeignKey('ExpertProtocol.id'), nullable=False, index=True)

    mkbs = db.relationship('MKB', secondary='ExpertSchemeMKB')
    scheme_measures = db.relationship('ExpertSchemeMeasureAssoc', backref='scheme')


class ExpertSchemeMKBAssoc(db.Model):
    __tablename__ = u'ExpertSchemeMKB'

    id = db.Column(db.Integer, primary_key=True)
    mkb_id = db.Column(db.Integer, db.ForeignKey('MKB.id'), nullable=False, index=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey('ExpertScheme.id'), nullable=False, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default="'0'")


class ExpertSchemeMeasureAssoc(db.Model):
    __tablename__ = u'ExpertSchemeMeasure'

    id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey('ExpertScheme.id'), nullable=False, index=True)
    measure_id = db.Column(db.Integer, db.ForeignKey('Measure.id'), nullable=False, index=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('MeasureSchedule.id'), index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default="'0'")

    measure = db.relationship('Measure')
    schedule = db.relationship('MeasureSchedule', backref='scheme_measure', cascade_backrefs=False, uselist=False)


class Measure(db.Model):
    __tablename__ = u'Measure'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    measureType_id = db.Column(db.Integer, db.ForeignKey('rbMeasureType.id'), nullable=False, index=True)
    code = db.Column(db.Unicode(16), index=True)
    name = db.Column(db.Unicode(512), nullable=False)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    uuid = db.Column(UUIDColumn(), nullable=False)
    actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), index=True)
    templateAction_id = db.Column(db.Integer, db.ForeignKey('Action.id'), index=True)

    measure_type = db.relationship('rbMeasureType')
    action_type = db.relationship('ActionType')
    template_action = db.relationship('Action')


class MeasureSchedule_ScheduleTypeAssoc(db.Model):
    __tablename__ = u'MeasureSchedule_ScheduleType'

    id = db.Column(db.Integer, primary_key=True)
    measureSchedule_id = db.Column(db.Integer, db.ForeignKey('MeasureSchedule.id'), nullable=False)
    scheduleType_id = db.Column(db.Integer, db.ForeignKey('rbMeasureScheduleType.id'), nullable=False, index=True)


class MeasureScheduleAdditionalMKBAssoc(db.Model):
    __tablename__ = u'MeasureScheduleAdditionalMKB'

    id = db.Column(db.Integer, primary_key=True)
    measureSchedule_id = db.Column(db.Integer, db.ForeignKey('MeasureSchedule.id'), nullable=False, index=True)
    mkb_id = db.Column(db.Integer, db.ForeignKey('MKB.id'), nullable=False)


class rbMeasureType(db.Model):
    __tablename__ = u'rbMeasureType'
    _table_description = u'Типы мероприятий'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class rbMeasureScheduleApplyType(db.Model):
    __tablename__ = u'rbMeasureScheduleApplyType'
    _table_description = u'Типы мероприятий'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class MeasureSchedule(db.Model):
    __tablename__ = u'MeasureSchedule'

    id = db.Column(db.Integer, primary_key=True)
    additionalText = db.Column(db.Text)
    applyType_id = db.Column(db.Integer, db.ForeignKey('rbMeasureScheduleApplyType.id'))
    applyBoundRangeLow = db.Column(db.Integer)
    applyBoundRangeLowUnits_id = db.Column(db.Integer, db.ForeignKey('rbUnits.id'))
    applyBoundRangeLowMax = db.Column(db.Integer)
    applyBoundRangeLowMaxUnits_id = db.Column(db.Integer, db.ForeignKey('rbUnits.id'))
    applyBoundRangeHigh = db.Column(db.Integer)
    applyBoundRangeHighUnits_id = db.Column(db.Integer, db.ForeignKey('rbUnits.id'))
    period = db.Column(db.Integer)
    periodUnits_id = db.Column(db.Integer, db.ForeignKey('rbUnits.id'))
    frequency = db.Column(db.Integer)
    count = db.Column(db.Integer)

    apply_type = db.relationship('rbMeasureScheduleApplyType')
    apply_bound_range_low_unit = db.relationship('rbUnits', foreign_keys=[applyBoundRangeLowUnits_id])
    apply_bound_range_low_max_unit = db.relationship('rbUnits', foreign_keys=[applyBoundRangeLowMaxUnits_id])
    apply_bound_range_high_unit = db.relationship('rbUnits', foreign_keys=[applyBoundRangeHighUnits_id])
    period_unit = db.relationship('rbUnits', foreign_keys=[periodUnits_id])
    schedule_types = db.relationship('rbMeasureScheduleType', secondary='MeasureSchedule_ScheduleType')
    additional_mkbs = db.relationship('MKB', secondary='MeasureScheduleAdditionalMKB')


class rbMeasureScheduleType(db.Model):
    __tablename__ = u'rbMeasureScheduleType'
    _table_description = u'Типы расписаний мероприятий'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class rbMeasureStatus(db.Model):
    __tablename__ = u'rbMeasureStatus'
    _table_description = u'Типы статусов мероприятий'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(32), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class EventMeasure(db.Model):
    __tablename__ = u'EventMeasure'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), nullable=False, index=True)
    schemeMeasure_id = db.Column(db.Integer, db.ForeignKey('ExpertSchemeMeasure.id'), nullable=False, index=True)
    begDateTime = db.Column(db.DateTime)
    endDateTime = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'", default=0)
    sourceAction_id = db.Column(db.Integer, db.ForeignKey('Action.id'), index=True)
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'), index=True)
    is_actual = db.Column(db.Integer, server_default="'1'")

    event = db.relationship('Event')
    scheme_measure = db.relationship('ExpertSchemeMeasureAssoc')
    source_action = db.relationship('Action', foreign_keys=[sourceAction_id])
    action = db.relationship('Action', foreign_keys=[action_id])
    create_person = db.relationship('Person', foreign_keys=[createPerson_id])
    modify_person = db.relationship('Person', foreign_keys=[modifyPerson_id])