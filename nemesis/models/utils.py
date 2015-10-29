# -*- coding: utf-8 -*-
import uuid
from sqlalchemy import types
from sqlalchemy.engine import reflection
from flask.ext.login import current_user


def safe_current_user_id():
    try:
        user_id = int(current_user.get_id()) if current_user else None
    except (ValueError, TypeError):
        user_id = None
    return user_id


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


def get_class_by_tablename(tablename):
    """Return class reference mapped to table.

    :param tablename: String with name of table.
    :return: Class reference or None.
    """
    from nemesis.systemwide import db

    for c in db.Model._decl_class_registry.values():
        if hasattr(c, '__tablename__') and c.__tablename__ == tablename and\
                check_table_exists_in_schema(tablename):
            return c


def check_table_exists_in_schema(tablename):
    from nemesis.systemwide import db

    inspector = reflection.Inspector.from_engine(db.engine)
    existing_tables = inspector.get_table_names()
    return tablename in existing_tables