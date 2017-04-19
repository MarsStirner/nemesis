# coding: utf-8
from nemesis.models.event import Event, EventType
from nemesis.models.exists import rbRequestType
from nemesis.lib.const import STATIONARY_EVENT_CODES


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

