# -*- coding: utf-8 -*-
__author__ = 'plakrisenko'
import datetime
from sqlalchemy import func, or_, Integer
from sqlalchemy.orm import aliased
from sqlalchemy import cast

from nemesis.models.client import ClientIdentification
from nemesis.models.exists import rbCounter, rbAccountingSystem
from nemesis.models.accounting import Contract, Invoice
from nemesis.systemwide import db


class Counter(object):
    code = None

    def __init__(self):
        self.counter = rbCounter.query.filter(rbCounter.code == self.code).first()

    def increment_value(self):
        self.counter.value = self.get_next_value()

    def set_value(self, val):
        self.counter.value = val

    def check_number_used(self, number):
        return False

    def get_current_value(self):
        return self.counter.value

    def get_next_value(self, current_value=None):
        raise NotImplementedError

    def get_next_number(self):
        next_value = self.get_next_value()
        separator = self.counter.separator if self.counter.separator else ''
        prefix = self.get_prefix(self.counter.prefix, separator)
        return separator.join([prefix, '%d' % (next_value,)])

    def get_date_prefix(self, val):
        val = val.replace('Y', 'y').replace('m', 'M').replace('D', 'd')
        if val.count('y') not in [0, 2, 4] or val.count('M') > 2 or val.count('d') > 2:
            return None
        # qt -> python date format
        _map = {'yyyy': '%Y', 'yy': '%y', 'mm': '%m', 'dd': '%d'}
        try:
            format_ = _map.get(val, '%Y')
            date_val = datetime.date.today().strftime(format_)
            check = datetime.datetime.strptime(date_val, format_)
        except ValueError, e:
            # logger.error(e, exc_info=True)
            return None
        return date_val

    def get_id_prefix(self, val, client_id):
        if val == '':
            return str(client_id)
        ext_val = ClientIdentification.query.join(rbAccountingSystem).filter(
            ClientIdentification.client_id == client_id, rbAccountingSystem.code == val).first()
        return ext_val.identifier if ext_val else None

    def get_prefix(self, prefix, separator):
        """
        формирует префикс
        """
        prefix_types = {'date': self.get_date_prefix, 'id': self.get_id_prefix}

        prefix_parts = prefix.split(';') if prefix else []
        prefix = []
        for p in prefix_parts:
            for t in prefix_types:
                pos = p.find(t)
                if pos == 0:
                    val = p[len(t):]
                    if val.startswith('(') and val.endswith(')'):
                        val = prefix_types[t](val[1:-1])
                        if val:
                            prefix.append(val)
        return separator.join(prefix)

    def cast_str_to_number(self, column):
        re_str_is_number = '^([1-9][0-9]*|0)$'
        return func.IF(
            column.op('regexp')(re_str_is_number),
            cast(column, Integer),
            None
        )


class ContractCounter(Counter):
    code = 'contract'

    def check_number_used(self, number):
        if isinstance(number, str):
            number = number.decode('utf-8')
        elif not isinstance(number, unicode):
            number = unicode(number)
        return Contract.query.join(rbCounter, rbCounter.code == self.code).filter(
            Contract.number == number,
            Contract.deleted == 0,
            or_(rbCounter.resetDate.is_(None),
                Contract.date >= rbCounter.resetDate)
        ).count() > 0

    def get_next_value(self):
        """В текущей реализации номер может состоять только из цифр"""
        # текущий номер по счетчику
        cur_val = self.get_current_value() or 0
        base_query = db.session.query(Contract).join(
            rbCounter, rbCounter.code == self.code
        ).filter(
            Contract.deleted == 0,
            or_(rbCounter.resetDate.is_(None),
                Contract.date >= rbCounter.resetDate),
            self.cast_str_to_number(Contract.number) >= cur_val,
        )

        # следующий минимальный номер
        min_contract_num = base_query.order_by(
            self.cast_str_to_number(Contract.number)
        ).with_entities(self.cast_str_to_number(Contract.number)).first()
        # если есть пропуск после текущего номера (при этом договора на текущий
        # номер нет)
        if min_contract_num is not None and min_contract_num[0] > cur_val + 1:
            next_number = cur_val + 1
        # иначе - найти следующий договор, после которого будет пропуск
        else:
            NContract = aliased(Contract, name='NextContract')
            contract_next = db.session.query(NContract.number).join(
                rbCounter, rbCounter.code == self.code
            ).filter(
                NContract.deleted == 0,
                or_(rbCounter.resetDate.is_(None),
                    NContract.date >= rbCounter.resetDate),
                self.cast_str_to_number(NContract.number) > rbCounter.value
            )

            gap_number = base_query.filter(
                # после целевого договора должен быть пропуск в нумерации
                ~contract_next.filter(
                    self.cast_str_to_number(NContract.number) == self.cast_str_to_number(Contract.number) + 1
                ).exists()
            ).order_by(
                self.cast_str_to_number(Contract.number),
            ).with_entities(
                self.cast_str_to_number(Contract.number) + 1
            ).first()
            # пропущенный номер; если нет, значит текущее значение больше, чем все
            # существующие номера договоров, - взять следующий номер
            gap_number = gap_number[0] if gap_number else cur_val + 1
            next_number = gap_number
        return next_number


class InvoiceCounter(Counter):
    code = 'invoice'

    def check_number_used(self, number):
        return Invoice.query.join(rbCounter, rbCounter.code == self.code).filter(
            Invoice.number == unicode(number),
            Invoice.deleted == 0,
            or_(rbCounter.resetDate.is_(None),
                Invoice.setDate >= rbCounter.resetDate)
        ).count() > 0

    def get_next_value(self):
        """В текущей реализации номер может состоять только из цифр"""
        # текущий номер по счетчику
        cur_val = self.get_current_value() or 0
        base_query = db.session.query(Invoice).join(
            rbCounter, rbCounter.code == self.code
        ).filter(
            Invoice.deleted == 0,
            or_(rbCounter.resetDate.is_(None),
                Invoice.setDate >= rbCounter.resetDate),
            self.cast_str_to_number(Invoice.number) >= cur_val,
        )

        # следующий минимальный номер
        min_invoice_num = base_query.order_by(
            self.cast_str_to_number(Invoice.number)
        ).with_entities(self.cast_str_to_number(Invoice.number)).first()
        # если есть пропуск после текущего номера (при этом счета с текущим
        # номером нет)
        if min_invoice_num is not None and min_invoice_num[0] > cur_val + 1:
            next_number = cur_val + 1
        # иначе - найти следующий счет, после которого будет пропуск
        else:
            NInvoice = aliased(Invoice, name='NextInvoice')
            invoice_next = db.session.query(NInvoice.number).join(
                rbCounter, rbCounter.code == self.code
            ).filter(
                NInvoice.deleted == 0,
                or_(rbCounter.resetDate.is_(None),
                    NInvoice.setDate >= rbCounter.resetDate),
                self.cast_str_to_number(NInvoice.number) > rbCounter.value
            )

            gap_number = base_query.filter(
                # после целевого договора должен быть пропуск в нумерации
                ~invoice_next.filter(
                    self.cast_str_to_number(NInvoice.number) == self.cast_str_to_number(Invoice.number) + 1
                ).exists()
            ).order_by(
                self.cast_str_to_number(Invoice.number),
            ).with_entities(
                self.cast_str_to_number(Invoice.number) + 1
            ).first()
            # пропущенный номер; если нет, значит текущее значение больше, чем все
            # существующие номера счетов, - взять следующий номер
            gap_number = gap_number[0] if gap_number else cur_val + 1
            next_number = gap_number
        return next_number
