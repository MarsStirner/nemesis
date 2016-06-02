# -*- coding: utf-8 -*-
from nemesis.models.enums import MedicationPrescriptionStatus
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


class MedicalPrescription(db.Model):
    __tablename__ = 'MedicalPrescription'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP"))
    modifyDatetime = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    createPerson_id = db.Column(db.ForeignKey(u'Person.id'), nullable=False, index=True)
    modifyPerson_id = db.Column(db.ForeignKey(u'Person.id'), nullable=False, index=True)
    action_id = db.Column(db.ForeignKey(u'Action.id'), nullable=False, index=True)
    rls_id = db.Column(db.ForeignKey(u'rlsNomen.id'), nullable=False, index=True)
    status_id = db.Column(db.Integer, nullable=False)
    dose_amount = db.Column(db.Float(asdecimal=True), nullable=False)
    dose_unit_id = db.Column(db.ForeignKey(u'rbUnits.id'), nullable=False, index=True)
    frequency_value = db.Column(db.Float(asdecimal=True), nullable=False)
    frequency_unit_id = db.Column(db.ForeignKey(u'rbUnits.id'), nullable=False, index=True)
    duration_value = db.Column(db.Integer, nullable=False)
    duration_unit_id = db.Column(db.ForeignKey(u'rbUnits.id'), nullable=False, index=True)
    begDate = db.Column(db.Date)
    methodOfAdministration_id = db.Column(db.ForeignKey(u'rbMethodOfAdministration.id'), nullable=False, index=True)
    reasonOfCancel = db.Column(db.String(256))
    note = db.Column(db.String(256))

    createPerson = db.relationship(u'Person', primaryjoin='MedicalPrescription.createPerson_id == Person.id')
    modifyPerson = db.relationship(u'Person', primaryjoin='MedicalPrescription.modifyPerson_id == Person.id')

    action = db.relationship(u'Action', backref='medication_prescriptions')
    rls = db.relationship(u'rlsNomen', lazy='joined')
    dose_unit = db.relationship(u'rbUnits', primaryjoin='MedicalPrescription.dose_unit_id == rbUnits.id', lazy='joined')
    duration_unit = db.relationship(u'rbUnits', primaryjoin='MedicalPrescription.duration_unit_id == rbUnits.id', lazy='joined')
    frequency_unit = db.relationship(u'rbUnits', primaryjoin='MedicalPrescription.frequency_unit_id == rbUnits.id', lazy='joined')
    methodOfAdministration = db.relationship(u'rbMethodOfAdministration', lazy='joined')

    @property
    def status(self):
        return MedicationPrescriptionStatus(self.status_id)

    @status.setter
    def status(self, value):
        self.status_id = int(value)

    def __json__(self):
        return {
            'id': self.id,
            'rls': self.rls,
            'method': self.methodOfAdministration,
            'note': self.note,
            'reason': self.reasonOfCancel,
            'status': self.status,
            'dose': {
                'value': self.dose_amount,
                'unit': self.dose_unit,
            },
            'frequency': {
                'value': self.frequency_value,
                'unit': self.frequency_unit,
            },
            'duration': {
                'value': self.duration_value,
                'unit': self.duration_unit,
            },
            'related': {
                'action_person_id': self.action.person_id,
                'action_set_person_id': self.action.setPerson_id,
                'event_exec_person_id': self.action.event.execPerson_id,
            },
            'closed': self.action.status >= 2 or self.status_id >= 3,
            'create_person': self.createPerson,
            'modify_person': self.modifyPerson,
            'create_datetime': self.createDatetime,
            'modify_datetime': self.modifyDatetime,
            'action_id': self.action_id,
        }

    def set_json(self, data):
        with db.session.no_autoflush:
            from nemesis.lib.utils import safe_traverse
            from nemesis.models.refbooks import rbUnits
            from nemesis.models.exists import rbMethodOfAdministration
            from nemesis.models.rls import rlsNomen

            if 'rls' in data:
                self.rls = rlsNomen.query.get(safe_traverse(data, 'rls', 'id'))
            if 'method' in data:
                self.methodOfAdministration = rbMethodOfAdministration.query.get(safe_traverse(data, 'method', 'id'))
            if 'note' in data:
                self.note = data['note'] or None
            if 'dose' in data:
                self.dose_amount = safe_traverse(data, 'dose', 'value')
                self.dose_unit = rbUnits.query.get(safe_traverse(data, 'dose', 'unit', 'id'))
            if 'frequency' in data:
                self.frequency_value = safe_traverse(data, 'frequency', 'value')
                self.frequency_unit = rbUnits.query.get(safe_traverse(data, 'frequency', 'unit', 'id'))
            if 'duration' in data:
                self.duration_value = safe_traverse(data, 'duration', 'value')
                self.duration_unit = rbUnits.query.get(safe_traverse(data, 'duration', 'unit', 'id'))
            if 'reason' in data:
                self.reasonOfCancel = data['reason'] or None
            if 'status' in data:
                self.status_id = safe_traverse(data, 'status', 'id')
