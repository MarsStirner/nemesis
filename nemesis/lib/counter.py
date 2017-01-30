# -*- coding: utf-8 -*-
__author__ = 'plakrisenko'
import datetime
from sqlalchemy import func, or_

from nemesis.lib.utils import safe_int
from nemesis.models.client import ClientIdentification
from nemesis.models.exists import rbCounter, rbAccountingSystem
from nemesis.models.accounting import Contract, Invoice


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

    def get_next_value(self, current_value=None):
        if current_value is None:
            current_value = self.counter.value
        while 1:
            next_value = current_value + 1
            if not self.check_number_used(next_value):
                return next_value
            current_value = next_value

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


class ContractCounter(Counter):
    code = 'contract'

    def check_number_used(self, number):
        if isinstance(number, str):
            number = number.decode('utf-8')
        elif not isinstance(number, unicode):
            number = unicode(number)
        return Contract.query.filter(Contract.number == number, Contract.deleted == 0).count() > 0

    def get_next_number(self):
        """В текущей реализации номер может состоять только из цифр"""
        n = super(ContractCounter, self).get_next_number()
        return n if n.isdigit() else None


class InvoiceCounter(Counter):
    code = 'invoice'

    def check_number_used(self, number):
        return Invoice.query.join(rbCounter, rbCounter.code == self.code).filter(
            Invoice.number == unicode(number),
            Invoice.deleted == 0,
            or_(rbCounter.resetDate.is_(None),
                Invoice.setDate >= rbCounter.resetDate)
        ).count() > 0

    def get_next_number(self):
        """В текущей реализации номер может состоять только из цифр"""
        n = super(InvoiceCounter, self).get_next_number()
        return n if n.isdigit() else None