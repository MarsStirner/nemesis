# -*- coding: utf-8 -*-
from nemesis.lib.enum import Enum, EnumLoadable

__author__ = 'mmalkov'


class EventOrder(Enum):
    planned = 1, u'Планово'
    emergency = 2, u'Экстренно'
    without = 3, u'Самотёком'
    forced = 4, u'Принудительно'


class EventPrimary(Enum):
    primary = 1, u'Первично'
    secondary = 2, u'Повторно'
    active = 3, u'Активное посещение'
    transport = 4, u'Транспортировка'
    ambulatory = 5, u'Амбулаторно'


class ActionStatus(Enum):
    started = 0, u'Начато'
    waiting = 1, u'Ожидание'
    finished = 2, u'Закончено'
    cancelled = 3, u'Отменено'
    no_result = 4, u'Без результата'


class Gender(Enum):
    male = 1, u'М'
    female = 2, u'Ж'


class AddressType(Enum):
    reg = 0, u'Регистрации'
    live = 1, u'Проживания'


class LocalityType(Enum):
    vilage = 2, u'Село'
    city = 1, u'Город'


class AllergyPower(Enum):
    undefined = 0, u'не известно'
    low = 1, u'малая'
    medium = 2, u'средняя'
    high = 3, u'высокая'
    strict = 4, u'строгая'


class PaymentType(Enum):
    cash = 0, u'наличный'
    noncash = 1, u'безналичный'


class IntoleranceType(Enum):
    allergy = 0, u'Аллергия'
    medicine = 1, u'Медикаментозная непереносимость'


class PrenatalRiskRate(Enum):
    undefined = 0, u'не определен'
    low = 1, u'низкий'
    medium = 2, u'средний'
    high = 3, u'высокий'


class PerinatalRiskRate(EnumLoadable):
    __tablename__ = 'rbPerinatalRiskRate'

    # assumed values
    # undefined = 1, u'не определен'
    # low = 2, u'низкий'
    # medium = 3, u'средний'
    # high = 4, u'высокий'


class PreeclampsiaRisk(Enum):
    # впоследствии будет больше значений
    undefined = 0, u'не определен'
    has_risk = 1, u'есть риск'
    no_risk = 2, u'нет риска'


class PregnancyPathology(EnumLoadable):
    __tablename__ = 'rbPregnancyPathology'

    # assumed values
    # undefined = 1, u'Неопределенная'
    # extragenital = 2, u'Экстрагенитальная'
    # obstetric = 3, u'Акушерско-гинекологическая'
    # infectious = 4, u'Инфекционно-паразитарная'
    # combined = 5, u'Сочетанная'


class MeasureStatus(EnumLoadable):
    __tablename__ = 'rbMeasureStatus'

    # assumed values
    # assigned = 1, u'Назначенное'
    # waiting = 2, u'Ожидает результатов'
    # upon_med_indications = 3, u'По показанию'
    # cancelled = 4, u'Отмененное'
    # overdue = 5, u'Просроченное'
    # performed = 6, u'Выполненное'


class MeasureScheduleType(EnumLoadable):
    __tablename__ = 'rbMeasureScheduleType'

    # assumed values
    # after_visit = 1, u'После каждого посещения врача'
    # after_first_visit = 2, u'После первого посещения'
    # within_pregnancy_range = 3, u'Диапазон срока беременности'
    # upon_med_indication = 4, u'По показаниям'
    # upon_diag_set = 5, u'При постановке диагноза'
    # in_presence_diag = 6, u'При наличии дополнительных диагнозов'


# TODO: think about usage
class MeasureScheduleTypeKind(Enum):
    absolute_dates = 1, u''
    relative_dates = 2, u''


class MeasureScheduleApplyType(EnumLoadable):
    __tablename__ = 'rbMeasureScheduleApplyType'

    # assumed values
    # before_next_visit = 1, u'До следующего осмотра'
    # range_up_to = 2, u'Контрольный срок'
    # bounds = 3, u'Границы повторения'


# TODO: think about usage
class MeasureScheduleApplyTypeKind(Enum):
    single = 1, u''
    repetitive = 2, u''


class ErrandStatus(EnumLoadable):
    __tablename__ = 'rbErrandStatus'


class MedicationPrescriptionStatus(Enum):
    draft = 0, u'Черновик'
    active = 1, u'Активное'
    on_hold = 2, u'Приостановлено'
    completed = 3, u'Завершено'
    entered_in_error = 4, u'Ошибочное'
    stopped = 5, u'Остановлено'
    superseded = 6, u'Заменено'
