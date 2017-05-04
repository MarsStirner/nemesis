# coding: utf-8
from flask import url_for
from sqlalchemy import and_, or_, func

from nemesis.lib.html_utils import UIException
from nemesis.lib.utils import bail_out
from nemesis.models.actions import ActionType, Action
from nemesis.models.client import Client
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.lib.const import STATIONARY_EVENT_CODES, STATIONARY_MOVING_CODE, STATIONARY_LEAVED_CODE
from nemesis.systemwide import db


def get_client_events(client, **flt):
    events = client.events
    if flt.get('stationary', False):
        events = events.join(EventType, rbRequestType).filter(
            rbRequestType.code.in_(STATIONARY_EVENT_CODES)
        )
    events = events.order_by(Event.setDate.desc())
    return events.all()


def get_current_hospitalisation(client_id, one=True):
    events = Event.query.join(EventType, rbRequestType).filter(
        Event.client_id == client_id,
        Event.execDate.is_(None),
        Event.deleted == 0,
        rbRequestType.code.in_(STATIONARY_EVENT_CODES)
    ).order_by(Event.setDate.desc())
    return events.first() if one else events.all()


def get_opened_events_data(client_id):
    # Event.id > 20000000 чтобы не проверять евенты импортированные из старых баз (TMIS-1459)
    base_query = db.session.query(Event).join(Client, EventType, rbRequestType)\
        .filter(Event.id > 20000000, Event.deleted == 0, Client.id == client_id,
                rbRequestType.code.in_(STATIONARY_EVENT_CODES))

    q_action_begdates = db.session.query(Action).join(
        Event, EventType, rbRequestType, ActionType,
    ).filter(
        Event.deleted == 0, Action.deleted == 0, rbRequestType.code.in_(STATIONARY_EVENT_CODES),
        ActionType.flatCode == STATIONARY_MOVING_CODE, Event.client_id == client_id
    ).with_entities(
        func.max(Action.begDate).label('max_beg_date'), Event.id.label('event_id')
    ).group_by(
        Event.id
    ).subquery('MaxActionBegDates')

    q_latest_movings_ids = db.session.query(Action).join(
        q_action_begdates, and_(q_action_begdates.c.max_beg_date == Action.begDate,
                                q_action_begdates.c.event_id == Action.event_id)
    ).group_by(
        Action.event_id
    ).with_entities(
        func.max(Action.id).label('action_id'), Action.event_id.label('event_id')
    ).subquery('LatestMovingsIds')

    q_closed_latest_movings = db.session.query(Action).join(
        q_latest_movings_ids, Action.id == q_latest_movings_ids.c.action_id
    ).filter(
        Action.endDate.isnot(None)
    ).subquery('LatestMovings')

    q_leaved_ids = db.session.query(Action).join(
        Event, EventType, rbRequestType, ActionType,
    ).filter(
        Event.deleted == 0, Action.deleted == 0, rbRequestType.code.in_(STATIONARY_EVENT_CODES),
        ActionType.flatCode == STATIONARY_LEAVED_CODE, Event.client_id == client_id
    ).group_by(
        Event.id
    ).with_entities(
        Action.event_id.label('event_id')
    ).subquery('LeavedActions')

    data = base_query.outerjoin(
        q_closed_latest_movings, q_closed_latest_movings.c.event_id == Event.id
    ).outerjoin(
        q_leaved_ids, q_leaved_ids.c.event_id == Event.id
    ).filter(
        or_(
            q_leaved_ids.c.event_id.is_(None),
            q_closed_latest_movings.c.event_id.is_(None)
        )
    ).with_entities(
        Event.id, Event.externalId, Event.setDate
    ).all()

    return data


def check_stationary_permissions(client_id):
    opened_events = []
    for event_id, external_id, set_date in get_opened_events_data(client_id):
        opened_events.append({
            'text': u'№{0} от {1}'.format(external_id, set_date),
            'href': url_for('event.html_event_info', event_id=event_id)
        })
    if opened_events:
        bail_out(UIException(403, u'Невозможно госпитализирвать пациента. Закройте истории болезни:',
                             href_data=opened_events))
