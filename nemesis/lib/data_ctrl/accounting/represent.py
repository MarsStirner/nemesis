# -*- coding: utf-8 -*-

from nemesis.models.enums import Gender, ContragentType
from nemesis.lib.utils import format_date, safe_double, safe_decimal, format_money, safe_bool, safe_traverse
from nemesis.lib.data_ctrl.accounting.utils import (get_contragent_type, check_invoice_closed,
    check_invoice_can_add_discounts, calc_invoice_sum_wo_discounts, calc_invoice_refunds_sum)
from nemesis.lib.data_ctrl.accounting.service import ServiceController
from nemesis.lib.data_ctrl.accounting.contract import ContragentController, ContractController
from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController


class ContractRepr(object):

    def __init__(self):
        self.ca_repr = ContragentRepr()
        self.contingent_repr = ContingentRepr()
        self.pricelist_repr = PriceListRepr()

    def represent_contract_full(self, contract):
        """
        @type contract: nemesis.models.accounting.Contract
        @param contract:
        @return:
        """
        if not contract:
            return None
        data = self.represent_contract(contract)
        data.update({
            'recipient': self.ca_repr.represent_contragent(contract.recipient),
            'payer': self.ca_repr.represent_contragent(contract.payer),
            'contingent_list': [
                self.contingent_repr.represent_contingent(cont)
                for cont in contract.contingent_list
            ],
            'pricelist_list': [
                self.pricelist_repr.represent_pricelist_short(pl)
                for pl in contract.pricelist_list
            ],
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            }
        })
        if not contract.id:
            con_ctrl = ContractController()
            data['last_contract_number'] = con_ctrl.get_last_contract_number()
        return data

    def represent_contract(self, contract):
        """
        @type contract: nemesis.models.accounting.Contract
        @param contract:
        @return:
        """
        return {
            'id': contract.id,
            'number': contract.number,
            'date': contract.date,
            'beg_date': contract.begDate,
            'end_date': contract.endDate,
            'finance': contract.finance,
            'contract_type': contract.contract_type,
            'resolution': contract.resolution,
            'deleted': contract.deleted,
            'draft': contract.draft,
        }

    def represent_contract_with_description(self, contract):
        """
        @type contract: nemesis.models.accounting.Contract
        @param contract:
        @return:
        """
        if not contract:
            return None
        data = self.represent_contract(contract)
        data.update({
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            }
        })
        return data

    def represent_contract_for_invoice(self, contract):
        """
        @type contract: nemesis.models.accounting.Contract
        @param contract:
        @return:
        """
        data = self.represent_contract(contract)
        data.update({
            'description': {
                'full': self.make_full_description(contract),
                'short': self.make_short_description(contract),
            },
            'payer': self.ca_repr.represent_contragent(contract.payer),
        })
        return data

    def make_full_description(self, contract):
        """
        @type contract: nemesis.models.accounting.Contract
        @param contract:
        @return:
        """
        return u'''№{0} от {1}. {2}. с {3} по {4}'''.format(
            contract.number, format_date(contract.date), contract.resolution or '', format_date(contract.begDate),
            format_date(contract.endDate)
        )

    def make_short_description(self, contract):
        """
        @type contract: nemesis.models.accounting.Contract
        @param contract:
        @return:
        """
        return u'№{0} от {1}. {2}'.format(contract.number, format_date(contract.date), contract.resolution or '')

    def represent_paginated_contracts(self, paginated_data):
        """
        @type paginated_data: nemesis.lib.pagination.Pagination
        @param paginated_data:
        @return:
        """
        return {
            'count': paginated_data.total,
            'total_pages': paginated_data.pages,
            'contract_list': [
                self.represent_contract_full(contract) for contract in paginated_data.items
            ]
        }

    def represent_listed_contracts(self, contract_list):
        return [
            self.represent_contract_full(contract) for contract in contract_list
        ]


