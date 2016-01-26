# -*- coding: utf-8 -*-

import datetime

from decimal import Decimal
from sqlalchemy import or_
from sqlalchemy.sql.expression import union, exists, join

from nemesis.models.accounting import Invoice, InvoiceItem, Service, Contract, Contract_Contragent, ServiceDiscount
from nemesis.models.actions import Action
from nemesis.models.enums import FinanceOperationType
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_decimal, safe_double, safe_traverse
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from .service import ServiceController
from .finance_trx import FinanceTrxController
from .utils import calc_invoice_total_sum, calc_invoice_item_sum


class InvoiceController(BaseModelController):

    def __init__(self):
        super(InvoiceController, self).__init__()
        self.item_ctrl = InvoiceItemController()

    @classmethod
    def get_selecter(cls):
        return InvoiceSelecter()

    def get_new_invoice(self, params=None):
        if params is None:
            params = {}
        now = datetime.datetime.now()
        invoice = Invoice()
        contract_id = safe_int(params.get('contract_id'))
        invoice.contract_id = contract_id
        if contract_id:
            contract = self.session.query(Contract).get(contract_id)
            invoice.contract = contract
        invoice.setDate = safe_date(now)
        invoice.deleted = 0

        if 'service_list' in params:
            item_list = []
            for service_data in params['service_list']:
                item_data = self.item_ctrl._format_new_invoice_item_data(service_data)
                item = self.item_ctrl.get_new_invoice_item(item_data)
                item_list.append(item)
            invoice.item_list = item_list
        else:
            invoice.item_list = []
        invoice.total_sum = self.calc_invoice_total_sum(invoice)
        return invoice

    def get_invoice(self, invoice_id):
        return self.get_selecter().get_by_id(invoice_id)

    def update_invoice(self, invoice, json_data):
        json_data = self._format_invoice_data(json_data)
        for attr in ('contract_id', 'contract', 'setDate', 'settleDate', 'number', 'deedNumber', 'note', ):
            if attr in json_data:
                setattr(invoice, attr, json_data.get(attr))
        self.update_invoice_items(invoice, json_data['item_list'])
        invoice.total_sum = self.calc_invoice_total_sum(invoice)
        return invoice

    def delete_invoice(self, invoice):
        invoice.deleted = 1
        return invoice

    def update_invoice_items(self, invoice, item_list_data):
        item_list = []
        for item_d in item_list_data:
            item_id = safe_int(item_d.get('id'))
            if item_id:
                item = self.item_ctrl.get_invoice_item(item_id)
            else:
                item = self.item_ctrl.get_new_invoice_item()
            item = self.item_ctrl.update_invoice_item(item, item_d, invoice)
            item_list.append(item)
        invoice.item_list = item_list

    def _format_invoice_data(self, data):
        contract_id = safe_int(data.get('contract_id'))
        contract = self.session.query(Contract).get(contract_id)
        data['contract_id'] = contract_id
        data['contract'] = contract
        data['setDate'] = safe_date(data['set_date'])
        data['settleDate'] = safe_date(data['settle_date'])
        data['number'] = safe_unicode(data['number'])
        data['deedNumber'] = safe_unicode(data['deed_number'])
        data['note'] = safe_unicode(data['note'])
        return data

    def calc_invoice_total_sum(self, invoice):
        return calc_invoice_total_sum(invoice)

    def search_invoices(self, args):
        selecter = self.get_selecter()
        selecter.apply_filter(**args)
        selecter.apply_sort_order(**args)
        listed_data = selecter.get_all()
        return listed_data

    def get_service_invoice(self, service):
        service_id = service.id
        sel = self.get_selecter()
        invoice_list = sel.get_service_invoice(service_id)
        if len(invoice_list) == 0:
            return None
        elif len(invoice_list) > 1:
            raise ApiException(409, u'Услуга Service с id = {0} находится в нескольких счетах'.format(service_id))
        return invoice_list[0]

    def get_invoice_payment_info(self, invoice):
        trx_ctrl = FinanceTrxController()
        op_list = trx_ctrl.get_invoice_finance_operations(invoice)

        pay_sum = Decimal('0')
        cancel_sum = Decimal('0')
        for op in op_list:
            if op.op_type.value == FinanceOperationType.invoice_pay[0]:
                pay_sum += op.op_sum
            if op.op_type.value == FinanceOperationType.invoice_cancel[0]:
                cancel_sum += op.op_sum
        paid_sum = pay_sum - cancel_sum
        invoice_total_sum = invoice.total_sum
        paid = paid_sum >= invoice_total_sum
        debt_sum = invoice_total_sum - paid_sum
        settle_date = invoice.settleDate
        return {
            'paid': paid,
            'invoice_total_sum': invoice_total_sum,
            'paid_sum': paid_sum,
            'debt_sum': debt_sum,
            'settle_date': settle_date
        }

    def check_event_has_invoice(self, event_id):
        return self.session.query(
            exists().select_from(
                join(Invoice, InvoiceItem, Invoice.id == InvoiceItem.invoice_id).
                    join(Service).join(Action)
            ).where(Invoice.deleted == 0).where(Service.deleted == 0).
                where(Action.event_id == event_id).where(Action.deleted == 0)
        ).scalar()


