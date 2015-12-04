# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import or_
from sqlalchemy.sql.expression import union

from nemesis.models.accounting import Invoice, InvoiceItem, Service, Contract, Contract_Contragent
from nemesis.models.actions import Action
from nemesis.models.client import Client
from nemesis.models.organisation import Organisation
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_decimal, safe_double, safe_traverse
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from .utils import calc_invoice_total_sum, calc_invoice_item_sum


class InvoiceController(BaseModelController):

    def __init__(self):
        super(InvoiceController, self).__init__()
        self.item_ctrl = InvoiceItemController()

    def get_selecter(self):
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
        invoice = self.session.query(Invoice).get(invoice_id)
        invoice.total_sum = self.calc_invoice_total_sum(invoice)
        return invoice

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


class InvoiceSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(Invoice).order_by(Invoice.setDate)
        super(InvoiceSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
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
        for attr in ('price', 'amount', 'concreteService_id', 'service', ):
            if attr in json_data:
                setattr(item, attr, json_data.get(attr))
        item.sum = self.calc_invoice_item_sum(item)
        item.invoice = invoice
        return item

    def _format_invoice_item_data(self, data):
        service_id = safe_int(data['service_id'])
        service = self.session.query(Service).get(service_id)
        pricelist_price = service.price_list_item.price
        data_price = safe_decimal(data['price'])
        if data_price != pricelist_price:
            raise ApiException(422, u'Цена позиции счета не соответсвует цене по прайсу')

        data['price'] = data_price
        data['amount'] = safe_double(data['amount'])
        data['concreteService_id'] = service_id
        data['service'] = service
        return data

    def _format_new_invoice_item_data(self, service_data):
        service_id = safe_int(service_data['service']['id'])
        service = self.session.query(Service).get(service_id)
        price = service.price_list_item.price
        amount = safe_double(service_data['service']['amount'])
        data = {
            'concreteService_id': service_id,
            'service': service,
            'price': price,
            'amount': amount,
        }
        return data

    def calc_invoice_item_sum(self, item):
        return calc_invoice_item_sum(item)