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


class ATClass(Enum):
    medical_documents = 0, u'Медицинские документы'
    diagno_labs = 1, u'Инструментальные исследования/Лабораторные исследования'
    treatments = 2, u'Манипуляции и операции'
    movings = 3, u'Движения'


class ActionTypeClass(Enum):
    medical_documents = 0, u'Медицинские документы'
    diagnostics = 1, u'Инструментальные исследования'
    treatments = 2, u'Манипуляции и операции'
    movings = 3, u'Движения'
    lab = 4, u'Лабораторные исследования'


class RequestTypeKind(Enum):
    stationary = 0, u'Стационар'  # rbRequestType.code - clinic, hospital
    policlinic = 1, u'Поликлиника'  # rbRequestType.code - policlinic, diagnostic
    dispensary = 2, u'Диспансер'  # rbRequestType.code - 5


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


class PerinatalRiskRate(EnumLoadable):
    __tablename__ = 'rbPerinatalRiskRate'

    undefined = 1, u'не определен'
    low = 2, u'низкий'
    medium = 3, u'средний'
    high = 4, u'высокий'


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

    created = 1, u'Создано'
    assigned = 2, u'Назначенное'
    waiting = 3, u'Ожидает результатов'
    upon_med_indications = 4, u'По показанию'
    overdue = 5, u'Просроченное'
    performed = 6, u'Выполненное'
    cancelled = 7, u'Отмененное'
    cancelled_dupl = 8, u'Отмененное, как дубль'
    cancelled_changed_data = 9, u'Отмененное, при изменении срока'
    cancelled_invalid = 10, u'Отмененное, как недействительное'


class MeasureScheduleType(EnumLoadable):
    __tablename__ = 'rbMeasureScheduleType'

    # assumed values
    # after_visit = 1, u'После каждого посещения врача'
    # after_first_visit = 2, u'После первого посещения'
    # within_pregnancy_range = 3, u'Диапазон срока беременности'
    # upon_med_indication = 4, u'По показаниям'
    # upon_diag_set = 5, u'При постановке диагноза'
    # in_presence_diag = 6, u'При наличии дополнительных диагнозов'


class MeasureScheduleApplyType(EnumLoadable):
    __tablename__ = 'rbMeasureScheduleApplyType'

    # assumed values
    # before_next_visit = 1, u'До следующего осмотра'
    # range_up_to = 2, u'Контрольный срок'
    # bounds = 3, u'Границы повторения'


class EventMeasureActuality(Enum):
    not_actual = 0, u'Неактуально'
    actual = 1, u'Актуально'


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


class ContragentType(Enum):
    undefined = 0, u'не выбрано'
    individual = 1, u'Физ. лицо'
    legal = 2, u'Юр. лицо'


class ContractContragentType(Enum):
    payer = 0, u'Плательщик'
    recipient = 1, u'Получатель'


class ContractTypeContingent(Enum):
    arbitrary_presence = 0, u'не требуется наличие пациента в списке контингента'
    strict_presence = 1, u'требуется наличие пациента в списке контингента'


class FinanceTransactionType(Enum):
    payer_balance = 1, u'Движение средств на счёте плательщика'
    invoice = 2, u'Движение средств по выставленным счетам'


class FinanceOperationType(EnumLoadable):
    payer_balance_in = 1, u'Поступление денежных средств'
    payer_balance_out = 2, u'Возврат денежных средств'
    invoice_pay = 3, u'Оплата по счёту'
    invoice_cancel = 4, u'Отмена оплаты по счёту'


class ServiceKind(EnumLoadable):
    __tablename__ = 'rbServiceKind'

    simple_action = 1, u'Простая услуга'
    group = 2, u'Набор услуг'
    lab_action = 3, u'Лабораторное исследование с показателями'
    lab_test = 4, u'Показатель лабораторного исследования'


class TTJStatus(Enum):
    waiting = 0, u'Ожидание'
    in_progress = 1, u'Выполнение'
    finished = 2, u'Закончено'
    sent_to_lab = 3, u'Отправлено в лабораторию'
    fail_to_lab = 4, u'Неудачно отправлено в лабораторию'


class CardFillRate(Enum):
    not_required = 0, u'Не требуется'
    waiting = 1, u'Ожидается'
    filled = 2, u'Заполнено'
    not_filled = 3, u'Не заполнено'


class ActionPayStatus(Enum):
    not_paid = 0, u'Не оплачено'
    paid = 1, u'Оплачено'
    refunded = 2, u'Совершен возврат'


class OrgStructType(Enum):
    amb = 0, u'Амбулатория'
    clinic = 1, u'Дневной стационар'
    emergency = 2, u'Скорая помощь'
    mobile = 3, u'Мобильная станция'
    hosp_reception = 4, u'Приемное отделение стационара'
    hospital = 5, u'Круглосутоный стационар'
    resuscitation = 6, u'Реанимация'


class HospStateStatus(Enum):
    current = 0, u'Текущие'
    received = 1, u'Поступившие'
    transferred = 2, 'Переведенные'
    leaved = 3, 'Выписанные'

