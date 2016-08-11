# -*- coding: utf-8 -*-

from decimal import Decimal

from nemesis.models.enums import ContragentType, FinanceTransactionType, FinanceOperationType, ServiceKind
from nemesis.lib.utils import safe_decimal, safe_bool
from nemesis.lib.const import PAID_EVENT_CODE


def get_contragent_type(contragent):
    return ContragentType(
        ContragentType.individual[0] if contragent.client is not None
        else (
            ContragentType.legal[0] if contragent.org is not None
            else ContragentType.undefined[0]
        )
    )


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


def _nullify_subservices_sum(service):
    service.sum = 0
    for ss in service.subservice_list:
        _nullify_subservices_sum(ss)


def calc_service_total_sum(service):
    if not service.price_list_item:
        return None
    if service.price_list_item.service.isComplex:
        if service.price_list_item.isAccumulativePrice:
            # общая сумма вычисляется как сумма всех подуслуг
            return sum(ss.sum for ss in service.subservice_list if ss.deleted == 0)
        else:
            # у услуги фиксированная стоимость; все подуслуги должны иметь пустую сумму
            for ss in service.subservice_list:
                _nullify_subservices_sum(ss)
            return calc_single_service_sum(service)
    else:
        return calc_single_service_sum(service)


def calc_single_service_sum(service):
    price = service.price_list_item.price
    amount = safe_decimal(service.amount)
    discount = service.discount
    return calc_item_sum(price, amount, discount)


def _nullify_subitems_sum(invoice_item):
    invoice_item.sum = 0
    for si in invoice_item.subitem_list:
        _nullify_subitems_sum(si)


def calc_invoice_item_total_sum(invoice_item, ignore_discount=False):
    if not invoice_item.service or not invoice_item.service.price_list_item:
        return None
    if invoice_item.service.price_list_item.service.isComplex:
        if invoice_item.service.price_list_item.isAccumulativePrice:
            # общая сумма вычисляется как сумма всех дочерних позиций
            if ignore_discount:
                # необходимо пересчитать
                return sum(
                    calc_invoice_item_total_sum(si, ignore_discount) for si in invoice_item.subitem_list
                )
            else:
                return sum(si.sum for si in invoice_item.subitem_list)
        else:
            # у услуги фиксированная стоимость; все дочерние позиции должны иметь пустую сумму
            for si in invoice_item.subitem_list:
                _nullify_subitems_sum(si)
            return calc_single_invoice_item_sum(invoice_item, ignore_discount)
    else:
        return calc_single_invoice_item_sum(invoice_item, ignore_discount)


def calc_single_invoice_item_sum(invoice_item, ignore_discount=False):
    price = invoice_item.price
    amount = safe_decimal(invoice_item.amount)
    discount = invoice_item.discount if not ignore_discount else None
    return calc_item_sum(price, amount, discount)


def calc_invoice_total_sum(invoice):
    total_sum = sum(item.sum for item in invoice.item_list)
    return total_sum


def calc_invoice_refund_sum(refund):
    """
    @type refund: nemesis.models.accounting.Invoice
    @param refund:
    @return:
    """
    return sum(item.sum for item in refund.refund_items if not item.service.price_list_item.isAccumulativePrice)


def calc_invoice_sum_wo_discounts(invoice):
    total_sum = sum(
        calc_invoice_item_total_sum(item, ignore_discount=True)
        for item in invoice.item_list
    )
    return total_sum


def calc_invoice_sum_with_refunds(invoice):
    total_sum = invoice.total_sum
    refunds_sum = calc_invoice_refunds_sum(invoice)
    return total_sum - refunds_sum


def calc_invoice_refunds_sum(invoice):
    refunds_sum = Decimal(0)
    for refund in invoice.refunds:
        if check_refund_closed(refund):
            refunds_sum += refund.refund_sum
    return refunds_sum


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


def check_refund_closed(invoice):
    return invoice.settleDate is not None


def check_invoice_can_add_discounts(invoice):
    return invoice.contract.finance.code == PAID_EVENT_CODE


def get_searched_service_kind(service_is_complex, at_is_lab):
    return ServiceKind(
        ServiceKind.lab_action[0] if safe_bool(at_is_lab)
        else (
            ServiceKind.group[0] if safe_bool(service_is_complex)
            else ServiceKind.simple_action[0]
        )
    )