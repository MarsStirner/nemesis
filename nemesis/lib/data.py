# -*- coding: utf-8 -*-
import logging
from datetime import datetime, time, timedelta, date

from flask.ext.login import current_user
from sqlalchemy.orm.util import aliased
from sqlalchemy.sql.expression import between, func
from nemesis.models.prescriptions import MedicalPrescription
from nemesis.models.utils import safe_current_user_id

from nemesis.systemwide import db, cache
from nemesis.lib.utils import get_new_uuid, group_concat, safe_date, safe_traverse, safe_datetime
from nemesis.lib.agesex import parseAgeSelector, recordAcceptableEx
from nemesis.models.actions import (Action, ActionType, ActionPropertyType, ActionProperty, Job, JobTicket,
    TakenTissueJournal, OrgStructure_ActionType, ActionType_Service, ActionProperty_OrgStructure,
    OrgStructure_HospitalBed, ActionProperty_HospitalBed, ActionProperty_Integer, Action_TakenTissueJournalAssoc)
from nemesis.models.enums import ActionStatus, MedicationPrescriptionStatus
from nemesis.models.exists import Person, ContractTariff, Contract, OrgStructure
from nemesis.models.event import Event, EventType_Action, EventType
from nemesis.lib.calendar import calendar
from nemesis.lib.const import (STATIONARY_MOVING_CODE, STATIONARY_ORG_STRUCT_STAY_CODE, STATIONARY_HOSP_BED_CODE,
    STATIONARY_LEAVED_CODE, STATIONARY_HOSP_LENGTH_CODE, STATIONARY_ORG_STRUCT_TRANSFER_CODE)
from nemesis.lib.action.utils import action_needs_service
from nemesis.lib.user import UserUtils


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

    now = datetime.now()
    now_date = now.date()
    actionType = ActionType.query.get(int(action_type_id))
    if isinstance(event, (int, long, basestring)):
        event = Event.query.get(int(event))
    if event is None:
        raise ValueError('Event neither refer to existing Event nor newly created model')
    main_user_p = Person.query.get(current_user.get_main_user().id)

    action = Action()
    action.actionType = actionType
    action.actionType_id = action_type_id
    action.event = event
    action.event_id = event.id  # need for now
    action.begDate = now  # todo
    action.setPerson = main_user_p
    action.office = actionType.office or u''
    action.amount = actionType.amount if actionType.amountEvaluation in (0, 7) else 1
    action.status = actionType.defaultStatus
    action.account = 0
    action.uet = 0  # TODO: calculate UET

    if actionType.defaultEndDate == DED_CURRENT_DATE:
        action.endDate = now
    elif actionType.defaultEndDate == DED_EVENT_SET_DATE:
        action.endDate = event.setDate
    elif actionType.defaultEndDate == DED_EVENT_EXEC_DATE:
        action.endDate = event.execDate

    if actionType.defaultDirectionDate == DDD_EVENT_SET_DATE:
        action.directionDate = event.setDate
    elif actionType.defaultDirectionDate == DDD_CURRENT_DATE:
        action.directionDate = now
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
        action.endDate = now
    elif action.endDate and action.status != ActionStatus.finished[0]:
        action.status = ActionStatus.finished[0]

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


def create_new_action(action_type_id, event_id, src_action=None, assigned=None, properties=None, data=None):
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
        os_id = org_structure.id
        create_TTJ_record(action)

    # Service
    if action_needs_service(action):
        from nemesis.lib.data_ctrl.accounting.service import ServiceController
        service_ctrl = ServiceController()
        new_service = service_ctrl.get_new_service_for_new_action(action)
        new_service.action = action
        db.session.add(new_service)

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

    # properties (only assigned data)
    assigned = kwargs.get('properties_assigned', [])
    for type_id in assigned:
        action.propsByTypeId[type_id].isAssigned = True

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
        raise Exception(u'У пользователя нет прав на удаление действия с id = %s' % action.id)
    action.delete()


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


def create_TTJ_record(action):
    planned_end_date = action.plannedEndDate
    if not planned_end_date:
        raise ActionException(u'Не заполнена плановая дата исследования')
    client_id = action.event.client_id
    at_tissue_type = action.actionType.tissue_type
    if at_tissue_type is None:
        raise ActionException(u'Неверно настроены параметры биозаборов для создания лабораторных исследований')

    ttj = TakenTissueJournal.query.filter(
        TakenTissueJournal.client_id == client_id,
        TakenTissueJournal.tissueType_id == at_tissue_type.tissueType_id,
        TakenTissueJournal.datetimeTaken == planned_end_date
    ).first()
    if not ttj:
        ttj = TakenTissueJournal()
        ttj.client_id = client_id
        ttj.tissueType_id = at_tissue_type.tissueType_id
        ttj.amount = at_tissue_type.amount
        ttj.unit_id = at_tissue_type.unit_id
        ttj.datetimeTaken = planned_end_date
        ttj.externalId = action.event.externalId
        ttj.testTubeType_id = at_tissue_type.testTubeType_id
    else:
        ttj.amount += at_tissue_type.amount
    db.session.add(ttj)
    db.session.commit()

    action_ttj = Action_TakenTissueJournalAssoc()
    action_ttj.action_id = action.id
    action_ttj.takenTissueJournal_id = ttj.id
    db.session.add(action_ttj)

    action.takenTissueJournal = ttj


