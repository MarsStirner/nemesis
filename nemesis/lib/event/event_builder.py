# -*- coding: utf-8 -*-
import datetime

from flask_login import current_user

from nemesis.lib.const import STATIONARY_EVENT_CODES, STATIONARY_RECEIVED_CODE
from nemesis.lib.data import create_action, get_action
from nemesis.models.actions import ActionType
from nemesis.models.client import Client
from nemesis.models.enums import EventPrimary, EventOrder
from nemesis.models.event import (Event, EventType)
from nemesis.models.exists import Person, rbRequestType
from nemesis.models.schedule import ScheduleClientTicket
from nemesis.lib.data_ctrl.utils import get_default_org
from nemesis.systemwide import db


class EventBuilder(object):
    def __init__(self, client_id, ticket_id):
        self.event = Event()
        self.client_id = client_id
        self.ticket_id = ticket_id

    def return_event(self):
        return self.event

    def create_base_info(self):
        self.event.organisation = get_default_org()
        if self.ticket_id:
            self.set_info_from_ticket()
        elif self.client_id:
            self.without_ticket()
        self.event.execPerson = Person.query.get(self.event.exec_person_id)
        self.event.orgStructure = self.event.execPerson.org_structure
        self.event.client = Client.query.get(self.client_id)
        self.set_additional_properties()
        self.set_default_event_type()

    def set_default_event_type(self, request_type_kind):
        # Тип события (обращения по умолчанию)
        pass

    def set_info_from_ticket(self):
        ticket = ScheduleClientTicket.query.get(int(self.ticket_id))
        self.event.client_id = ticket.client_id
        self.event.setDate = ticket.get_date_for_new_event()
        self.event.exec_person_id = ticket.ticket.schedule.person_id  # что в диагностике,
        self.event.note = ticket.note

    def without_ticket(self):
        self.event.setDate = datetime.datetime.now()
        self.event.exec_person_id = current_user.get_main_user().id
        self.event.note = ''

    def get_prev_event(self, event_codes):
        return Event.query.join(EventType, rbRequestType).filter(
            Event.client_id == self.client_id,
            Event.deleted == 0,
            rbRequestType.code.in_(event_codes),
            Event.execDate.is_(None)
        ).order_by(Event.setDate.desc()).first()

    def set_additional_properties(self):
        pass

    def create_contract(self):
        pass

    def create_received(self):
        """
        Создание поступления
        """
        pass


class PoliclinicEventBuilder(EventBuilder):

    def set_default_event_type(self):
        self.event.eventType = EventType.query.filter_by(code='02').first()


class StationaryEventBuilder(EventBuilder):

    def set_default_event_type(self):
        self.event.eventType = EventType.query.filter_by(code='03').first()

    def set_additional_properties(self):
        self.event.isPrimaryCode = EventPrimary.primary[0]
        self.event.order = EventOrder.planned[0]

    def create_received(self):
        prev_event = self.get_prev_event(STATIONARY_EVENT_CODES)
        prev_received = get_action(prev_event, STATIONARY_RECEIVED_CODE)
        action_type = ActionType.query.filter(ActionType.flatCode == STATIONARY_RECEIVED_CODE).first()
        self.event.received = create_action(action_type.id, self.event)
        if self.event.received and prev_received:
            self.event.received.propsByCode['weight'].value = prev_received.propsByCode['weight'].value
            self.event.received.propsByCode['height'].value = prev_received.propsByCode['height'].value


class EventConstructionDirector(object):

    def set_builder(self, builder):
        self.builder = builder

    def construct(self):
        self.builder.create_base_info()
        self.builder.create_received()
        return self.builder.return_event()