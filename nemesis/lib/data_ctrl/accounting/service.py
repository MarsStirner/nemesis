# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import exists
from sqlalchemy.orm import join

from nemesis.models.accounting import Service, PriceListItem, Invoice, InvoiceItem, ServiceDiscount, rbServiceKind
from nemesis.models.client import Client
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.enums import ServiceKind
from nemesis.lib.utils import safe_int, safe_unicode, safe_double, safe_decimal, safe_traverse, safe_bool, safe_dict
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter, BaseSphinxSearchSelecter
from nemesis.lib.sphinx_search import SearchEventService
from nemesis.lib.data import int_get_atl_dict_all, create_action, update_action, format_action_data
from nemesis.lib.agesex import recordAcceptableEx
from .contract import ContractController
from .pricelist import PriceListItemController
from .utils import calc_item_sum, get_searched_service_kind


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
        params = self._format_service_data(params)
        service = Service()
        service.serviceKind_id = params['serviceKind_id']
        service.service_kind = params['service_kind']
        service.event_id = params['event_id']
        service.event = params['event']
        service.priceListItem_id = params.get('priceListItem_id')
        service.price_list_item = params.get('price_list_item')
        service.amount = safe_double(params.get('amount', 1))
        service.deleted = 0
        service.parent_id = params.get('parent_id')
        service.parent_service = params.get('parent_service')

        self.set_new_service_serviced_entity(service, params.get('serviced_entity_id'))

        service.recalc_sum()

        service.subservice_list = []
        ss_list_params = params['subservice_list']
        if ss_list_params:
            for subservice_params in ss_list_params:
                service.subservice_list.append(self.get_new_service(subservice_params))
        else:
            service.subservice_list = self.get_new_subservices_from_pricelist(service)
        return service

    def set_new_service_serviced_entity(self, service, serviced_entity_id):
        if service.serviceKind_id == ServiceKind.simple_action[0]:
            service.action = self.get_new_service_action(service, serviced_entity_id)
        elif service.serviceKind_id == ServiceKind.group[0]:
            pass
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            service.action = self.get_new_service_action(service, serviced_entity_id)
        elif service.serviceKind_id == ServiceKind.lab_test[0]:
            lab_action = service.parent_service.action
            service.action_property = self.get_new_service_action_property(lab_action, serviced_entity_id)

    def get_new_subservices_from_pricelist(self, service):
        if service.serviceKind_id in (ServiceKind.simple_action[0], ServiceKind.lab_test[0]):
            return []
        elif service.serviceKind_id == ServiceKind.group[0]:
            ss_list = []
            for rbservice in service.price_list_item.service.subservice_list:
                ss_list.append(self.get_new_subservice_action(rbservice, service))
            return ss_list
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            ss_list = []
            for rbservice in service.price_list_item.service.subservice_list:
                ss_list.append(self.get_new_subservice_action_property(rbservice, service))
            return ss_list
        else:
            return []

    def get_new_subservice_action(self, rbservice, parent_service):
        pli_ctrl = PriceListItemController()
        pli_at_list = pli_ctrl.get_available_pli_at_from_rbservice(
            rbservice.id, parent_service.price_list_item.priceList_id
        )
        if len(pli_at_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для подуслуги')
        elif len(pli_at_list) > 1:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для подуслуги')
        pli_id, at_id = pli_at_list[0]
        service_kind = get_searched_service_kind(rbservice.isComplex, False)  # TODO
        new_service = self.get_new_service({
            'service_kind': safe_dict(service_kind),
            'event_id': parent_service.event_id,
            'price_list_item_id': pli_id,
            'parent_service': parent_service,
            'serviced_entity_id': at_id,
        })
        return new_service

    def get_new_subservice_action_property(self, rbservice, parent_service):
        pli_ctrl = PriceListItemController()
        pli_apt_list = pli_ctrl.get_available_pli_apt_from_rbservice(
            rbservice.id,
            parent_service.price_list_item.priceList_id,
            parent_service.event.client_id,
            parent_service.action.actionType_id
        )
        if len(pli_apt_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для подуслуги')
        elif len(pli_apt_list) > 1:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для подуслуги')
        pli_id, apt_id = pli_apt_list[0]
        service_kind = ServiceKind(ServiceKind.lab_test[0])
        new_service = self.get_new_service({
            'service_kind': safe_dict(service_kind),
            'event_id': parent_service.event_id,
            'price_list_item_id': pli_id,
            'parent_service': parent_service,
            'serviced_entity_id': apt_id
        })
        return new_service

    def get_service(self, service_id):
        return self.get_selecter().get_by_id(service_id)

    def update_service(self, service, json_data):
        json_data = self._format_service_data(json_data)
        for attr in ('serviceKind_id', 'service_kind', 'amount', 'priceListItem_id', 'price_list_item',
                     'discount_id', 'discount'):
            if attr in json_data:
                setattr(service, attr, json_data.get(attr))
        return service

    def _format_service_data(self, data):
        service_kind_id = safe_int(
            safe_traverse(data, 'service_kind', 'id') or data.get('service_kind_id')
        )
        if service_kind_id is None:
            raise ApiException(422, u'`service_kind` required')
        if not ServiceKind(service_kind_id).is_valid():
            raise ApiException(422, u'Unknown `service_kind`: {0}'.format(service_kind_id))
        data['serviceKind_id'] = service_kind_id
        data['service_kind'] = self.session.query(rbServiceKind).get(service_kind_id)

        if 'event_id' in data:
            event_id = safe_int(data['event_id'])
            data['event_id'] = event_id
            data['event'] = self.session.query(Event).get(event_id)
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
        if 'parent_id' in data:
            parent_id = safe_int(data['parent_id'])
            data['parent_id'] = parent_id
            data['parent_service'] = self.session.query(Service).get(parent_id)

        if 'serviced_entity_id' in data:
            data['serviced_entity_id'] = self._format_serviced_entity_data(service_kind_id, data['serviced_entity_id'])

        data['subservice_list'] = [
            self._format_service_data(subservice_data)
            for subservice_data in data.get('subservice_list', [])
        ]
        return data

    def _format_serviced_entity_data(self, service_kind_id, data):
        if service_kind_id == ServiceKind.simple_action[0]:
            # should be valid ActionType.id
            return safe_int(data)
        elif service_kind_id == ServiceKind.group[0]:
            return None
        elif service_kind_id == ServiceKind.lab_action[0]:
            # should be valid ActionType.id
            return safe_int(data)
        elif service_kind_id == ServiceKind.lab_test[0]:
            # should be valid ActionPropertyType.id
            return safe_int(data)

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
        data = self._process_search_results(data)
        data = self._filter_mis_action_search_results(data, args)
        return data

    def _process_search_results(self, data):
        for item in data:
            item['service_kind'] = get_searched_service_kind(item['is_complex_service'], item['is_at_lab'])
            item['amount'] = 1
            is_acc_price = safe_bool(item['is_accumulative_price'])
            if is_acc_price:
                item['sum'] = None
            else:
                item['sum'] = safe_decimal(item['price']) * safe_decimal(item['amount'])
        return data

    def _filter_mis_action_search_results(self, data, args):
        client_id = safe_int(args.get('client_id'))
        if not client_id:
            return data
        client = self.session.query(Client).get(client_id)
        client_age = client.age_tuple(datetime.date.today())
        ats_apts = int_get_atl_dict_all()

        matched = []
        for item in data:
            at_id = item['action_type_id']
            if at_id == 0:  # not action_type service
                matched.append(item)
            else:
                at_data = ats_apts.get(at_id)
                if at_data and recordAcceptableEx(client.sexCode, client_age, at_data[6], at_data[5]):
                    matched.append(item)
        return matched

    def get_services_by_event(self, event_id):
        args = {
            'event_id': event_id
        }
        service_list = self.get_listed_data(args)
        return service_list

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

    def get_new_service_action(self, service, serviced_entity_id):
        event_id = service.event_id
        action_type_id = serviced_entity_id
        action = create_action(action_type_id, event_id)
        return action

    def get_new_service_action_property(self, lab_action, serviced_entity_id):
        apt_id = serviced_entity_id
        for prop in lab_action.properties:
            if prop.type_id == apt_id:
                return prop

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

    def get_subservices(self, service):
        if service.serviceKind_id in (ServiceKind.simple_action[0], ServiceKind.lab_test[0]):
            return []
        sel = self.get_selecter()
        ss_list = sel.get_subservices(service.id)
        return ss_list


class ServiceSelecter(BaseSelecter):

    def __init__(self):
        query = self.model_provider.get_query('Service')
        super(ServiceSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        Service = self.model_provider.get('Service')

        if 'event_id' in flt_args:
            event_id = safe_int(flt_args['event_id'])
            self.query = self.query.filter(
                Service.event_id == event_id,
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

    def get_subservices(self, service_id):
        Service = self.model_provider.get('Service')
        self.query = self.query.filter(
            Service.parent_id == service_id,
            Service.deleted == 0
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