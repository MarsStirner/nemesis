# -*- coding: utf-8 -*-
import contextlib
import logging
from collections import namedtuple
from datetime import datetime, time, timedelta, date

import collections

import blinker
import six
import sqlalchemy
from flask_login import current_user
from nemesis.lib.action.utils import action_needs_service
from nemesis.lib.agesex import parseAgeSelector, recordAcceptableEx
from nemesis.lib.apiutils import ApiException
from nemesis.lib.calendar import calendar
from nemesis.lib.const import (STATIONARY_MOVING_CODE, STATIONARY_ORG_STRUCT_STAY_CODE, STATIONARY_HOSP_BED_CODE,
    STATIONARY_LEAVED_CODE, STATIONARY_HOSP_LENGTH_CODE, STATIONARY_ORG_STRUCT_TRANSFER_CODE)
from nemesis.lib.user import UserUtils
from nemesis.lib.utils import get_new_uuid, group_concat, safe_date, safe_traverse, safe_datetime, bail_out
from nemesis.models.actions import (Action, ActionType, ActionPropertyType, ActionProperty, TakenTissueJournal, OrgStructure_ActionType, ActionProperty_OrgStructure,
                                    OrgStructure_HospitalBed, ActionProperty_HospitalBed, ActionProperty_Integer)
from nemesis.models.client import Client
from nemesis.models.enums import ActionStatus, MedicationPrescriptionStatus
from nemesis.models.event import Event, EventType_Action
from nemesis.models.exists import Person, OrgStructure
from nemesis.models.prescriptions import MedicalPrescription
from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db, cache
from sqlalchemy.orm.util import aliased

logger = logging.getLogger('simple')


# планируемая дата выполнения (default planned end date)
DPED_UNDEFINED = 0  # Не определено
DPED_NEXT_DAY = 1  # Следующий день
DPED_NEXT_WORK_DAY = 2  # Следедующий рабочий день
DPED_CURRENT_DAY = 3  # Текущий день

# дата выполнения (default end date)
DED_UNDEFINED = 0
DED_CURRENT_DATE = 1
DED_EVENT_SET_DATE = 2
DED_EVENT_EXEC_DATE = 3

# дата назначения (default direction date)
DDD_UNDEFINED = 0
DDD_EVENT_SET_DATE = 1
DDD_CURRENT_DATE = 2
DDD_ACTION_EXEC_DATE = 3

# ответственный
DP_UNDEFINED = 0
DP_EMPTY = 1
DP_SET_PERSON = 2
DP_EVENT_EXEC_PERSON = 3
DP_CURRENT_USER = 4


class ActionException(Exception): pass


class ActionServiceException(Exception): pass


