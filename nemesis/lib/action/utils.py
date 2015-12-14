# -*- coding: utf-8 -*-

from sqlalchemy import exists
from sqlalchemy.orm import join

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


def action_is_prescriptions(action):
    return action.actionType.hasPrescriptions


def action_needs_service(action):
    action_type_id = action.actionType.id
    return db.session.query(
        exists().select_from(
            ActionType_Service
        ).where(ActionType_Service.master_id == action_type_id)
    ).scalar()
