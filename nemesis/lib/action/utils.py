# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import exists, join, and_, or_
from sqlalchemy.sql.expression import func, between

from nemesis.models.actions import Action, ActionType, ActionType_Service, ActionType_rbDiagnosisType
from nemesis.models.accounting import PriceListItem
from nemesis.models.enums import ActionTypeClass, ATClass
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


def check_at_service_pli_match(action_type_id, price_list_item_id):
    return db.session.query(
        exists().select_from(
            join(
                ActionType_Service, PriceListItem,
                PriceListItem.service_id == ActionType_Service.service_id
            )
        ).where(
            ActionType_Service.master_id == action_type_id
        ).where(
            between(func.curdate(),
                    ActionType_Service.begDate,
                    func.coalesce(ActionType_Service.endDate, func.curdate()))
        ).where(
            PriceListItem.id == price_list_item_id
        )
    ).scalar()


def check_action_service_requirements(action_type_id, price_list_item_id=None):
    result = {
        'result': True,
        'message': ''
    }
    required = check_at_service_requirement(action_type_id)
    result['result'] = not required

    if required:
        if not price_list_item_id:
            result['message'] = u'Действие требует оплаты, однако не передан атрибут `price_list_item_id`. ' \
                                u'Возможно, в настройках прайс-листа для выбранного договора отсутствует позиция, ' \
                                u'соответствующая выбранному действию.'
        else:
            pli_matched = check_at_service_pli_match(action_type_id, price_list_item_id)
            if not pli_matched:
                result['message'] = u'Действие требует оплаты, однако в настройках прайс-листа для выбранного ' \
                                    u'договора отсутствует позиция, соответствующая выбранному действию. Атрибут ' \
                                    u'`price_list_item_id` не соответствует ни одной встречающейся в данном прайс-' \
                                    u'листе позиции'
            else:
                result['result'] = True
    return result


def get_prev_inspection_with_diags(action):
    return db.session.query(Action).join(ActionType).join(
        ActionType.diagnosis_types
    ).filter(
        Action.deleted == 0,
        Action.event_id == action.event_id,
        or_(Action.begDate < action.begDate,
            and_(Action.begDate == action.begDate,
                 Action.id < action.id if action.id else True)
            ),
        Action.id != action.id
    ).order_by(Action.begDate.desc()).limit(1)


def get_action_type_class(at_class, tissue_required):
    return ActionTypeClass(
        ActionTypeClass.diagnostics[0] if at_class == ATClass.diagno_labs[0] and not tissue_required else
        ActionTypeClass.lab[0] if at_class == ATClass.diagno_labs[0] and at_class else
        at_class
    )
