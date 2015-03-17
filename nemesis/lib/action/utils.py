# -*- coding: utf-8 -*-

from nemesis.models.actions import Action


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