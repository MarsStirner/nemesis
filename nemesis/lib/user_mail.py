# -*- coding: utf-8 -*-
import requests
import logging


logger = logging.getLogger('simple')


def send_usermail(recipient_id, subject, text, sender_id=None, parent_id=None):
    from nemesis.app import app
    from nemesis.models.utils import safe_current_user_id

    if subject is None:
        subject = u'Без темы'

    logger.info(u'Отправка внутренней почты: {0}'.format(recipient_id, subject, text, sender_id, parent_id))
    requests.post(app.config['SIMARGL_URL'].rstrip('/') + '/simargl-rpc', json={
        'topic': 'mail:new',
        'recipient': recipient_id,
        'sender': sender_id,
        'data': {
            'subject': subject,
            'text': text,
            'parent_id': parent_id
        },
        'ctrl': True
    })