def create_action(action_type_id, event, src_action=None, assigned=None, properties=None, data=None):
    """
    Базовое создание действия, например для отправки клиентской стороне.

    :param action_type_id: action_type_id int
    :param event: event_id or Event int
    :param src_action: другое действие Action, из которого будут браться данные
    :param assigned: список id ActionPropertyType, которые должны быть отмечены назначенными
    :param properties: список словарей с данными по ActionProperty, включая value
    :param data: словарь с данными для установки произвольных параметров действия
    :return: Action model
    """
    # TODO: transfer some checks from ntk
    if not action_type_id or not event:
        raise AttributeError

    actionType = ActionType.query.get(int(action_type_id)) or bail_out(ApiException(404, u'Тип действия с id=%s не найден' % action_type_id))
    if isinstance(event, (int, long, basestring)):
        event = Event.query.get(int(event))
    if event is None:
        raise ValueError('Event neither refer to existing Event nor newly created model')
    now = datetime.now()
    now_date = now.date()
    default_dt = get_new_action_default_dt(event)
    main_user_p = Person.query.get(current_user.get_main_user().id)

    action = Action()
    action.actionType = actionType
    action.actionType_id = action_type_id
    action.event = event
    action.event_id = event.id  # need for now
    action.begDate = default_dt
    action.setPerson = main_user_p
    action.office = actionType.office or u''
    action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.status = actionType.defaultStatus
    action.account = 0
    action.uet = 0  # TODO: calculate UET

    if actionType.defaultEndDate == DED_CURRENT_DATE:
        action.endDate = default_dt
    elif actionType.defaultEndDate == DED_EVENT_SET_DATE:
        action.endDate = event.setDate
    elif actionType.defaultEndDate == DED_EVENT_EXEC_DATE:
        action.endDate = event.execDate

    if actionType.defaultDirectionDate == DDD_EVENT_SET_DATE:
        action.directionDate = event.setDate
    elif actionType.defaultDirectionDate == DDD_CURRENT_DATE:
        action.directionDate = default_dt
    elif actionType.defaultDirectionDate == DDD_ACTION_EXEC_DATE and action.endDate:
        action.directionDate = max(action.endDate, event.setDate)
    else:
        action.directionDate = event.setDate

    if src_action:
        action.person = src_action.person
    elif actionType.defaultExecPerson_id:
        action.person = Person.query.get(actionType.defaultExecPerson_id)
    elif actionType.defaultPersonInEvent == DP_UNDEFINED:
        action.person = None
    elif actionType.defaultPersonInEvent == DP_SET_PERSON:
        action.person = action.setPerson
    elif actionType.defaultPersonInEvent == DP_EVENT_EXEC_PERSON:
        action.person = event.execPerson
    elif actionType.defaultPersonInEvent == DP_CURRENT_USER:
        action.person = main_user_p

    action.plannedEndDate = get_planned_end_datetime(action_type_id)
    action.uuid = get_new_uuid()

    # set changed attributes
    if data:
        for field, value in data.items():
            if field in Action.__table__.columns or hasattr(action, field):
                setattr(action, field, value)

    # some restrictions
    if action.status == ActionStatus.finished[0] and not action.endDate:
        action.endDate = default_dt
    elif action.endDate and action.status != ActionStatus.finished[0]:
        action.status = ActionStatus.finished[0]

    check_action_dates(action)

    # properties
    if assigned is None:
        assigned = []
    src_props = dict((prop.type_id, prop) for prop in src_action.properties) if src_action else {}
    full_props = dict((prop_desc['type']['id'], prop_desc) for prop_desc in properties) if properties else {}
    prop_types = actionType.property_types.filter(ActionPropertyType.deleted == 0)
    for prop_type in prop_types:
        if recordAcceptableEx(event.client.sexCode, event.client.age_tuple(now_date), prop_type.sex, prop_type.age):
            prop = ActionProperty()
            prop.type = prop_type
            prop.type_id = prop_type.id
            prop.action = action
            prop.action_id = action.id
            prop.isAssigned = prop_type.id in assigned
            if src_props.get(prop_type.id):
                prop.value = src_props[prop_type.id].value
            elif prop_type.id in full_props:
                prop_desc = full_props[prop_type.id]
                prop.value = prop_desc['value']
                prop.isAssigned = prop_desc['is_assigned']
            elif prop.type.defaultValue:
                prop.set_value(prop.type.defaultValue, True)
            else:
                prop.value = None
            action.properties.append(prop)

    return action


def create_action_property(action, prop_type):
    prop = ActionProperty()
    prop.type = prop_type
    prop.type_id = prop_type.id
    prop.action = action
    prop.action_id = action.id
    action.properties.append(prop)
    return prop


def update_action_prescriptions(action, prescriptions):
    if not prescriptions:
        return
    prescriptions_map = dict(
        (presc.id, presc)
        for presc in action.medication_prescriptions
    )
    for presc in prescriptions:
        p_obj = prescriptions_map.get(presc.get('id'))
        if not p_obj:
            if presc.get('deleted'):
                continue
            p_obj = MedicalPrescription()
            p_obj.modifyPerson_id = p_obj.createPerson_id = safe_current_user_id()
            action.medication_prescriptions.append(p_obj)

        p_obj.set_json(presc)

        if not presc.get('deleted'):
            p_obj.reasonOfCancel = None
            p_obj.status_id = safe_traverse(presc, 'status', 'id', default=MedicationPrescriptionStatus.active[0])
        else:
            p_obj.status_id = safe_traverse(presc, 'status', 'id', default=MedicationPrescriptionStatus.stopped[0])


