# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import exists
from sqlalchemy.orm import join

from nemesis.models.accounting import Service, PriceListItem, Invoice, InvoiceItem, ServiceDiscount
from nemesis.models.client import Client
from nemesis.models.actions import Action
from nemesis.lib.utils import safe_int, safe_unicode, safe_double, safe_decimal, safe_traverse
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter, BaseSphinxSearchSelecter
from nemesis.lib.sphinx_search import SearchEventService
from nemesis.lib.data import int_get_atl_dict_all, create_action, update_action, format_action_data
from nemesis.lib.agesex import recordAcceptableEx
from .contract import ContractController
from .pricelist import PriceListItemController
from .utils import calc_item_sum


class ServiceController(BaseModelController):
    class DataKind(object):
        abstract = 0
        mis_action = 1

    def __init__(self):
        super(ServiceController, self).__init__()
        self.contract_ctrl = ContractController()

    @classmethod
    def get_selecter(cls):
        return ServiceSelecter()

    def get_new_service(self, params=None):
        if params is None:
            params = {}
        service = Service()
        price_list_item_id = safe_int(params.get('price_list_item_id'))
        service.priceListItem_id = price_list_item_id
        if price_list_item_id:
            service.price_list_item = self.session.query(PriceListItem).get(price_list_item_id)
        amount = safe_double(params.get('amount', 1))
        service.amount = amount
        service.deleted = 0
        return service

    def get_service(self, service_id):
        contract = self.session.query(Service).get(service_id)
        return contract

    def update_service(self, service, json_data):
        json_data = self._format_service_data(json_data)
        for attr in ('amount', 'priceListItem_id', 'price_list_item', 'discount_id', 'discount'):
            if attr in json_data:
                setattr(service, attr, json_data.get(attr))
        return service

    def _format_service_data(self, data):
        if 'amount' in data:
            data['amount'] = safe_double(data['amount'])
        if 'price_list_item_id' in data:
            price_list_item_id = safe_int(data['price_list_item_id'])
            data['priceListItem_id'] = price_list_item_id
            data['price_list_item'] = self.session.query(PriceListItem).get(price_list_item_id)
        if 'discount_id' in data or 'discount' in data:
            if 'discount_id' in data:
                discount_id = safe_int(data.get('discount_id'))
            else:
                discount_id = safe_int(safe_traverse(data, 'discount', 'id'))
            data['discount_id'] = discount_id
            data['discount'] = self.session.query(ServiceDiscount).get(discount_id) if discount_id else None
        return data

    def delete_service(self, service):
        if not self.check_can_delete_service(service):
            raise ApiException(403, u'Невозможно удалить услугу с id = {0}'.format(service.id))
        service.deleted = 1
        if service.action:
            from nemesis.lib.data import delete_action
            try:
                delete_action(service.action)
            except Exception, e:
                raise ApiException(403, unicode(e))
        return service

    def search_mis_action_services(self, args):
        contract_id = safe_int(args.get('contract_id'))
        if not contract_id:
            raise ApiException(422, u'`contract_id` required')
        pricelist_id_list = self.contract_ctrl.get_contract_pricelist_id_list(contract_id)
        service_sphinx = ServiceSphinxSearchSelecter()
        service_sphinx.apply_filter(pricelist_id_list=pricelist_id_list, **args)
        search_result = service_sphinx.get_all()
        data = search_result['result']['items']
        for item in data:
            item['amount'] = 1
            item['sum'] = safe_decimal(item['price']) * safe_decimal(item['amount'])
        data = self._filter_mis_action_search_results(args, data)
        return data

    def _filter_mis_action_search_results(self, args, data):
        client_id = safe_int(args.get('client_id'))
        if not client_id:
            return data
        client = self.session.query(Client).get(client_id)
        client_age = client.age_tuple(datetime.date.today())
        ats_apts = int_get_atl_dict_all()

        matched = []
        for item in data:
            at_id = item['action_type_id']
            at_data = ats_apts.get(at_id)
            if at_data and recordAcceptableEx(client.sexCode, client_age, at_data[6], at_data[5]):
                matched.append(item)
        return matched

    def get_grouped_services_by_event(self, event_id):
        args = {
            'event_id': event_id
        }
        service_list = self.get_listed_data(args)
        grouped = []
        sg_map = {}
        for service in service_list:
            key = u'{0}/{1}'.format(service.price_list_item.service_id, service.action.actionType_id)
            if key not in sg_map:
                sg_map[key] = len(grouped)
                grouped.append({
                    'sg_data': {
                        'service_code': service.price_list_item.serviceCodeOW,
                        'service_name': service.price_list_item.serviceNameOW,
                        'at_name': service.action.actionType.name,
                        'price': service.price_list_item.price,
                        'total_amount': 0,
                        'total_sum': 0
                    },
                    'sg_list': []
                })
            idx = sg_map[key]
            grouped[idx]['sg_list'].append({
                'service': service,
                'action': service.action
            })
            grouped[idx]['sg_data']['total_amount'] += service.amount
            grouped[idx]['sg_data']['total_sum'] += service.sum_
        return {
            'grouped': grouped,
            'sg_map': sg_map
        }

    def get_new_service_action(self, service_data, event_id):
        action_type_id = safe_int(service_data['action']['action_type_id'])
        action = create_action(action_type_id, event_id)
        return action

    def get_service_action(self, action_id):
        contract = self.session.query(Action).get(action_id)
        return contract

    def update_service_action(self, action, json_data):
        # json_data = format_action_data(json_data)
        # action = update_action(action, **json_data)
        # TODO:
        return action

    def save_service_list(self, grouped_service_list, event_id):
        result = []
        for service_group in grouped_service_list:
            for service_data in service_group['sg_list']:
                service_id = service_data['service'].get('id')
                if service_id:
                    service = self.get_service(service_id)
                    action = self.get_service_action(service.action_id)
                else:
                    service = self.get_new_service(service_data['service'])
                    action = self.get_new_service_action(service_data, event_id)
                    service.action = action
                service = self.update_service(service, service_data['service'])
                action = self.update_service_action(action, service_data)
                result.append(service)
                result.append(action)
        return result

    def get_new_service_for_new_action(self, action):
        pli_ctrl = PriceListItemController()
        pli_list = pli_ctrl.get_available_pli_list_for_new_action(action)
        if len(pli_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для создаваемого Action')
        elif len(pli_list) > 1:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для создаваемого Action')
        pli = pli_list[0]
        amount = safe_double(action.amount)
        new_service = self.get_new_service({
            'price_list_item_id': pli.id,
            'amount': amount
        })
        return new_service

    def get_action_service(self, action):
        action_id = action.id
        if not action_id:
            return None
        sel = self.get_selecter()
        service_list = sel.get_action_service(action_id)
        if len(service_list) > 1:
            raise ApiException(409, u'Найдено более одной услуги Service для Action с id = {0}'.format(action_id))
        elif len(service_list) == 0:
            return None
        return service_list[0]

    def check_service_in_invoice(self, service):
        if not service.id:
            return False
        return self.session.query(
            exists().select_from(
                join(Service, InvoiceItem, InvoiceItem.service).join(Invoice)
            ).where(Service.id == service.id).where(Invoice.deleted == 0).where(Service.deleted == 0)
        ).scalar()

    def check_service_is_paid(self, service):
        if not service.id:
            return False
        invoice = service.invoice
        if invoice is None:
            return False
        from .invoice import InvoiceController
        invoice_ctrl = InvoiceController()
        invoice_payment = invoice_ctrl.get_invoice_payment_info(invoice)
        return invoice_payment['paid']

    def check_can_edit_service(self, service):
        return not service.in_invoice

    def check_can_delete_service(self, service):
        return not service.in_invoice

    def get_service_payment_info(self, service):
        if not service.id:
            return False
        invoice = service.invoice
        if invoice is not None:
            from .invoice import InvoiceController
            invoice_ctrl = InvoiceController()
            invoice_payment = invoice_ctrl.get_invoice_payment_info(invoice)
            is_paid = invoice_payment['paid']
        else:
            is_paid = False
        sum_ = service.sum_
        return {
            'sum': sum_,
            'is_paid': is_paid
        }

    def calc_service_sum(self, service, params):
        price = service.price_list_item.price
        new_amount = safe_double(params.get('amount', service.amount))
        discount_id = safe_int(params.get('discount_id'))
        if discount_id:
            discount = self.session.query(ServiceDiscount).get(discount_id)
        else:
            discount = None
        return calc_item_sum(price, new_amount, discount)


class ServiceSelecter(BaseSelecter):

    def __init__(self):
        query = self.model_provider.get_query('Service')
        super(ServiceSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        if 'event_id' in flt_args:
            event_id = safe_int(flt_args['event_id'])
            self.query = self.query.join(Action).filter(
                Action.event_id == event_id,
                Action.deleted == 0,
                Service.deleted == 0
            )
        return self

    def get_action_service(self, action_id):
        # вообще этому место в области экшенов
        Service = self.model_provider.get('Service')
        Action = self.model_provider.get('Action')
        self.query = self.query.join(Action).filter(
            Service.deleted == 0,
            Action.id == action_id,
        )
        return self.get_all()


class ServiceSphinxSearchSelecter(BaseSphinxSearchSelecter):

    def __init__(self):
        search = SearchEventService.get_search()
        super(ServiceSphinxSearchSelecter, self).__init__(search)

    def apply_filter(self, **flt_args):
        if 'query' in flt_args:
            self.search = self.search.match(safe_unicode(flt_args['query']))
        if 'pricelist_id_list' in flt_args:
            id_list = flt_args['pricelist_id_list']
            if not id_list:
                self.search = self.search.filter(pricelist_id__in=[-1])
            else:
                self.search = self.search.filter(pricelist_id__in=id_list)
        return self

    def apply_limit(self, **limit_args):
        self.search = self.search.limit(0, 100)
        return self