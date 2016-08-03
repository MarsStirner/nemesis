# -*- coding: utf-8 -*-

import datetime
import logging

from decimal import Decimal

from nemesis.lib.types import Undefined
from sqlalchemy import or_
from sqlalchemy.sql.expression import union, exists, join

from nemesis.models.accounting import Invoice, InvoiceItem, Service, Contract, ServiceDiscount
from nemesis.models.actions import Action
from nemesis.models.enums import FinanceOperationType, ServiceKind
from nemesis.lib.counter import InvoiceCounter
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_bool, safe_double, safe_traverse
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from .service import ServiceController
from .finance_trx import FinanceTrxController
from .utils import calc_invoice_total_sum, calc_invoice_item_total_sum


logger = logging.getLogger('simple')


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
        params = self._format_invoice_data(params)
        now = datetime.datetime.now()
        invoice = Invoice()
        invoice.contract_id = params.get('contract_id')
        invoice.contract = params.get('contract')
        invoice.setDate = params.get('set_date') or safe_date(now)
        invoice.settleDate = params.get('settle_date')
        invoice.number = params.get('number')
        invoice.deedNumber = params.get('deedNumber')
        invoice.note = params.get('note')
        invoice.deleted = 0

        if 'service_list' in params:
            item_list = []
            for service in params['service_list']:
                item = self.item_ctrl.get_new_invoice_item({
                    'from_service': service
                })
                item_list.append(item)
            invoice.item_list = item_list
        else:
            invoice.item_list = []
        return invoice

    def get_invoice(self, invoice_id):
        return self.get_selecter().get_by_id(invoice_id)

    def update_invoice(self, invoice, json_data):
        json_data = self._format_invoice_data(json_data)
        for attr in ('contract_id', 'contract', 'setDate', 'settleDate', 'deedNumber', 'note', ):
            if attr in json_data:
                setattr(invoice, attr, json_data.get(attr))

        self.update_invoice_number(invoice, json_data['number'])
        self.update_invoice_items(invoice, json_data['item_list'])
        invoice.total_sum = self.calc_invoice_total_sum(invoice)
        return invoice

    def delete_invoice(self, invoice):
        invoice.deleted = 1
        return invoice

    def update_invoice_number(self, invoice, number):
        if not invoice.id or invoice.number != number:
            invoice_counter = InvoiceCounter("invoice")
            self.check_number_used(number, invoice_counter)
            setattr(invoice, 'number', number)
            if number.isdigit() and int(number) == invoice_counter.counter.value + 1:
                invoice_counter.increment_value()
                self.session.add(invoice_counter.counter)

    def update_invoice_items(self, invoice, item_list_data):
        item_list = []
        for item_d in item_list_data:
            item_id = safe_int(item_d.get('id'))
            if item_id:
                item = self.item_ctrl.get_invoice_item(item_id)
                item = self.item_ctrl.update_invoice_item(item, item_d, invoice)
                self.item_ctrl.update_invoice_item_service(item, item_d)
            else:
                item = self.item_ctrl.get_new_invoice_item(item_d, invoice=invoice)
                self.item_ctrl.update_invoice_item_service(item, item_d)
            item_list.append(item)
        invoice.item_list = item_list

    def _format_invoice_data(self, data):
        if 'contract_id' in data:
            contract_id = safe_int(data.get('contract_id'))
            contract = self.session.query(Contract).get(contract_id)
            data['contract_id'] = contract_id
            data['contract'] = contract
        if 'set_date' in data:
            data['setDate'] = safe_date(data['set_date'])
        if 'settle_date' in data:
            data['settleDate'] = safe_date(data['settle_date'])
        if 'number' in data:
            data['number'] = safe_unicode(data['number'])
        if 'deed_number' in data:
            data['deedNumber'] = safe_unicode(data['deed_number'])
        if 'note' in data:
            data['note'] = safe_unicode(data['note'])
        if 'item_list' in data:
            data['item_list'] = data['item_list']
        if 'service_list' in data:
            data['service_list'] = [
                self.session.query(Service).get(service_id)
                for service_id in data['service_list']
            ]
        if safe_bool(data.get('generate_number', False)):
            inv_counter = InvoiceCounter('invoice')
            data['number'] = inv_counter.get_next_number()
        elif 'number' in data:
            data['number'] = safe_unicode(data['number'])
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

        paid_sum = Decimal('0')
        for op in op_list:
            if op.op_type.value not in (FinanceOperationType.invoice_pay[0], FinanceOperationType.payer_balance_in[0]):
                logger.critical(u'Некорректная транзакция с id = {0} по счёту с id = {1}'.format(op.trx.id, invoice.id))
            if op.op_type.value == FinanceOperationType.invoice_pay[0]:
                paid_sum += op.op_sum
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

    def get_refund_payment_info(self, invoice):
        trx_ctrl = FinanceTrxController()
        op_list = trx_ctrl.get_invoice_finance_operations(invoice)

        refund_sum = Decimal('0')
        for op in op_list:
            if op.op_type.value not in (FinanceOperationType.invoice_cancel[0], FinanceOperationType.payer_balance_out[0]):
                logger.critical(u'Некорректная транзакция с id = {0} по счёту с id = {1}'.format(op.trx.id, invoice.id))
            if op.op_type.value == FinanceOperationType.invoice_cancel[0]:
                refund_sum += op.op_sum
        refund_total_sum = invoice.refund_sum
        refunded = refund_sum >= refund_total_sum
        settle_date = invoice.settleDate
        return {
            'refunded': refunded,
            'refund_total_sum': refund_total_sum,
            'refund_sum': refund_sum,
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

    def check_number_used(self, number, counter):
        same_number = counter.check_number_used(number)
        if same_number:
            raise ApiException(409, u'Невозможно сохранить счет: счет с таким номером уже существует')

    def get_invoice_event(self, invoice):
        sel = self.get_selecter()
        return sel.get_invoice_event(invoice.id)


class InvoiceSelecter(BaseSelecter):

    def __init__(self):
        Invoice = self.model_provider.get('Invoice')
        query = self.model_provider.get_query('Invoice').order_by(Invoice.setDate)
        super(InvoiceSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        Invoice = self.model_provider.get('Invoice')
        InvoiceItem = self.model_provider.get('InvoiceItem')
        Service = self.model_provider.get('Service')
        Contract = self.model_provider.get('Contract')
        Contract_Contragent = self.model_provider.get('Contract_Contragent')
        Client = self.model_provider.get('Client')
        Organisation = self.model_provider.get('Organisation')

        if 'event_id' in flt_args:
            event_id = safe_int(flt_args['event_id'])
            self.query = self.query.join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id).join(Service).filter(
                Service.event_id == event_id,
                Service.deleted == 0,
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
            ).order_by(Invoice.settleDate.is_(None).desc(), Invoice.setDate.desc(), Invoice.id.desc())

        refunds = flt_args.get('refunds', Undefined)
        only_refunds = flt_args.get('only_refunds', Undefined)
        if only_refunds is True:
            self.query = self.query.filter(Invoice.parent_id.isnot(None))
        elif refunds is Undefined or refunds is False:
            self.query = self.query.filter(Invoice.parent_id.is_(None))

        return self

    def get_service_invoice(self, service_id):
        Invoice = self.model_provider.get('Invoice')
        InvoiceItem = self.model_provider.get('InvoiceItem')

        self.query = self.query.join(InvoiceItem, InvoiceItem.invoice_id == Invoice.id).filter(
            Invoice.deleted == 0,
            InvoiceItem.deleted == 0,
            InvoiceItem.concreteService_id == service_id
        )
        return self.get_all()

    def get_invoice_event(self, invoice_id):
        Event = self.model_provider.get('Event')
        InvoiceItem = self.model_provider.get('InvoiceItem')
        Service = self.model_provider.get('Service')

        event_id_q = self.model_provider.get_query('Event').join(
            Service, InvoiceItem
        ).filter(
            Service.deleted == 0,
            InvoiceItem.deleted == 0,
            InvoiceItem.invoice_id == invoice_id
        ).with_entities(Event.id.label('event_id')).subquery()
        self.query = self.model_provider.get_query('Event').join(
            event_id_q, Event.id == event_id_q.c.event_id
        )
        return self.get_one()


class InvoiceItemController(BaseModelController):

    def __init__(self):
        super(InvoiceItemController, self).__init__()

    @classmethod
    def get_selecter(cls):
        return InvoiceItemSelecter()

    def get_new_invoice_item(self, params=None, invoice=None):
        if params is None:
            params = {}
        params = self._format_invoice_item_data(params)
        item = InvoiceItem()
        item.invoice = invoice if invoice is not None else params.get('invoice')
        item.concreteService_id = params.get('concreteService_id')
        item.parent_id = params.get('parent_id')
        item.parent_item = params.get('parent_item')
        item.service = params.get('service')
        item.discount_id = params.get('discount_id')
        item.discount = params.get('discount')
        item.price = params.get('price')
        item.amount = params.get('amount')

        item.subitem_list = []
        si_list_params = params.get('subitem_list')
        if si_list_params is not None:
            for subitem_params in si_list_params:
                subitem_params.update({
                    'parent_item': item
                })
                subitem = self.get_new_invoice_item(subitem_params, invoice)
                item.subitem_list.append(subitem)
        else:
            item.subitem_list = self.get_new_subitems_from_service(item)

        item.sum = self.calc_invoice_item_sum(item)
        return item

    def get_new_subitems_from_service(self, item):
        """Получить экзмепляры подпунктов счета для подуслуг на основе данных корневой услуги."""
        if item.service.serviceKind_id in (ServiceKind.group[0], ServiceKind.lab_action[0]):
            si_list = []
            for service in item.service.subservice_list:
                subitem = self.get_new_invoice_item({
                    'from_service': service,
                    'parent_item': item
                }, invoice=item.invoice)
                si_list.append(subitem)
            return si_list
        else:  # serviceKind_id in (ServiceKind.simple_action[0], ServiceKind.lab_test[0]):
            return []

    def get_invoice_item(self, item_id):
        item = self.session.query(InvoiceItem).get(item_id)
        return item

    def update_invoice_item(self, item, json_data, invoice):
        json_data = self._format_invoice_item_data(json_data)
        for attr in ('price', 'amount', 'concreteService_id', 'service', 'parent_id', 'parent_item',
                     'discount_id', 'discount', ):
            if attr in json_data:
                setattr(item, attr, json_data.get(attr))
        item.invoice = invoice
        item.deleted = json_data.get('deleted', 0) and 1 or 0

        if 'subitem_list' in json_data:
            # traverse subitems
            existing_si_map = dict(
                (si.id, si)
                for si in item.subitem_list
            )
            for si_data in json_data.get('subitem_list'):
                si_id = si_data['id']
                self.update_invoice_item(existing_si_map[si_id], si_data, invoice)

        item.sum = self.calc_invoice_item_sum(item)
        return item

    def update_invoice_item_service(self, invoice_item, item_data):
        service_ctrl = ServiceController()
        if invoice_item.service:
            service = service_ctrl.update_service(invoice_item.service, dict(
                discount_id=item_data.get('discount_id')
            ))
            invoice_item.service = service

        # service_id: invoice_item
        existing_si_map = dict(
            (si.concreteService_id, si)
            for si in invoice_item.subitem_list
        )
        for subitem_data in item_data['subitem_list']:
            item_service_id = subitem_data['service_id']
            if item_service_id:
                subitem = existing_si_map[item_service_id]
                self.update_invoice_item_service(subitem, subitem_data)

        if invoice_item.service:
            service_ctrl.update_service_sum(invoice_item.service)

    def _format_invoice_item_data(self, data):
        if 'from_service' in data:
            return self._format_new_invoice_item_data(data)

        if 'invoice' in data:
            data['invoice'] = data['invoice']

        if 'service_id' in data:
            service_id = safe_int(data.get('service_id'))
            service = self.session.query(Service).get(service_id)
            data['concreteService_id'] = service_id
            data['service'] = service

            pricelist_price = service.price_list_item.price
            data['price'] = pricelist_price

        if 'discount' in data:
            discount_id = safe_int(safe_traverse(data, 'discount', 'id'))
            discount = self.session.query(ServiceDiscount).get(discount_id) if discount_id else None
            data['discount_id'] = discount_id
            data['discount'] = discount

        if 'amount' in data:
            amount = safe_double(data['amount']) or 1
            data['amount'] = amount

        if 'parent_id' in data or 'parent_item' in data:
            parent_id = safe_int(data.get('parent_id'))
            parent_service = data.get('parent_item')
            if parent_id is not None:
                data['parent_id'] = parent_id
                data['parent_item'] = self.session.query(InvoiceItem).get(parent_id)
            elif parent_service is not None:
                data['parent_item'] = parent_service

        if 'subitem_list' in data:
            data['subitem_list'] = data['subitem_list']

        return data

    def _format_new_invoice_item_data(self, data):
        result = {}
        service = data['from_service']
        result['concreteService_id'] = service.id
        result['service'] = service

        result['discount_id'] = service.discount_id
        result['discount'] = service.discount

        pricelist_price = service.price_list_item.price
        result['price'] = pricelist_price
        result['amount'] = service.amount

        if 'invoice' in data:
            result['invoice'] = data['invoice']

        if 'parent_item' in data:
            result['parent_item'] = data['parent_item']

        return result

    def calc_invoice_item_sum(self, item):
        return calc_invoice_item_total_sum(item)

    def get_subitems(self, item):
        if item.service.serviceKind_id in (ServiceKind.simple_action[0], ServiceKind.lab_test[0]):
            return []
        sel = self.get_selecter()
        si_list = sel.get_subitems(item.id)
        return si_list


class InvoiceItemSelecter(BaseSelecter):

    def __init__(self):
        query = self.model_provider.get_query('InvoiceItem')
        super(InvoiceItemSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        return self

    def get_subitems(self, item_id):
        InvoiceItem = self.model_provider.get('InvoiceItem')
        self.query = self.query.filter(
            InvoiceItem.parent_id == item_id,
            InvoiceItem.deleted == 0
        )
        return self.get_all()

