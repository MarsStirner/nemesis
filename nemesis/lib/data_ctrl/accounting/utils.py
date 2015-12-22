# -*- coding: utf-8 -*-

from decimal import Decimal

from nemesis.models.enums import ContragentType, FinanceTransactionType, FinanceOperationType
from nemesis.lib.utils import safe_decimal
from nemesis.lib.const import PAID_EVENT_CODE
from nemesis.lib.data_ctrl.model_provider import ApplicationModelProvider


def get_contragent_type(contragent):
    return ContragentType(
        ContragentType.individual[0] if contragent.client is not None
        else (
            ContragentType.legal[0] if contragent.org is not None
            else ContragentType.undefined[0]
        )
    )


def check_contract_type_with_insurance_policy(contract):
    pass


def calc_item_sum(price, amount, discount=None):
    if discount is not None:
        if discount.valuePct is not None:
            discounted_value = price * safe_decimal(discount.valuePct) / safe_decimal('100')
        elif discount.valueFixed is not None:
            discounted_value = max(price - safe_decimal(discount.valueFixed), 0)
        else:
            raise ValueError('Invalid discount value')
        price -= discounted_value
    amount = safe_decimal(amount)
    return price * amount


def calc_service_sum(service):
    price = service.price_list_item.price
    amount = safe_decimal(service.amount)
    discount = service.discount
    return calc_item_sum(price, amount, discount)


def calc_invoice_item_sum(invoice_item):
    price = invoice_item.service.price_list_item.price
    amount = safe_decimal(invoice_item.amount)
    discount = invoice_item.discount
    return calc_item_sum(price, amount, discount)


def calc_invoice_total_sum(invoice):
    total_sum = sum(item.sum for item in invoice.item_list)
    return total_sum


def calc_invoice_sum_wo_discounts(invoice):
    total_sum = sum(
        calc_item_sum(item.service.price_list_item.price, safe_decimal(item.amount))
        for item in invoice.item_list
    )
    return total_sum


def calc_payer_balance(payer):
    balance = Decimal('0')
    for trx in payer.payer_finance_trx_list:
        if trx.financeOperationType_id in (FinanceOperationType.payer_balance_in[0],
                                           FinanceOperationType.invoice_cancel[0]):
            balance += trx.sum
        elif trx.financeOperationType_id in (FinanceOperationType.payer_balance_out[0],
                                             FinanceOperationType.invoice_pay[0]):
            balance -= trx.sum
    return balance


def get_finance_trx_type(trx_type_code):
    trx_type_id = FinanceTransactionType.getId(trx_type_code)
    if trx_type_id is None:
        return None
    return FinanceTransactionType(trx_type_id)


def check_invoice_closed(invoice):
    return invoice.settleDate is not None


def check_invoice_can_add_discounts(invoice):
    return invoice.contract.finance.code == PAID_EVENT_CODE