class InvoiceSelecter(BaseSelecter):

    def __init__(self):
        Invoice = self.model_provider.get('Invoice')
        query = self.model_provider.get_query('Invoice').order_by(Invoice.setDate)
        super(InvoiceSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        Invoice = self.model_provider.get('Invoice')
        InvoiceItem = self.model_provider.get('InvoiceItem')
        Action = self.model_provider.get('Action')
        Service = self.model_provider.get('Service')
        Contract = self.model_provider.get('Contract')
        Contract_Contragent = self.model_provider.get('Contract_Contragent')
        Client = self.model_provider.get('Client')
        Organisation = self.model_provider.get('Organisation')

        if 'event_id' in flt_args:
            event_id = safe_int(flt_args['event_id'])
            self.query = self.query.join(InvoiceItem, Service, Action).filter(
                Action.event_id == event_id,
                Action.deleted == 0,
                Invoice.deleted == 0
            )

        if 'query' in flt_args:
            query = u'%{0}%'.format(flt_args['query'])

            invoice_num_q = self.session.query(Invoice).filter(
                Invoice.number.like(query),
                Invoice.deleted == 0
            )

            payer_individual_q = self.session.query(Invoice).join(
                Contract,
                (Contract_Contragent, Contract.payer_id == Contract_Contragent.id),
                (Client, Contract_Contragent.client_id == Client.id)
            ).filter(or_(
                Client.firstName.like(query),
                Client.lastName.like(query),
                Client.patrName.like(query)
            ),
                Invoice.deleted == 0,
                Contract.deleted == 0,
                Contract_Contragent.deleted == 0
            )

            payer_legal_q = self.session.query(Invoice).join(
                Contract,
                (Contract_Contragent, Contract.payer_id == Contract_Contragent.id),
                (Organisation, Contract_Contragent.organisation_id == Organisation.id)
            ).filter(or_(
                Organisation.shortName.like(query),
                Organisation.fullName.like(query)
            ),
                Invoice.deleted == 0,
                Contract.deleted == 0,
                Contract_Contragent.deleted == 0
            )
            self.query = self.session.query(Invoice).select_entity_from(
                union(invoice_num_q, payer_individual_q, payer_legal_q)
            ).order_by(Invoice.settleDate.is_(None).desc(), Invoice.setDate.desc())
        elif 'payer_id' in flt_args:
            payer_id = safe_int(flt_args['payer_id'])
            self.query = self.session.query(Invoice).join(
                Contract,
                (Contract_Contragent, Contract.payer_id == Contract_Contragent.id)
            ).filter(
                Contract_Contragent.id == payer_id,
                Invoice.deleted == 0,
                Contract.deleted == 0,
                Contract_Contragent.deleted == 0
            ).order_by(Invoice.settleDate.is_(None).desc(), Invoice.setDate.desc())

        return self

    def get_service_invoice(self, service_id):
        Invoice = self.model_provider.get('Invoice')
        InvoiceItem = self.model_provider.get('InvoiceItem')

        self.query = self.query.join(InvoiceItem).filter(
            Invoice.deleted == 0,
            InvoiceItem.deleted == 0,
            InvoiceItem.concreteService_id == service_id
        )
        return self.get_all()


class InvoiceItemController(BaseModelController):

    def __init__(self):
        super(InvoiceItemController, self).__init__()

    def get_new_invoice_item(self, params=None):
        if params is None:
            params = {}
        item = InvoiceItem()
        if 'concreteService_id' in params:
            item.concreteService_id = params['concreteService_id']
        if 'service' in params:
            item.service = params['service']
        if 'discount_id' in params:
            item.discount_id = params['discount_id']
        if 'discount' in params:
            item.discount = params['discount']
        if 'price' in params:
            item.price = params['price']
        if 'amount' in params:
            item.amount = params['amount']
        if 'service' in params and 'amount' in params:
            item.sum = self.calc_invoice_item_sum(item)
        return item

    def get_invoice_item(self, item_id):
        item = self.session.query(InvoiceItem).get(item_id)
        return item

    def update_invoice_item(self, item, json_data, invoice):
        json_data = self._format_invoice_item_data(json_data)
        for attr in ('price', 'amount', 'concreteService_id', 'service', 'discount_id', 'discount', ):
            if attr in json_data:
                setattr(item, attr, json_data.get(attr))
        item.sum = self.calc_invoice_item_sum(item)
        if item.service:
            self.update_invoice_item_service(item, dict(discount_id=json_data.get('discount_id')))
        item.invoice = invoice
        return item

    def update_invoice_item_service(self, invoice_item, data):
        service_ctrl = ServiceController()
        service = service_ctrl.update_service(invoice_item.service, data)
        invoice_item.service = service

    def _format_invoice_item_data(self, data):
        service_id = safe_int(data['service_id'])
        service = self.session.query(Service).get(service_id)
        discount_id = safe_int(safe_traverse(data, 'discount', 'id'))
        discount = self.session.query(ServiceDiscount).get(discount_id) if discount_id else None
        pricelist_price = service.price_list_item.price
        data_price = safe_decimal(data['price'])
        if data_price != pricelist_price:
            raise ApiException(422, u'Цена позиции счета не соответсвует цене по прайсу')

        data['price'] = data_price
        data['amount'] = safe_double(data['amount'])
        data['concreteService_id'] = service_id
        data['service'] = service
        data['discount_id'] = discount_id
        data['discount'] = discount
        return data

    def _format_new_invoice_item_data(self, service_data):
        service_id = safe_int(service_data['service']['id'])
        service = self.session.query(Service).get(service_id)
        discount_id = safe_int(safe_traverse(service_data['service'], 'discount', 'id'))
        discount = self.session.query(ServiceDiscount).get(discount_id) if discount_id else None
        price = service.price_list_item.price
        amount = safe_double(service_data['service']['amount'])
        data = {
            'concreteService_id': service_id,
            'service': service,
            'discount_id': discount_id,
            'discount': discount,
            'price': price,
            'amount': amount,
        }
        return data

    def calc_invoice_item_sum(self, item):
        return calc_invoice_item_sum(item)