def create_JT(action, orgstructure_id):
    """
    Создание JobTicket для лабораторного исследования

    :param action: Action
    :param orgstructure_id:
    :return: JobTicket
    """
    planned_end_date = action.plannedEndDate
    if not planned_end_date:
        raise ActionException(u'Не заполнена плановая дата исследования')
    job_type_id = action.actionType.jobType_id
    jt_date = planned_end_date.date()
    jt_time = planned_end_date.time()
    client_id = action.event.client_id
    at_tissue_type = action.actionType.tissue_type
    if at_tissue_type is None:
        raise ActionException(u'Неверно настроены параметры биозаборов для создания лабораторных исследований')

    job = Job.query.filter(
        Job.jobType_id == job_type_id,
        Job.date == jt_date,
        Job.orgStructure_id == orgstructure_id,
        Job.begTime <= jt_time,
        Job.endTime >= jt_time
    ).first()
    if not job:
        job = Job()
        job.date = jt_date
        job.begTime = '00:00:00'
        job.endTime = '23:59:59'
        job.jobType_id = job_type_id
        job.orgStructure_id = orgstructure_id
        job.quantity = 100
        db.session.add(job)
    ttj = TakenTissueJournal.query.filter(
        TakenTissueJournal.client_id == client_id,
        TakenTissueJournal.tissueType_id == at_tissue_type.tissueType_id,
        TakenTissueJournal.datetimeTaken == planned_end_date
    ).first()
    if not ttj:
        ttj = TakenTissueJournal()
        ttj.client_id = client_id
        ttj.tissueType_id = at_tissue_type.tissueType_id
        ttj.amount = at_tissue_type.amount
        ttj.unit_id = at_tissue_type.unit_id
        ttj.datetimeTaken = planned_end_date
        ttj.externalId = action.event.externalId
        db.session.add(ttj)
    action.takenTissueJournal = ttj
    jt = JobTicket()
    jt.job = job
    jt.datetime = planned_end_date
    db.session.add(jt)
    return jt


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

    defaultPlannedEndDate = action_type.defaultPlannedEndDate
    currentDate = datetime.now()
    if defaultPlannedEndDate == DPED_UNDEFINED:
        plannedEndDate = None
    elif defaultPlannedEndDate == DPED_NEXT_DAY:
        plannedEndDate = addPeriod(currentDate, 2, True)
    elif defaultPlannedEndDate == DPED_NEXT_WORK_DAY:
        plannedEndDate = addPeriod(currentDate, 2, False)
    elif defaultPlannedEndDate == DPED_CURRENT_DAY:
        plannedEndDate = current_date
    else:
        plannedEndDate = None

    plannedEndTime = None
    if plannedEndDate:
        if defaultPlannedEndDate < DPED_CURRENT_DAY:
            plannedEndTime = time(7, 0)
        elif defaultPlannedEndDate == DPED_CURRENT_DAY:
            cur_hour = now.hour
            if cur_hour == 23:
                plannedEndTime = time(23, 59)
            else:
                plannedEndTime = time(cur_hour + 1, 0)
    if plannedEndDate is None:
        plannedEndDate = current_date
    if plannedEndTime is None:
        plannedEndTime = time(7, 0)
    return datetime.combine(plannedEndDate, plannedEndTime)