class ContragentRepr(object):

    def __init__(self):
        self.ca_ctrl = ContragentController()

    def represent_contragent(self, contragent):
        if not contragent:
            return None
        ca_type = get_contragent_type(contragent)
        return {
            'id': contragent.id,
            'client': self.represent_ca_client(contragent.client),
            'org': self.represent_ca_org(contragent.org),
            'ca_type': ca_type,
            'ca_type_code': unicode(ca_type),
            'short_descr': self.make_ca_short_descr(contragent),
            'full_descr': self.make_ca_full_descr(contragent)
        }

    def represent_contragent_payer(self, contragent):
        if not contragent:
            return None
        data = self.represent_contragent(contragent)
        contract_repr = ContractRepr()
        data['contract_list'] = [
            contract_repr.represent_contract_with_description(contract)
            for contract in contragent.payer_contract_list
        ]
        return data

    def represent_contragent_payer_full(self, contragent):
        data = self.represent_contragent(contragent)
        data['balance'] = format_money(self.ca_ctrl.get_payer_balance(contragent))
        return data

    def make_ca_short_descr(self, contragent):
        ca_type = get_contragent_type(contragent)
        if ca_type.value == ContragentType.legal[0]:
            return contragent.org.shortName
        elif ca_type.value == ContragentType.individual[0]:
            return contragent.client.nameText

    def make_ca_full_descr(self, contragent):
        ca_type = get_contragent_type(contragent)
        if ca_type.value == ContragentType.legal[0]:
            return contragent.org.fullName
        elif ca_type.value == ContragentType.individual[0]:
            return u'{0}, {1}, {2}'.format(
                contragent.client.nameText,
                Gender.getName(contragent.client.sex),
                format_date(contragent.client.birthDate)
            )

    def represent_ca_client(self, client):
        if client is None:
            return None
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }

    def represent_ca_org(self, org):
        if org is None:
            return None
        return {
            'id': org.id,
            'short_name': org.shortName,
            'full_name': org.fullName
        }

    def represent_listed_contragents(self, ca_list):
        return [
            self.represent_contragent(contragent) for contragent in ca_list
        ]

    def represent_listed_contragents_payers(self, ca_list):
        return [
            self.represent_contragent_payer(contragent) for contragent in ca_list
        ]


class ContingentRepr(object):

    def represent_contingent(self, contingent):
        return {
            'id': contingent.id,
            'contract_id': contingent.contract_id,
            'client': self.represent_client(contingent.client),
            'deleted': contingent.deleted
        }

    def represent_client(self, client):
        if not client:
            return None
        return {
            'id': client.id,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode),
            'full_name': client.nameText,
        }


class PriceListRepr(object):

    def represent_pricelist(self, pl):
        return {
            'id': pl.id,
            'code': pl.code,
            'name': pl.name,
            'deleted': pl.deleted,
            'finance': pl.finance,
            'beg_date': pl.begDate,
            'end_date': pl.endDate
        }

    def represent_pricelist_short(self, pl):
        data = self.represent_pricelist(pl)
        data['description'] = {
            'short': self.make_short_description(pl),
        }
        return data

    def make_short_description(self, pl):
        return u'{0} ({1}), с {1} по {2}'.format(pl.name, pl.finance.name,
                                                 format_date(pl.begDate), format_date(pl.endDate))

    def represent_listed_pricelists(self, pl_list):
        return [
            self.represent_pricelist_short(pl) for pl in pl_list
        ]


