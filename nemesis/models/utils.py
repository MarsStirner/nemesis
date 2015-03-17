# -*- coding: utf-8 -*-

from flask.ext.login import current_user


def safe_current_user_id():
    return current_user.get_id() if current_user else None


def get_model_by_name(name):
    from nemesis.models import exists, schedule, actions, client, event
    for mod in (exists, schedule, actions, client, event):
        if hasattr(mod, name):
            return getattr(mod, name)
    return None