def create_new_action(action_type_id, event_id, src_action=None, assigned=None, properties=None, data=None,
                      service_data=None):
    """
    Создание действия для сохранения в бд.

    :param action_type_id: action_type_id int
    :param event_id: event_id int
    :param src_action: другое действие Action, из которого будут браться данные
    :param assigned: список id ActionPropertyType, которые должны быть отмечены назначенными
    :param properties: список словарей с данными по ActionProperty, включая value
    :param data: словарь с данными для установки произвольных параметров действия
    :return: Action model
    """
    action = create_action(action_type_id, event_id, src_action, assigned, properties, data)
    update_action_prescriptions(action, data.get('prescriptions'))

    org_structure = action.event.current_org_structure
    if action.actionType.isRequiredTissue and org_structure:
        create_TTJ_record(action)

    # Service
    if action_needs_service(action):
        if not service_data:
            raise ActionServiceException(u'Для action требуется услуга, но данные service_data отсутствуют')

        from nemesis.lib.data_ctrl.accounting.service import ServiceController
        service_ctrl = ServiceController()
        new_service = service_ctrl.get_new_service_for_new_action(action, service_data)
        db.session.add(new_service)
        db.session.add_all(new_service.get_flatten_subservices())

    return action


def update_action(action, **kwargs):
    """
    Обновление модели действия данными из kwargs.

    kwargs может содержать:
      - атрибуты Action со значениями
      - properties_assigned - список id ActionPropertyType, которые должны
      быть отмечены назначаемыми для исследований
      - properties - список словарей для редактирования данных свойств в целом

    :type action: Action
    :param action: Action
    :param properties_assigned: список id ActionPropertyType, которые должны быть отмечены назначаемыми для исследований
    :param properties: список словарей для редактирования данных свойств в целом
    :return: Action
    """
    # action attributes
    for attr in ('amount', 'account', 'status', 'person_id', 'setPerson_id', 'begDate', 'endDate', 'directionDate',
                 'isUrgent', 'plannedEndDate', 'coordPerson_id', 'coordDate', 'note', 'uet', 'payStatus',
                 'contract_id', 'office'):
        if attr in kwargs:
            setattr(action, attr, kwargs.get(attr))

    check_action_dates(action)

    # properties (only assigned data)
    assigned = kwargs.get('properties_assigned')
    if assigned:
        for ap in action.properties:
            ap.isAssigned = ap.type_id in assigned

    # properties (full data)
    for prop_desc in kwargs.get('properties', []):
        type_id = prop_desc['type']['id']
        prop = action.propsByTypeId.get(type_id)
        if not prop:
            logger.warn(u'Попытка установить свойство, когорого нет у действия (Action.id=%s, type_id=%s)' % (action.id, type_id))
            continue
        prop.value = prop_desc['value']
        prop.isAssigned = prop_desc['is_assigned']

    update_action_prescriptions(action, kwargs.get('prescriptions'))

    return action


def delete_action(action):
    if not UserUtils.can_delete_action(action):
        raise ActionException(u'У пользователя нет прав на удаление действия с id = %s' % action.id)
    action.delete()
    from nemesis.lib.data_ctrl.accounting.service import ServiceController
    ctrl = ServiceController()
    service = ctrl.get_action_service(action)
    if service:
        ctrl.delete_service(service, True)
    return action


def format_action_data(json_data):
    set_person_id = safe_traverse(json_data, 'set_person', 'id')
    person_id = safe_traverse(json_data, 'person', 'id')
    data = {
        'begDate': safe_datetime(json_data['beg_date']),
        'endDate': safe_datetime(json_data['end_date']),
        'plannedEndDate': safe_datetime(json_data['planned_end_date']),
        'directionDate': safe_datetime(json_data['direction_date']),
        'isUrgent': json_data['is_urgent'],
        'status': json_data['status']['id'],
        'setPerson_id': set_person_id,
        'person_id':  person_id,
        'setPerson': Person.query.get(set_person_id) if set_person_id else None,
        'person':  Person.query.get(person_id) if person_id else None,
        'note': json_data['note'],
        'amount': json_data['amount'],
        'account': json_data['account'] or 0,
        'uet': json_data['uet'],
        'payStatus': json_data['pay_status'] or 0,
        'coordDate': safe_datetime(json_data['coord_date']),
        'office': json_data['office'],
        'properties': json_data['properties']
    }
    return data


