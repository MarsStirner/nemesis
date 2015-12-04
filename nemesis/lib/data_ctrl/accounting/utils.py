# -*- coding: utf-8 -*-

from nemesis.models.enums import ContragentType, FinanceTransactionType
from nemesis.lib.utils import safe_decimal


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


def calc_invoice_item_sum(invoice_item):
    price = invoice_item.service.price_list_item.price
    amount = safe_decimal(invoice_item.amount)
    sum_ = price * amount
    return sum_


def calc_invoice_total_sum(invoice):
    total_sum = sum(item.sum for item in invoice.item_list)
    return total_sum


def calc_payer_balance(payer):
    return sum(trx.sum for trx in payer.payer_finance_trx_list)


def get_finance_trx_type(trx_type_code):
    trx_type_id = FinanceTransactionType.getId(trx_type_code)
    if trx_type_id is None:
        return None
    return FinanceTransactionType(trx_type_id)


def check_invoice_closed(invoice):
    return invoice.settleDate is not None