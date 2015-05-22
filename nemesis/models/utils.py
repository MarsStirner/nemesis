# -*- coding: utf-8 -*-
import uuid
from sqlalchemy import types
from flask.ext.login import current_user


def safe_current_user_id():
    return int(current_user.get_id()) if current_user else None


def get_model_by_name(name):
    from nemesis.models import exists, schedule, actions, client, event
    for mod in (exists, schedule, actions, client, event):
        if hasattr(mod, name):
            return getattr(mod, name)
    return None


class UUIDColumn(types.TypeDecorator):
    impl = types.Binary

    def __init__(self):
        self.impl.length = 16
        types.TypeDecorator.__init__(self, length=self.impl.length)

    def process_bind_param(self, value, dialect=None):
        if value and isinstance(value, uuid.UUID):
            return value.bytes
        elif value and isinstance(value, basestring):
            return uuid.UUID(value).bytes
        elif value:
            raise ValueError('value %s is not a valid uuid.UUId' % value)
        else:
            return None

    def process_result_value(self, value, dialect=None):
        if value:
            return uuid.UUID(bytes=value)
        else:
            return None

    def is_mutable(self):
        return False