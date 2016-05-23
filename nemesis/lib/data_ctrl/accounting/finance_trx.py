# -*- coding: utf-8 -*-

import datetime

from nemesis.models.accounting import (FinanceTransaction, rbFinanceTransactionType, rbPayType,
   Contract_Contragent, Invoice, rbFinanceOperationType)
from nemesis.models.enums import FinanceTransactionType, FinanceOperationType
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_decimal, safe_double, safe_traverse
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController
from .utils import calc_payer_balance


class FinanceTrxController(BaseModelController):

    def __init__(self):
        super(FinanceTrxController, self).__init__()

    def get_new_trx(self, params=None):
        if params is None:
            params = {}
        trx = FinanceTransaction()
        contragent_id = safe_int(params.get('contragent_id'))
        trx.contragent_id = contragent_id
        if contragent_id:
            contragent = self.session.query(Contract_Contragent).get(contragent_id)
            trx.contragent = contragent
        return trx

    def make_trx(self, trx_type, json_data):
        new_trx = self.get_new_trx()
        if trx_type.value == FinanceTransactionType.payer_balance[0]:
            json_data = self._format_trx_payer_balance_data(json_data)
            for attr in ('contragent_id', 'contragent', 'invoice_id', 'invoice', 'payType_id', 'pay_type', 'sum',
                         'trxType_id', 'trx_type', 'financeOperationType_id', 'operation_type', ):
                setattr(new_trx, attr, json_data[attr])
        elif trx_type.value == FinanceTransactionType.invoice[0]:
            json_data = self._format_trx_invoice_data(json_data)
            for attr in ('invoice_id', 'invoice', 'contragent_id', 'contragent', 'sum', 'trxType_id', 'trx_type',
                         'financeOperationType_id', 'operation_type', ):
                setattr(new_trx, attr, json_data[attr])
        else:
            raise ApiException(422, u'Unsupported trx type')
        return new_trx

    def _format_trx_payer_balance_data(self, data):
        contragent_id = safe_int(data.get('contragent_id'))
        if not contragent_id:
            raise ApiException(422, u'`contragent_id` required')
        contragent = self.session.query(Contract_Contragent).get(contragent_id)
        if not contragent:
            raise ApiException(404, u'Не найден плательщик с id={0}'.format(contragent_id))

        if data.get('invoice_id'):
            invoice_id = safe_int(data.get('invoice_id'))
            invoice = self.session.query(Invoice).get(invoice_id)
            if not invoice:
                raise ApiException(404, u'Не найден счёт с id={0}'.format(invoice_id))
        else:
            invoice_id = None
            invoice = None

        pay_type_id = safe_int(safe_traverse(data, 'pay_type', 'id'))
        if not pay_type_id:
            raise ApiException(422, u'`pay_type_id` required')
        pay_type = self.session.query(rbPayType).get(pay_type_id)
        trx_type_id = FinanceTransactionType.payer_balance[0]
        trx_type = self.session.query(rbFinanceTransactionType).get(trx_type_id)
        fin_op_type_id = safe_int(safe_traverse(data, 'finance_operation_type', 'id'))
        fin_op_type = self.session.query(rbFinanceOperationType).get(fin_op_type_id)
        sum_ = safe_decimal(data.get('sum'))

        data['contragent_id'] = contragent_id
        data['contragent'] = contragent
        data['invoice_id'] = invoice_id
        data['invoice'] = invoice
        data['payType_id'] = pay_type_id
        data['pay_type'] = pay_type
        data['trxType_id'] = trx_type_id
        data['trx_type'] = trx_type
        data['financeOperationType_id'] = fin_op_type_id
        data['operation_type'] = fin_op_type
        data['sum'] = sum_
        return data

    def _format_trx_invoice_data(self, data):
        invoice_id = safe_int(data.get('invoice_id'))
        if not invoice_id:
            raise ApiException(422, u'`invoice_id` required')
        invoice = self.session.query(Invoice).get(invoice_id)
        if not invoice:
            raise ApiException(404, u'Не найден счёт с id={0}'.format(invoice_id))
        contragent_id = safe_int(data.get('contragent_id'))
        if not contragent_id:
            raise ApiException(422, u'`contragent_id` required')
        contragent = self.session.query(Contract_Contragent).get(contragent_id)
        if not contragent:
            raise ApiException(404, u'Не найден плательщик с id={0}'.format(contragent_id))
        trx_type_id = FinanceTransactionType.invoice[0]
        trx_type = self.session.query(rbFinanceTransactionType).get(trx_type_id)
        fin_op_type_id = safe_int(safe_traverse(data, 'finance_operation_type', 'id'))
        fin_op_type = self.session.query(rbFinanceOperationType).get(fin_op_type_id)
        sum_ = safe_decimal(data.get('sum'))

        data['invoice_id'] = invoice_id
        data['invoice'] = invoice
        data['contragent_id'] = contragent_id
        data['contragent'] = contragent
        data['trxType_id'] = trx_type_id
        data['trx_type'] = trx_type
        data['financeOperationType_id'] = fin_op_type_id
        data['operation_type'] = fin_op_type
        data['sum'] = sum_
        return data

    def get_new_invoice_trxes(self, params):
        invoice_id = safe_int(params.get('invoice_id'))
        if not invoice_id:
            raise ApiException(422, u'`invoice_id` required')
        invoice = self.session.query(Invoice).get(invoice_id)
        if not invoice:
            raise ApiException(404, u'Не найден счёт с id={0}'.format(invoice_id))
        contragent_id = safe_int(params.get('contragent_id'))
        if not contragent_id:
            raise ApiException(422, u'`contragent_id` required')
        contragent = self.session.query(Contract_Contragent).get(contragent_id)
        if not contragent:
            raise ApiException(404, u'Не найден плательщик с id={0}'.format(contragent_id))
        invoice_sum = invoice.total_sum
        payer_balance = calc_payer_balance(contragent)

        payer_balance_trx = FinanceTransaction()
        payer_balance_trx.contragent_id = contragent_id
        payer_balance_trx.contragent = contragent
        payer_balance_trx.sum = min(abs(payer_balance - invoice_sum), invoice_sum)

        invoice_trx = FinanceTransaction()
        invoice_trx.contragent_id = contragent_id
        invoice_trx.contragent = contragent
        invoice_trx.invoice_id = invoice_id
        invoice_trx.invoice = invoice
        invoice_trx.sum = invoice_sum

        return {
            'payer_balance_trx': payer_balance_trx,
            'invoice_trx': invoice_trx
        }

    def make_invoice_trxes(self, trx_type, json_data):
        with self.session.no_autoflush:
            invoice_trx_data = json_data.get('invoice_trx')
            if not invoice_trx_data:
                raise ApiException(422, u'`invoice_trx` required')
            item_list = []
            new_invoice_trx = self.make_trx(trx_type, invoice_trx_data)
            item_list.append(new_invoice_trx)

            pb_trx_data = json_data.get('payer_balance_trx')
            if pb_trx_data:
                pb_trx_type = FinanceTransactionType(FinanceTransactionType.payer_balance[0])
                pb_trx_data['invoice_id'] = new_invoice_trx.invoice_id
                new_pb_trx = self.make_trx(pb_trx_type, pb_trx_data)
                item_list.append(new_pb_trx)
            else:
                new_pb_trx = None

            payer_balance = calc_payer_balance(new_invoice_trx.contragent)
            invoice_sum = new_invoice_trx.invoice.total_sum
            if payer_balance < invoice_sum:
                if not new_pb_trx:
                    raise ApiException(422, u'Недостаточная сумма на балансе плательщика для оплаты '
                                            u'счёта с id={0}'.format(new_invoice_trx.invoice_id))
                pb_deposit = new_pb_trx.sum
                if (payer_balance + pb_deposit) < invoice_sum:
                    raise ApiException(422, u'Сумма, вносимая на баланс плательщика, недостаточна для оплаты '
                                            u'счёта с id={0}'.format(new_invoice_trx.invoice_id))

            invoice = new_invoice_trx.invoice
            invoice.settleDate = datetime.date.today()
            item_list.append(invoice)
            return item_list

    def get_invoice_finance_operations(self, invoice):
        trx_list = self.session.query(FinanceTransaction).filter(
            FinanceTransaction.invoice_id == invoice.id
        ).all()
        op_list = []
        for trx in trx_list:
            op_sum = trx.sum
            op_type_id = trx.financeOperationType_id
            fo = FinanceOperation(op_type_id, op_sum, trx)
            op_list.append(fo)
        return op_list


class FinanceOperation(object):

    def __init__(self, op_type_id, op_sum, trx):
        self.op_type = FinanceOperationType(op_type_id)
        self.op_sum = abs(op_sum)
        self.trx = trx