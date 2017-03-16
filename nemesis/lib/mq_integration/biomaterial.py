# coding: utf-8
import logging

from nemesis.lib.enum import Enum
from nemesis.lib.apiutils import json_dumps
from nemesis.models.enums import TTJStatus
from nemesis.models.actions import TakenTissueJournal
from nemesis.lib.utils import safe_double
from .base import MQIntegrationNotifier


logger = logging.getLogger('simple')


class MQOpsBiomaterial(Enum):
    send = 1


def notify_biomaterials_changed(op, ttj_ids):
    ttj_list = TakenTissueJournal.query.filter(TakenTissueJournal.id.in_(ttj_ids)).all()
    notifier = BiomaterialIntegrationNotifier()
    for ttj in ttj_list:
        try:
            notifier.notify(op, ttj)
        except Exception, e:
            logger.exception(e.message)


class BiomaterialIntegrationNotifier(MQIntegrationNotifier):

    msg_type = 'BiologicalMaterialMessage'
    bind_name = 'biomaterial'
    operations = MQOpsBiomaterial

    def notify(self, operation, data):
        self.set_operation(operation)
        if not self._is_ready:
            return

        if operation == MQOpsBiomaterial.send:
            self.send_biom_send_message(data)

    def send_biom_send_message(self, ttj):
        event_data = self._get_message_data(ttj)

        msg = json_dumps(event_data)
        logger.info(
            u'Отправка сообщения отправке биозабора с id={0}: {1}'.format(ttj.id, msg),
            extra=dict(tags=['BIOM_INTGR'])
        )

        self.send(msg)

    def _get_message_data(self, ttj):
        return {
            'biomaterial': self._make_biomaterial(ttj),
            'research': [self._make_analysis_action(action)
                         for action in ttj.actions]
        }

    def _make_biomaterial(self, ttj):
        class DefaultUnit(object):
            id = 0
            code = u'Шт'
            name = u'Шт'

        return {
            'id': ttj.id,
            'event': self._make_event(ttj.event),
            'biomaterialType': self._make_rb_tissue_type(ttj.tissueType),
            'testTubeType': self._make_rb_testtube_type(ttj.testTubeType),
            'amount': self._make_value_and_unit(ttj.amount or 1, ttj.unit or DefaultUnit()),
            'datetimePlanned': ttj.datetimePlanned,
            'datetimeTaken': ttj.datetimeTaken,
            'status': self._make_ttj_status(ttj.statusCode),
            'barcode': {
                'period': ttj.period,
                'code': ttj.barcode
            },
            'note': ttj.note,
            'person': self._make_person(ttj.execPerson)
        }

    def _make_analysis_action(self, action):
        res = self._make_basic_action(action)
        if res is not None:
            res.update({
                'type': self._make_action_type(action.actionType),
                'isUrgent': action.isUrgent,
                'assigner': self._make_person(action.person),
                'tests': [self._make_lab_test(prop) for prop in action.properties if prop.isAssigned],
            })
        return res

    def _make_lab_test(self, prop):
        return {
            'id': prop.id,
            'test': self._make_rb(prop.type.test),
        }

    def _make_rb_tissue_type(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'code': rb.code,
            'name': rb.name,
            'sex': self._make_gender(rb.sexCode)
        }

    def _make_rb_testtube_type(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'code': rb.code,
            'name': rb.name,
            'volume': self._make_value_and_unit(rb.volume, rb.unit),
            'color': rb.color
        }

    def _make_ttj_status(self, status_code):
        g = TTJStatus(status_code)
        if g.value == TTJStatus.waiting[0]:
            return 'WAIT'
        elif g.value == TTJStatus.in_progress[0]:
            return 'IN_PROGRESS'
        elif g.value == TTJStatus.finished[0]:
            return 'FINISH'
        elif g.value == TTJStatus.sent_to_lab[0]:
            return 'SENT'
        elif g.value == TTJStatus.fail_to_lab[0]:
            return 'FAILED'
        else:
            return 'FINISH'