def get_new_action_default_dt(event):
    now = datetime.now()
    e_beg = event.setDate
    e_end = event.execDate

    default_date = now
    if now < e_beg:
        default_date = e_beg
    elif e_end is not None:
        if now > e_end:
            default_date = e_end
    return default_date


def check_action_dates(action):
    e_beg = action.event.setDate
    e_end = action.event.execDate
    for d, name in ((action.begDate, u'Дата начала'),
                    (action.endDate, u'Дата окончания'),
                    (action.plannedEndDate, u'Плановая дата выполнения')):
        if d is not None and (d < e_beg or (e_end is not None and d > e_end)):
            raise ActionException(u'{0} выходит за период действия обращения {1}-{2}'.format(
                name, e_beg, e_end or u''
            ))


def create_TTJ_record(action):
    """
    @type action: nemesis.models.actions.Action
    @param action:
    @return:
    """
    planned_end_date = action.plannedEndDate
    if not planned_end_date:
        raise ActionException(
            u'Не заполнена плановая дата исследования "%s" (ActionType.id = %s)' % (
                action.actionType.name,
                action.actionType_id))
    at_tissue_types = action.actionType.tissue_types
    if not at_tissue_types:
        raise ActionException(
            u'Действие "%s" требует забор биоматериала, но не указан ни один необходимый тип биоматериала (ActionType.id = %s)' % (
                action.actionType.name,
                action.actionType_id))

    client = action.event.client
    ttj_ids = set()
    for attt in at_tissue_types:
        ttj = TakenTissueJournal.query.filter(
            TakenTissueJournal.client == client,
            TakenTissueJournal.tissueType == attt.tissueType,
            TakenTissueJournal.testTubeType == attt.testTubeType,
            TakenTissueJournal.datetimePlanned == planned_end_date,
        ).first()
        if not ttj:
            ttj = TakenTissueJournal()
            ttj.client = client
            ttj.tissueType = attt.tissueType
            ttj.amount = attt.amount
            ttj.unit = attt.unit
            ttj.datetimePlanned = planned_end_date
            ttj.externalId = action.event.externalId
            ttj.testTubeType = attt.testTubeType
        else:
            if ttj.statusCode == 0:
                ttj.amount += attt.amount
            else:
                # Если забор уже произведён, то надо уведомить врача о возможных проблемах
                action.note = u'Биозабор уже %s. Возможны проблемы с нехваткой биоматериала для новых анализов' % (
                    {1: u'начат', 2: u'закончен'}.get(ttj.statusCode, u'отправлен в ЛИС')
                )
            if ttj.statusCode in (3, 4):
                # Отправка в ЛИС уже произведена. Надо переотправить
                ttj_ids.add(ttj.id)
        action.tissues.append(ttj)
        db.session.add(ttj)
    blinker.signal('Core.Notify.TakenTissueJournal').send(None, ids=ttj_ids)


def isRedDay(date):
    holidays = calendar.getList()
    holiday = False
    for hol in holidays:
        break
    return date.isoweekday() > 5 or holiday


def addPeriod(startDate, length, countRedDays):
    u"""Добавление к некоторой дате некоторого периода в днях.
    Сама дата, к которой идет прибавление дней, уже считается как целый день,
    кроме случая, когда она является выходным или праздником. При передаче
    False аргументу countRedDays при добавлении периода будут учитываться
    только рабочие дни (не выходные и не праздники).

    args:
    startDate -- начальная дата
    length -- число дней для добавления
    countRedDays -- считать или нет выходные и праздники

    """
    if isinstance(startDate, datetime):
        savedTime = startDate.time()
        startDate = startDate.date()
    else:
        savedTime = None

    if countRedDays:
        result_date = startDate + timedelta(days=length-1)
    else:
        current_date = startDate
        # если начальная дата не рабочий день, то она не должна учитываться
        while isRedDay(current_date):
            current_date = current_date + timedelta(days=1)
        days_count = length - 1  # не считая текущий
        if days_count < 0:
            current_date = startDate + timedelta(days=-1)
        while days_count > 0:
            current_date = current_date + timedelta(days=1)
            if not isRedDay(current_date):
                days_count -= 1
        result_date = current_date
    if savedTime:
        result_date = datetime.combine(result_date, savedTime)
    return result_date


