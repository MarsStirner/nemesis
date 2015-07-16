# -*- coding: utf-8 -*-

__author__ = 'viruzzz-kun'


def notify_user(person_id, subject, text, folder='system'):
    import requests
    from nemesis.app import app
    from nemesis.models.utils import safe_current_user_id

    mail = {
        'sender': safe_current_user_id(),
        'recipient': person_id,
        'topic': 'mail:new',
        'ctrl': True,
        'i': True,
        's': False,
        'data': {
            'subject': subject,
            'text': text,
            'folder': folder,
        }
    }
    requests.post(app.config['SIMARGL_URL'].rstrip('/') + '/simargl-rpc', json=mail)
