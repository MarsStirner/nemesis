# coding: utf-8
import logging

from nemesis.lib.enum import Enum
from nemesis.lib.apiutils import json_dumps
from nemesis.models.enums import MedicationPrescriptionStatus
from .base import MQIntegrationNotifier


logger = logging.getLogger('simple')


class MQOpsMedPrescription(Enum):
    create = 1
    close = 2


def notify_action_prescriptions_changed(op, action):
    notifier = MedPrescriptionIntegrationNotifier()
    try:
        notifier.notify(op, action)
    except Exception, e:
        logger.exception(e.message)


class MedPrescriptionIntegrationNotifier(MQIntegrationNotifier):

    msg_type = 'PrescriptionListMessage'
    bind_name = 'med_prescription'
    operations = MQOpsMedPrescription

    def notify(self, operation, data):
        self.set_operation(operation)
        if not self._is_ready:
            return

        if operation == MQOpsMedPrescription.create:
            self.send_mp_create_message(data)
        elif operation == MQOpsMedPrescription.close:
            self.send_mp_close_message(data)

    def send_mp_create_message(self, action):
        event_data = self._get_message_data(action)

        msg = json_dumps(event_data)
        logger.info(
            u'Отправка сообщения по созданию назначений для экшена с id={0}: {1}'.format(action.id, msg),
            extra=dict(tags=['MED_PRESCR_INTGR'])
        )

        self.send(msg)

    def send_mp_close_message(self, action):
        event_data = self._get_message_data(action)

        msg = json_dumps(event_data)
        logger.info(
            u'Отправка сообщения по закрытию назначений для экшена с id={0}: {1}'.format(action.id, msg),
            extra=dict(tags=['MED_PRESCR_INTGR'])
        )

        self.send(msg)

    def _get_message_data(self, action):
        event = action.event
        return {
            'event': self._make_event(event),
            'prescription': self._make_prescription_action(action)
        }

    def _make_prescription_action(self, action):
        res = self._make_basic_action(action)
        if res is not None:
            res.update({
                'prescriptions': [
                    self._make_prescription(p)
                    for p in action.medication_prescriptions
                ]
            })
        return res

    def _make_prescription(self, prescription):
        return {
            'id': prescription.id,
            'rls': self._make_rls_nomen(prescription.rls),
            'status': self._make_med_prescr_status(prescription.status_id),
            'dose': self._make_value_and_unit(prescription.dose_amount, prescription.dose_unit),
            'frequency': self._make_value_and_unit(prescription.frequency_value, prescription.frequency_unit),
            'duration': self._make_value_and_unit(prescription.duration_value, prescription.duration_unit),
            'begDate': prescription.begDate,
            'note': prescription.note,
            'reasonOfCancel': prescription.reasonOfCancel
        }

    def _make_rls_nomen(self, nomen):
        return {
            'id': nomen.id,
            'actMatters': self._make_rb_rls_act_matters(nomen.actMatters),
            'tradeName': self._make_rb_rls_trade_name(nomen.tradeName),
            'form': self._make_rb_rls_form(nomen.form),
            'packaging': self._make_rb_rls_packaging(nomen.packing),
            'filling': self._make_rb_rls_filling(nomen.filling),
            'unit': self._make_rb_units(nomen.unit),
            'dose': self._make_value_and_unit(nomen.dosageValue, nomen.dosageUnit),
            'drugLifeTime': nomen.drugLifetime
        }

    def _make_rb_rls_act_matters(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'name': rb.name,
            'localName': rb.localName
        }

    def _make_rb_rls_trade_name(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'name': rb.name,
            'localName': rb.localName
        }

    def _make_rb_rls_form(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'name': rb.name
        }

    def _make_rb_rls_packaging(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'name': rb.name
        }

    def _make_rb_rls_filling(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'name': rb.name
        }

    def _make_med_prescr_status(self, status_code):
        # TODO:
        g = MedicationPrescriptionStatus(status_code)
        if g.value == MedicationPrescriptionStatus.active[0]:
            return 'STARTED'
        else:
            return 'STARTED'