def get_planned_end_datetime(action_type_id):
    """Получение планируемого времени для действия
    @param actionType_id: тип действия
    @return: дата, время понируемого действия
    @rtype 2-tuple"""
    now = datetime.now()
    current_date = now.date()
    action_type = ActionType.query.get(int(action_type_id))

    default_planned_end = action_type.defaultPlannedEndDate
    if default_planned_end == DPED_UNDEFINED:
        return None
    planned_end_date = current_date
    if default_planned_end == DPED_NEXT_DAY:
        planned_end_date = addPeriod(now, 2, True)
    elif default_planned_end == DPED_NEXT_WORK_DAY:
        planned_end_date = addPeriod(now, 2, False)

    planned_end_time = time(7, 0)
    if default_planned_end == DPED_CURRENT_DAY:
        cur_hour = now.hour
        if cur_hour == 23:
            planned_end_time = time(23, 59)
        else:
            planned_end_time = time(cur_hour + 1, 0)
    return datetime.combine(planned_end_date, planned_end_time)


def _split_to_integers(string):
    if string:
        return map(int, string.split())
    return []


at_tuple = collections.namedtuple(
    'at_tuple',
    'id name code flat_code gid age sex at_os required_tissue at_apt class_ at_et children'
)

at_flat_tuple = collections.namedtuple(
    'at_flat_tuple',
    'id name code flat_code gid age sex at_os required_tissue at_apt'
)


def at_tuple_2_flat_tuple_convert(item):
    return at_flat_tuple(*item[:10])


@cache.memoize(3600)
def select_all_at():
    tmp_apt_dict = {
        id_: (id_, name, parseAgeSelector(age), sex)
        for id_, name, age, sex in ActionPropertyType.query.filter(
            ActionPropertyType.deleted == 0,
            ActionPropertyType.isAssignable == 1,
        ).with_entities(
            ActionPropertyType.id,
            ActionPropertyType.name,
            ActionPropertyType.age,
            ActionPropertyType.sex
        )
    }
    at_apt_dict = {
        at_id: [tmp_apt_dict.get(apt_id) for apt_id in _split_to_integers(apt_ids)]
        for at_id, apt_ids in ActionPropertyType.query.filter(
            ActionPropertyType.deleted == 0,
            ActionPropertyType.isAssignable == 1,
        ).group_by(
            ActionPropertyType.actionType_id
        ).with_entities(
            ActionPropertyType.actionType_id,
            group_concat(ActionPropertyType.id, ' '),
        )
    }
    at_os_dict = {
        at_id: _split_to_integers(os_ids)
        for at_id, os_ids in OrgStructure_ActionType.query.group_by(
            OrgStructure_ActionType.actionType_id
        ).with_entities(
            OrgStructure_ActionType.actionType_id,
            group_concat(OrgStructure_ActionType.master_id, ' ')
        )
    }
    at_et_dict = {
        at_id: _split_to_integers(et_ids)
        for at_id, et_ids in EventType_Action.query.group_by(
            EventType_Action.actionType_id
        ).with_entities(
            EventType_Action.actionType_id,
            group_concat(EventType_Action.eventType_id, ' ')
        )
    }
    l = ActionType.query.filter(
        ActionType.deleted == 0,
        ActionType.hidden == 0,
        ActionType.class_.in_([0, 1, 2, 3])
    ).with_entities(
        ActionType.id,              # 0
        ActionType.name,            # 1
        ActionType.code,            # 2
        ActionType.flatCode,        # 3
        ActionType.group_id,        # 4
        ActionType.age,             # 5
        ActionType.sex,             # 6
        ActionType.isRequiredTissue,    # 7
        ActionType.class_,          # 8
    )
    tmp_dict = {
        id_: at_tuple(
            id_,
            name,
            code,
            flat_code,
            gid,
            parseAgeSelector(age),
            sex,
            at_os_dict.get(id_, []),
            bool(required_tissue),
            at_apt_dict.get(id_, []),
            class_,
            at_et_dict.get(id_, []),
            set(),
        )
        for id_, name, code, flat_code, gid, age, sex, required_tissue, class_ in l
    }

    for item in six.itervalues(tmp_dict):
        if item.gid in tmp_dict:
            tmp_dict[item.gid].children.add(item.id)

    result = collections.defaultdict(dict)

    for item in six.itervalues(tmp_dict):
        result[item.class_][item.id] = item

    return result


