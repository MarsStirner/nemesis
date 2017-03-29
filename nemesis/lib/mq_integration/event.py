# coding: utf-8
import logging

from nemesis.lib.enum import Enum
from nemesis.lib.apiutils import json_dumps
from nemesis.lib.data import get_action, get_action_list
from nemesis.lib.const import STATIONARY_RECEIVED_CODE, STATIONARY_ORG_STRUCT_STAY_CODE, \
    STATIONARY_MOVING_CODE, STATIONARY_LEAVED_CODE, STATIONARY_ORG_STRUCT_TRANSFER_CODE
from .base import MQIntegrationNotifier


logger = logging.getLogger('simple')


class MQOpsEvent(Enum):
    create = 1
    close = 2
    moving = 3


def notify_event_changed(op, event):
    notifier = None
    if event.is_stationary:
        if op == MQOpsEvent.create:
            notifier = HospEventCreateIntegrationNotifier()
        elif op == MQOpsEvent.close:
            notifier = HospEventCloseIntegrationNotifier()

    if notifier:
        try:
            notifier.notify(op, event)
        except Exception, e:
            logger.exception(e.message)


def notify_moving_changed(op, action):
    notifier = HospMovingIntegrationNotifier()
    if op == MQOpsEvent.moving:
        try:
            notifier.notify(op, action)
        except Exception, e:
            logger.exception(e.message)


class HospEventCreateIntegrationNotifier(MQIntegrationNotifier):

    msg_type = 'HospitalizationCreateMessage'
    bind_name = 'hosp'
    operations = MQOpsEvent

    def notify(self, operation, data):
        self.set_operation(operation)
        if not self._is_ready:
            return

        if operation == MQOpsEvent.create:
            self.send_hosp_create_message(data)

    def send_hosp_create_message(self, event):
        event_data = self._get_message_data(event)

        msg = json_dumps(event_data)
        logger.info(
            u'Отправка сообщения по созданию госпитализации с id={0}: {1}'.format(event.id, msg),
            extra=dict(tags=['HOSP_CREATE_INTGR'])
        )

        self.send(msg)

    def _get_message_data(self, event):
        received = get_action(event, STATIONARY_RECEIVED_CODE)
        return {
            'event': self._make_event(event),
            'received': self._make_received_action(received)
        }

    def _make_received_action(self, action):
        res = self._make_basic_action(action)
        if res is not None:
            res.update({
                'orgStructStay': self._make_org_struct(action.get_prop_value(STATIONARY_ORG_STRUCT_STAY_CODE)),
                'orgStructTransfer': self._make_org_struct(action.get_prop_value(STATIONARY_ORG_STRUCT_TRANSFER_CODE)),
            })
        return res


class HospMovingIntegrationNotifier(MQIntegrationNotifier):

    msg_type = 'HospitalizationMovingMessage'
    bind_name = 'hosp'
    operations = MQOpsEvent

    def notify(self, operation, data):
        self.set_operation(operation)
        if not self._is_ready:
            return

        if operation == MQOpsEvent.moving:
            self.send_hosp_moving_message(data)

    def send_hosp_moving_message(self, action):
        event_data = self._get_message_data(action)

        msg = json_dumps(event_data)
        logger.info(
            u'Отправка сообщения по движению пациента с id={0}: {1}'.format(action.id, msg),
            extra=dict(tags=['HOSP_MOVING_INTGR'])
        )

        self.send(msg)

    def _get_message_data(self, action):
        event = action.event
        return {
            'event': self._make_event(event),
            'moving': self._make_moving_action(action)
        }


class HospEventCloseIntegrationNotifier(MQIntegrationNotifier):

    msg_type = 'HospitalizationFinishMessage'
    bind_name = 'hosp'
    operations = MQOpsEvent

    def notify(self, operation, data):
        self.set_operation(operation)
        if not self._is_ready:
            return

        if operation == MQOpsEvent.close:
            self.send_hosp_close_message(data)

    def send_hosp_close_message(self, event):
        event_data = self._get_message_data(event)

        msg = json_dumps(event_data)
        logger.info(
            u'Отправка сообщения по закрытию госпитализации с id={0}: {1}'.format(event.id, msg),
            extra=dict(tags=['HOSP_CLOSE_INTGR'])
        )

        self.send(msg)

    def _get_message_data(self, event):
        leaved = get_action(event, STATIONARY_LEAVED_CODE)
        movings = get_action_list(event, STATIONARY_MOVING_CODE, all=True)
        return {
            'event': self._make_event(event),
            'leaved': self._make_leaved_action(leaved),  # not used?
            'movings': [
                self._make_moving_action(ma)
                for ma in movings
            ]
        }

    def _make_leaved_action(self, action):
        res = self._make_basic_action(action)
        if res is not None:
            res.update({
                'hospOutcome': self._make_org_struct(action.get_prop_value('hospOutcome'))  # not used?
            })
        return res
