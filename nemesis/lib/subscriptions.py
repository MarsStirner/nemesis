# -*- coding: utf-8 -*-
import requests

__author__ = 'viruzzz-kun'


def int_subscribe_user(person_id, object_id, subscribe):
    from nemesis.app import app
    from nemesis.models.utils import safe_current_user_id

    requests.post(app.config['SIMARGL_URL'].rstrip('/') + '/simargl-rpc', json={
        'topic': 'subscription:%s' % ('add' if subscribe else 'del'),
        'sender': safe_current_user_id(),
        'ctrl': True,
        'data': {
            'object_id': object_id,
            'person_id': person_id,
        }
    })


def subscribe_user(person_id, object_id):
    return int_subscribe_user(person_id, object_id, True)


def unsubscribe_user(person_id, object_id):
    return int_subscribe_user(person_id, object_id, False)


def notify_object(object_id, reasons, kwargs, default=None):
    from nemesis.app import app
    from nemesis.models.utils import safe_current_user_id

    requests.post(app.config['SIMARGL_URL'].rstrip('/') + '/simargl-rpc', json={
        'sender': safe_current_user_id(),
        'topic': 'subscription:notify',
        'ctrl': True,
        'data': {
            'kwargs': kwargs,
            'object_id': object_id,
            'reasons': reasons,
            'default_reason': default,
        },
    })