@cache.memoize(3600)
def int_get_atl_flat(at_class, event_type_id=None):
    d = select_all_at()[at_class]
    if event_type_id is None:
        filtered = {
            item.id: at_tuple_2_flat_tuple_convert(item)
            for item in six.itervalues(d)
        }
    else:
        filtered = {
            item.id: at_tuple_2_flat_tuple_convert(item)
            for item in six.itervalues(d)
            if event_type_id in item.at_et
        }

    def upstairs(item):
        gid = item.gid
        if gid and gid in d and gid not in filtered:
            super_item = at_tuple_2_flat_tuple_convert(d[gid])
            upstairs(super_item)
            filtered[gid] = super_item

    for item in filtered.values():
        upstairs(item)

    return filtered


@cache.memoize(3600)
def int_get_atl_dict_all():
    result = {}
    for d in six.itervalues(select_all_at()):
        for item in six.itervalues(d):
            result[item.id] = at_tuple_2_flat_tuple_convert(item)
    return result


def get_patient_location(event, dt=None):
    if event.is_stationary:
        query = _get_stationary_location_query(event, dt)
        query = query.with_entities(
            OrgStructure
        )
        current_os = query.first()
    else:
        current_os = event.orgStructure
    return current_os


def _get_stationary_location_query(event, dt=None):
    query = _get_moving_query(event, dt, False)
    query = query.join(
        ActionProperty
    ).join(
        ActionPropertyType, db.and_(ActionProperty.type_id == ActionPropertyType.id,
                                    ActionPropertyType.actionType_id == ActionType.id)
    ).join(
        ActionProperty_OrgStructure, ActionProperty.id == ActionProperty_OrgStructure.id
    ).join(
        OrgStructure
    ).filter(
        ActionPropertyType.code == STATIONARY_ORG_STRUCT_STAY_CODE
    )
    return query


def get_patient_hospital_bed(event, dt=None):
    query = _get_moving_query(event, dt, False)
    query = query.join(
        ActionProperty
    ).join(
        ActionPropertyType, db.and_(ActionProperty.type_id == ActionPropertyType.id,
                                    ActionPropertyType.actionType_id == ActionType.id)
    ).join(
        ActionProperty_HospitalBed, ActionProperty.id == ActionProperty_HospitalBed.id
    ).join(
        OrgStructure_HospitalBed
    ).filter(
        ActionPropertyType.code == STATIONARY_HOSP_BED_CODE
    ).with_entities(
        OrgStructure_HospitalBed
    )
    hb = query.first()
    return hb


def _get_moving_query(event, dt=None, finished=None):
    query = db.session.query(Action).join(
        ActionType
    ).filter(
        Action.event_id == event.id,
        Action.deleted == 0,
        ActionType.flatCode == STATIONARY_MOVING_CODE
    )
    if dt:
        query = query.filter(Action.begDate <= dt)
    elif finished is not None:
        if finished:
            query = query.filter(Action.status == ActionStatus.finished[0])
        else:
            query = query.filter(Action.status != ActionStatus.finished[0])
    query = query.order_by(Action.begDate.desc())
    return query