class ServiceRepr(object):

    def represent_mis_action_service_search_result(self, service_data):
        # should be ~ similar to represent_service_full
        return {
            'id': None,
            'price_list_item_id': service_data['price_list_item_id'],
            'service_kind': service_data['service_kind'],
            'event_id': None,
            'parent_id': None,
            'service_id': service_data['service_id'],
            'service_code': service_data['service_code'],
            'service_name': service_data['service_name'],
            'price': format_money(service_data['price']),
            'amount': service_data['amount'],
            'sum': format_money(service_data['sum']),
            'is_accumulative_price': safe_bool(service_data['is_accumulative_price']),
            'is_complex_service': safe_bool(service_data['is_complex_service']),
            'in_invoice': False,
            'is_paid': False,
            'discount': None,
            'access': {
                'can_edit': True,
                'can_delete': True
            },
            'action_type_id': service_data['action_type_id'],
            'at_code': service_data['at_code'],
            'at_name': service_data['at_name'],
            'subservice_list': [],
        }

    def represent_search_result_mis_action_services(self, service_list):
        return [
            self.represent_mis_action_service_search_result(service) for service in service_list
        ]

    def represent_services_by_at(self, at_service_map):
        return dict(
            (at_id, self.represent_mis_action_service_search_result(service_data))
            for at_id, service_data in at_service_map.iteritems()
        )

    def represent_service(self, service):
        return {
            'id': service.id,
            'price_list_item_id': service.priceListItem_id,
            'service_id': service.price_list_item.service_id,
            'service_kind': service.service_kind,
            'event_id': service.event_id,
            'parent_id': service.parent_id,
            'deleted': service.deleted,
            'service_code': service.price_list_item.serviceCodeOW,
            'service_name': service.price_list_item.serviceNameOW,
            'price': service.price_list_item.price,
            'amount': service.amount,
            'is_accumulative_price': safe_bool(service.price_list_item.isAccumulativePrice),
            'discount': ServiceDiscountRepr.represent_discount_short(service.discount),
            'is_complex_service': safe_bool(service.price_list_item.service.isComplex)
        }

    def represent_service_full(self, service, payment=None):
        data = self.represent_service(service)
        data['sum'] = format_money(service.sum)
        data['in_invoice'] = service.in_invoice
        data['pay_status'] = safe_traverse(payment, 'pay_status')
        data['access'] = {
            'can_edit': service.can_edit,
            'can_delete': service.can_delete
        }
        data['serviced_entity'] = service.service_data
        data['subservice_list'] = [
            self.represent_subservice(ss)
            for ss in service.get_sorted_subservices()
        ]
        return data

    def represent_subservice(self, service):
        data = self.represent_service(service)
        data['sum'] = format_money(service.sum)
        data['access'] = {
            'can_edit': service.parent_service.can_edit,
            'can_delete': False
        }
        data['in_invoice'] = service.parent_service.in_invoice
        data['serviced_entity'] = service.service_data
        data['subservice_list'] = [
            self.represent_subservice(ss)
            for ss in service.get_sorted_subservices()
        ]
        return data

    def represent_listed_event_services(self, service_list):
        service_id_list = [service.id for service in service_list]
        ctrl = ServiceController()
        pay_data = ctrl.get_services_pay_info(service_id_list)
        return [
            self.represent_service_full(service, pay_data.get(service.id))
            for service in service_list
        ]

    def represent_paginated_event_services(self, paginated_data):
        service_id_list = [service.id for service in paginated_data.items]
        ctrl = ServiceController()
        pay_data = ctrl.get_services_pay_info(service_id_list)
        return {
            'count': paginated_data.total,
            'total_pages': paginated_data.pages,
            'service_list': [
                self.represent_service_full(service, pay_data.get(service.id))
                for service in paginated_data.items
            ]
        }


class ServiceDiscountRepr(object):

    @staticmethod
    def represent_discount(discount):
        return {
            'id': discount.id,
            'code': discount.code,
            'name': discount.name,
            'deleted': discount.deleted,
            'value_pct': discount.valuePct,
            'value_fixed': discount.valueFixed,
            'beg_date': discount.begDate,
            'end_date': discount.endDate
        }

    @staticmethod
    def represent_discount_short(discount):
        if not discount:
            return None
        data = ServiceDiscountRepr.represent_discount(discount)
        data['description'] = {
            'short': ServiceDiscountRepr.make_short_description(discount),
        }
        return data

    @staticmethod
    def make_short_description(discount):
        return u'{0}'.format(
            u'{0} %'.format(discount.valuePct) if discount.valuePct is not None
            else u'{0}'.format(discount.valueFixed) if discount.valueFixed is not None
            else 'invalid'
        )

    @staticmethod
    def represent_listed_discounts(sd_list):
        return [
            ServiceDiscountRepr.represent_discount_short(discount) for discount in sd_list
        ]