@cache.memoize(86400)
def int_get_atl_flat(at_class, event_type_id=None, contract_id=None):
    id_list = {}

    def schwing(t):
        t = list(t)
        t[5] = list(parseAgeSelector(t[7]))
        t[7] = t[7].split() if t[7] else None
        t[8] = bool(t[8])
        t.append([])
        id_list[t[0]] = t
        return t

    def _filter_atl(query):
        """
        Отфильтровать сырые AT по возможности их создания для выбранного
        типа события и по существованию соответствующих позиций в прайсе услуг.

        В итоговый результат нужно также включить внутренние узлы дерева для
        возможности построения этого самого дерева в интерфейсе. Поэтому к
        отфильтрованным AT сначала добавляются все возможные промежуточные
        узлы, а затем лишние убираются.
        """
        at_2 = aliased(ActionType, name='AT2')
        internal_nodes_q = db.session.query(ActionType.id.distinct().label('id'), ActionType.group_id).join(
            at_2, ActionType.id == at_2.group_id
        ).filter(
            ActionType.deleted == 0, at_2.deleted == 0,
            ActionType.hidden == 0, at_2.hidden == 0,
            ActionType.class_ == at_class, at_2.class_ == at_class
        ).subquery('AllInternalNodes')
        # 1) filter atl query by EventType_Action reference and include *all* internal AT tree nodes in result
        ats = query.outerjoin(
            internal_nodes_q, ActionType.id == internal_nodes_q.c.id
        ).outerjoin(
            EventType_Action, db.and_(EventType_Action.actionType_id == ActionType.id,
                                      EventType_Action.eventType_id == event_type_id)
        )
        # 2) filter atl query by contract tariffs if necessary
        need_price_list = EventType.query.get(event_type_id).createOnlyActionsWithinPriceList
        if contract_id and need_price_list:
            ats = ats.outerjoin(
                ActionType_Service, db.and_(ActionType.id == ActionType_Service.master_id,
                                            between(func.curdate(),
                                                    ActionType_Service.begDate,
                                                    func.coalesce(ActionType_Service.endDate, func.curdate())))
            ).outerjoin(
                ContractTariff, db.and_(ActionType_Service.service_id == ContractTariff.service_id,
                                        ContractTariff.master_id == contract_id,
                                        ContractTariff.eventType_id == event_type_id,
                                        # временно убрана проверка на даты действия тарифа в прайсе.
                                        # Вернуть с добавлением возможности работы с несколькими контрактами в обращении.
                                        ContractTariff.deleted == 0)  # between(func.curdate(), ContractTariff.begDate, ContractTariff.endDate)
            ).outerjoin(
                Contract, db.and_(Contract.id == ContractTariff.master_id,
                                  Contract.deleted == 0)
            ).filter(
                db.or_(db.and_(EventType_Action.id != None,
                               ContractTariff.id != None,
                               Contract.id != None,
                               ActionType_Service.id != None),
                       internal_nodes_q.c.id != None)
            )
        else:
            # filter for 1)
            ats = ats.filter(
                db.or_(internal_nodes_q.c.id != None, EventType_Action.id != None)
            )

        result = map(schwing, ats)

        # remove unnecessary internal nodes
        all_internal_nodes = dict((at_id, gid) for at_id, gid in db.session.query(internal_nodes_q))
        used_internal_nodes = set()
        for item in result:
            at_id = item[0]
            gid = item[4]
            if at_id not in all_internal_nodes and gid:
                used_internal_nodes.add(gid)
        while used_internal_nodes:
            at_id = used_internal_nodes.pop()
            if at_id in all_internal_nodes:
                used_internal_nodes.add(all_internal_nodes[at_id])
                del all_internal_nodes[at_id]

        exclude_ids = all_internal_nodes.keys()
        result = [item for item in result if item[0] not in exclude_ids]
        # and from external reference
        for at_id in exclude_ids:
            del id_list[at_id]
        return result


    ats = db.session.query(
        ActionType.id,
        ActionType.name,
        ActionType.code,
        ActionType.flatCode,
        ActionType.group_id,
        ActionType.age,
        ActionType.sex,
        group_concat(OrgStructure_ActionType.master_id, ' '),
        ActionType.isRequiredTissue
    ).outerjoin(OrgStructure_ActionType).filter(
        ActionType.class_ == at_class,
        ActionType.deleted == 0,
        ActionType.hidden == 0
    ).group_by(ActionType.id)

    if event_type_id:
        result = _filter_atl(ats)
    else:
        result = map(schwing, ats)

    apts = db.session.query(
        ActionPropertyType.actionType_id,
        ActionPropertyType.id,
        ActionPropertyType.name,
        ActionPropertyType.age,
        ActionPropertyType.sex
    ).filter(
        ActionPropertyType.isAssignable != 0,
        ActionPropertyType.actionType_id.in_(id_list.keys()),
        ActionPropertyType.deleted == 0
    )
    # Да, данные в итоговом результате заполняются через id_list
    map(lambda (at_id, apt_id, name, age, sex):
        id_list[at_id][9].append(
            (apt_id, name, list(parseAgeSelector(age)), sex)
        ),
        apts)
    return result


@cache.cached(86400, key_prefix='AT_dict_all')
def int_get_atl_dict_all():
    all_at_apt = {}
    for class_ in range(4):
        flat = int_get_atl_flat(class_)
        all_at_apt.update(dict([(at[0], at) for at in flat]))
    return all_at_apt


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