def get_hosp_length(event):
    def from_hosp_release():
        query = _get_hosp_release_query(event)
        query = query.join(
            ActionProperty
        ).join(
            ActionPropertyType, db.and_(ActionProperty.type_id == ActionPropertyType.id,
                                        ActionPropertyType.actionType_id == ActionType.id)
        ).join(
            ActionProperty_Integer, ActionProperty.id == ActionProperty_Integer.id
        ).filter(
            ActionPropertyType.code == STATIONARY_HOSP_LENGTH_CODE
        ).with_entities(
            ActionProperty_Integer
        )
        hosp_length = query.first()
        return hosp_length.value if hosp_length else None

    def _get_start_date_from_moving():
        query = _get_moving_query(event)
        start_date = query.with_entities(
            Action.begDate
        ).order_by(None).order_by(Action.begDate).first()
        return safe_date(start_date[0]) if start_date else None

    def _get_finish_date_from_moving():
        last_moving_q = _get_moving_query(event, finished=True)
        final_moving_q = last_moving_q.join(
            ActionProperty
        ).join(
            ActionPropertyType, db.and_(ActionProperty.type_id == ActionPropertyType.id,
                                        ActionPropertyType.actionType_id == ActionType.id)
        ).outerjoin(
            ActionProperty_Integer, ActionProperty.id == ActionProperty_Integer.id
        ).filter(
            ActionPropertyType.code == STATIONARY_ORG_STRUCT_TRANSFER_CODE,
            ActionProperty_Integer.id == None
        )
        end_date = final_moving_q.with_entities(
            Action.endDate
        ).first()
        return safe_date(end_date[0]) if end_date else None

    def calculate_not_finished():
        date_start = _get_start_date_from_moving() or event.setDate.date()
        date_to = _get_finish_date_from_moving()
        if not date_to:
            date_to = date.today()
        hosp_length = (date_to - date_start).days
        if event.is_day_hospital:
            hosp_length += 1
        return hosp_length

    # 1) from hospital release document
    duration = from_hosp_release()
    if duration is not None:
        hosp_length = duration
    else:
        # 2) calculate not yet finished stay length
        hosp_length = calculate_not_finished()
    return hosp_length


def _get_hosp_release_query(event):
    query = db.session.query(Action).join(
        ActionType
    ).filter(
        Action.event_id == event.id,
        Action.deleted == 0,
        ActionType.flatCode == STATIONARY_LEAVED_CODE
    ).filter(
        Action.status == ActionStatus.finished[0]
    ).order_by(Action.begDate.desc())
    return query


def get_assignable_apts(at_id, client_id=None):
    all_at_data = int_get_atl_dict_all()
    at_data = all_at_data.get(at_id)
    if at_data is not None:
        apt_data_list = at_data[9]
        if client_id:
            client = db.session.query(Client).get(client_id)
            client_age = client.age_tuple(date.today())
            filtered_apts = []
            for apt_data in apt_data_list:
                if recordAcceptableEx(client.sexCode, client_age, apt_data[3], apt_data[2]):
                    filtered_apts.append(apt_data)
            apt_data_list = filtered_apts
    else:
        apt_data_list = []

    return apt_data_list


def get_client_diagnostics(client, beg_date, end_date=None, including_closed=False):
    """
    :type client: nemesis.models.client.Client
    :type beg_date: datetime.date
    :type end_date: datetime.date | NoneType
    :type including_closed: bool
    :param client:
    :param beg_date:
    :param end_date:
    :param including_closed:
    :return:
    :rtype: sqlalchemy.orm.Query
    """
    from nemesis.models.diagnosis import Diagnosis, Diagnostic
    query = db.session.query(Diagnostic).join(
        Diagnosis
    ).filter(
        Diagnosis.client == client,
        Diagnosis.deleted == 0,
        Diagnostic.deleted == 0,
        )
    if end_date is not None:
        query = query.filter(
            Diagnostic.createDatetime <= end_date,
            Diagnosis.setDate <= end_date,
            )
    if not including_closed:
        query = query.filter(
            db.or_(
                Diagnosis.endDate.is_(None),
                Diagnosis.endDate >= beg_date,
                )
        )
    query = query.group_by(
        Diagnostic.diagnosis_id
    )
    query = query.with_entities(sqlalchemy.func.max(Diagnostic.id).label('zid')).subquery()
    query = db.session.query(Diagnostic).join(query, query.c.zid == Diagnostic.id)
    return query