class InvoiceRepr(object):

    def __init__(self):
        self.service_repr = ServiceRepr()

    def represent_invoice_full(self, invoice):
        if not invoice:
            return None
        data = self.represent_invoice(invoice)
        data.update({
            'total_sum': format_money(invoice.total_sum),
            'sum_wo_discounts': format_money(calc_invoice_sum_wo_discounts(invoice)),
            'sum_with_refunds': format_money(invoice.sum_),
            'refunds_sum': format_money(calc_invoice_refunds_sum(invoice)),
            'item_list': [
                self.represent_invoice_item_full(item)
                for item in invoice.item_list
            ],
            'description': {
                'full': self.make_full_description(invoice),
            },
            'closed': check_invoice_closed(invoice),
            'payment': self.represent_invoice_payment(invoice),
            'can_add_discounts': check_invoice_can_add_discounts(invoice),
            'coordinated_refund': self.represent_refund(invoice.coordinated_refund),
            'refund_list': [
                self.represent_refund(refund)
                for refund in invoice.refunds
            ]
        })
        return data

    def represent_refund(self, refund):
        """
        @type refund: nemesis.models.accounting.Invoice
        @param refund:
        @return:
        """
        if not refund:
            return None
        data = self.represent_invoice(refund)
        data.update({
            'item_list': map(self.represent_invoice_item_full, refund.refund_items),
            'payment': self.represent_refund_payment(refund),
        })
        return data

    def represent_invoice_for_payment(self, invoice):
        data = self.represent_invoice(invoice)
        inv_ctrl = InvoiceController()
        cont_repr = ContractRepr()
        event = inv_ctrl.get_invoice_event(invoice)
        data.update({
            'event_id': event.id if event else None,
            'total_sum': format_money(invoice.total_sum),
            'sum_with_refunds': format_money(invoice.sum_),
            'contract': cont_repr.represent_contract_for_invoice(invoice.contract),
            'description': {
                'full': self.make_full_description(invoice),
            },
            'closed': check_invoice_closed(invoice),
            'coordinated_refund': self.represent_refund(invoice.coordinated_refund),
            'refund_list': [
                self.represent_refund(refund)
                for refund in invoice.refunds
            ]
        })
        return data

    def represent_invoice_for_event(self, invoice):
        data = self.represent_invoice(invoice)
        refunds_sum = calc_invoice_refunds_sum(invoice)
        data.update({
            'description': {
                'full': self.make_full_description(invoice),
            },
            'payment': self.represent_invoice_payment(invoice),
            'has_refunds': refunds_sum != 0,
            'refunds_sum': format_money(refunds_sum)
        })
        return data

    def represent_invoice(self, invoice):
        return {
            'id': invoice.id,
            'contract_id': invoice.contract_id,
            'set_date': invoice.setDate,
            'settle_date': invoice.settleDate,
            'number': invoice.number,
            'deed_number': invoice.deedNumber,
            'deleted': invoice.deleted,
            'note': invoice.note,
            'draft': invoice.draft,
        }

    def make_full_description(self, invoice):
        return u'''\
№{0} от {1}.{2}'''.format(
            invoice.number or '',
            format_date(invoice.setDate),
            u' Дата погашения {0}.'.format(format_date(invoice.settleDate)) if invoice.settleDate else u''
        )

    def represent_invoice_payment(self, invoice):
        invoice_ctrl = InvoiceController()
        pay_info = invoice_ctrl.get_invoice_payment_info(invoice)
        pay_info['invoice_total_sum'] = format_money(pay_info['invoice_total_sum'])
        pay_info['paid_sum'] = format_money(pay_info['paid_sum'])
        pay_info['debt_sum'] = format_money(pay_info['debt_sum'])
        return pay_info

    def represent_refund_payment(self, refund):
        invoice_ctrl = InvoiceController()
        pay_info = invoice_ctrl.get_refund_payment_info(refund)
        pay_info['refund_total_sum'] = format_money(pay_info['refund_total_sum'])
        pay_info['refund_sum'] = format_money(pay_info['refund_sum'])
        return pay_info

    def represent_invoice_item_full(self, item):
        data = self.represent_invoice_item(item)
        data['subitem_list'] = [
            self.represent_invoice_item_full(si)
            for si in item.subitem_list
        ]
        return data

    def represent_invoice_item(self, item):
        """
        @type item: nemesis.models.accounting.InvoiceItem
        @param item:
        @return:
        """
        return {
            'id': item.id,
            'invoice_id': item.invoice_id,
            'service_id': item.concreteService_id,
            'service': self.service_repr.represent_service(item.service),
            'discount_id': item.discount_id,
            'discount': ServiceDiscountRepr.represent_discount_short(item.discount),
            'price': format_money(item.price),
            'amount': item.amount,
            'sum': format_money(item.sum),
            'deleted': item.deleted,
            'refund_id': item.refund_id,
        }

    def represent_listed_invoices(self, invoice_list):
        return [
            self.represent_invoice_full(invoice) for invoice in invoice_list
        ]

    def represent_listed_invoices_for_payment(self, invoice_list):
        return [
            self.represent_invoice_for_payment(invoice) for invoice in invoice_list
        ]

    def represent_listed_invoices_for_event(self, invoice_list):
        return [
            self.represent_invoice_for_event(invoice) for invoice in invoice_list
        ]


class FinanceTrxRepr(object):

    @staticmethod
    def represent_finance_trx(trx):
        return {
            'id': trx.id,
            'trx_datetime': trx.trxDatetime,
            'trx_type': trx.trx_type,
            'contragent_id': trx.contragent_id,
            'invoice_id': trx.invoice_id,
            'pay_type': trx.pay_type,
            'sum': trx.sum
        }

    @staticmethod
    def represent_finance_trx_invoice(trxes):
        return {
            'payer_balance_trx': FinanceTrxRepr.represent_finance_trx(trxes['payer_balance_trx']),
            'invoice_trx': FinanceTrxRepr.represent_finance_trx(trxes['invoice_trx'])
        }