# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import exists
from sqlalchemy.sql.expression import func, between

from nemesis.models.actions import Action, ActionType, ActionType_Service
from nemesis.systemwide import db


def action_is_bak_lab(action):
    """
    :type action: application.models.actions.Action | int
    :param action:
    :return:
    """
    if isinstance(action, int):
        action = Action.query.get(action)
        if not action:
            return False
    return action.actionType.mnem == 'BAK_LAB'


def action_is_lab(action):
    """
    :type action: application.models.actions.Action | int
    :param action:
    :return:
    """
    if isinstance(action, int):
        action = Action.query.get(action)
        if not action:
            return False
    return action.actionType.isRequiredTissue or action.actionType.mnem == 'LAB'


def at_is_lab(action_type_id):
    return bool(db.session.query(
        ActionType.isRequiredTissue
    ).select_from(ActionType).filter(
        ActionType.id == action_type_id
    ).scalar())


def action_is_prescriptions(action):
    return action.actionType.hasPrescriptions


def action_needs_service(action):
    action_type_id = action.actionType_id
    return check_at_service_requirement(action_type_id)


def check_at_service_requirement(action_type_id, when=None):
    if not when:
        when = datetime.date.today()
    return db.session.query(
        exists().select_from(
            ActionType_Service
        ).where(
            ActionType_Service.master_id == action_type_id
        ).where(
            between(when,
                    ActionType_Service.begDate,
                    func.coalesce(ActionType_Service.endDate, func.curdate()))
        )
    ).scalar()
