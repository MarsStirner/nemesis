# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.orm import joinedload, aliased
from sqlalchemy import and_, exists, func
from sqlalchemy.sql.expression import label

from nemesis.models.accounting import Service, PriceListItem, Invoice, InvoiceItem, ServiceDiscount, rbServiceKind
from nemesis.models.client import Client
from nemesis.models.actions import Action
from nemesis.models.event import Event
from nemesis.models.enums import ServiceKind, FinanceOperationType, ActionPayStatus
from nemesis.lib.utils import (safe_int, safe_unicode, safe_double, safe_decimal, safe_traverse, safe_bool, safe_dict,
    safe_traverse_attrs, safe_datetime)
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter, BaseSphinxSearchSelecter
from nemesis.lib.sphinx_search import SearchEventService
from nemesis.lib.data import (int_get_atl_dict_all, create_action, get_assignable_apts, get_planned_end_datetime,
    update_action, delete_action, fit_planned_end_date, create_new_action_ttjs, get_at_tissue_type_ids)
from nemesis.lib.agesex import recordAcceptableEx
from .pricelist import PriceListItemController, PriceListController
from .utils import calc_item_sum, get_searched_service_kind, calc_service_total_sum
from nemesis.lib.action.utils import at_is_lab
from nemesis.lib.const import PAID_EVENT_CODE


class ServiceController(BaseModelController):

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
        service.amount = safe_double(params.get('amount')) or 1
        service.deleted = 0
        service.parent_id = params.get('parent_id')
        service.parent_service = params.get('parent_service')

        self._process_serviced_entity(service, params)

        service.subservice_list = []
        ss_list_params = params.get('subservice_list')
        no_subservices = params.get('no_subservices', False)
        if ss_list_params is not None:
            for subservice_params in ss_list_params:
                subservice_params.update({
                    'parent_service': service
                })
                subservice = self.get_new_service(subservice_params)
                service.subservice_list.append(subservice)
        elif not no_subservices:
            service.subservice_list = self.get_new_subservices_from_pricelist(service)

        service.sum = calc_service_total_sum(service) if service.priceListItem_id else 0

        return service

    def _process_serviced_entity(self, service, params):
        if 'serviced_entity_from_search' in params:
            search_item = params['serviced_entity_from_search']
            se_data = self.make_new_serviced_entity_data(
                service.serviceKind_id,
                code=search_item.get('at_code'),
                name=search_item.get('at_name'),
                at_id=search_item.get('action_type_id'),
                client_id=safe_traverse_attrs(service, 'event', 'client_id'),
                contract_id=safe_traverse_attrs(service, 'event', 'contract_id'),
                event=safe_traverse_attrs(service, 'event'),
                no_subservices=search_item.get('no_subservices')
            )
            self.set_new_service_serviced_entity(service, se_data)
        elif 'serviced_entity_from_action' in params:
            action = params['serviced_entity_from_action']
            service.action = action
        elif 'serviced_entity' in params:
            se_data = params['serviced_entity']
            self.set_new_service_serviced_entity(service, se_data)

    def set_new_service_serviced_entity(self, service, serviced_entity_data):
        if service.serviceKind_id == ServiceKind.simple_action[0]:
            service.action = self.get_new_service_action(service, serviced_entity_data)
        elif service.serviceKind_id == ServiceKind.group[0]:
            pass
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            service.action = self.get_new_service_action(service, serviced_entity_data)
        elif service.serviceKind_id == ServiceKind.lab_test[0]:
            lab_action = service.parent_service.action
            service.action_property = self.get_new_service_action_property(lab_action, serviced_entity_data)

    def get_new_subservices_from_pricelist(self, service):
        """Получить экзмепляры подсервисов на основе данных подуслуг"""
        if service.serviceKind_id == ServiceKind.group[0]:
            # в случае группы услуг подуслугами может быть либо новая группа услуг,
            # либо простая услуга-экшен или лабораторная услуга
            ss_list = []
            for rbservicegroup_assoc in service.price_list_item.service.subservice_assoc:
                sk_id = rbservicegroup_assoc.serviceKind_id
                if sk_id == ServiceKind.group[0]:
                    subservice = self._get_new_subservice_group(rbservicegroup_assoc.subservice, service)
                    ss_list.append(subservice)
                elif sk_id in (ServiceKind.simple_action[0], ServiceKind.lab_action[0]):
                    subservice = self._get_new_subservice_action(rbservicegroup_assoc.subservice, service)
                    ss_list.append(subservice)

            return ss_list
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            # в случае лабораторной услуги подуслугами могут быть только показатели исследования
            ss_list = []
            for rbservicegroup_assoc in service.price_list_item.service.subservice_assoc:
                ss_list.append(self._get_new_subservice_action_property(rbservicegroup_assoc.subservice, service))
            return ss_list
        else:  # service.serviceKind_id in (ServiceKind.simple_action[0], ServiceKind.lab_test[0]):
            # В остальных случаях - простая услуга-экшен или показатель исследования - подуслуг быть не может
            return []

    def _get_new_subservice_action(self, rbservice, parent_service):
        pli_ctrl = PriceListItemController()
        pli_at_list = pli_ctrl.get_available_pli_at_from_rbservice(
            rbservice.id, parent_service.price_list_item.priceList_id
        )
        if len(pli_at_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для подуслуги {0} ({1})'.format(
                rbservice.name, rbservice.id
            ))
        # TODO: одной услуге может соответствовать несколько возможных AT;
        # добавить обработку таких случаев и выбор подходящего ТД клиентом + использовать состояние валидности
        # группы услуг
        elif len(pli_at_list) > 1 and False:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для подуслуги {0} ({1})'.format(
                rbservice.name, rbservice.id
            ))
        pli_id, at_id = pli_at_list[0]
        is_lab = at_is_lab(at_id)
        client_id = parent_service.event.client_id
        service_kind = get_searched_service_kind(rbservice.isComplex, is_lab)
        new_service = self.get_new_service({
            'service_kind': safe_dict(service_kind),
            'event_id': parent_service.event_id,
            'price_list_item_id': pli_id,
            'parent_service': parent_service,
            'serviced_entity': self.make_new_serviced_entity_data(
                service_kind.value,
                at_id=at_id,
                client_id=client_id,
                contract_id=parent_service.event.contract_id,
                event=parent_service.event
            ),
        })
        return new_service

    def _get_new_subservice_action_property(self, rbservice, parent_service):
        pli_ctrl = PriceListItemController()
        pli_apt_list = pli_ctrl.get_available_pli_apt_from_rbservice(
            rbservice.id,
            parent_service.price_list_item.priceList_id,
            parent_service.event.client_id,
            parent_service.action.actionType_id
        )
        if len(pli_apt_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для подуслуги {0} ({1})'.format(
                rbservice.name, rbservice.id
            ))
        elif len(pli_apt_list) > 1:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для подуслуги {0} ({1})'.format(
                rbservice.name, rbservice.id
            ))
        pli_id, apt_id = pli_apt_list[0]
        service_kind = ServiceKind(ServiceKind.lab_test[0])
        new_service = self.get_new_service({
            'service_kind': safe_dict(service_kind),
            'event_id': parent_service.event_id,
            'price_list_item_id': pli_id,
            'parent_service': parent_service,
            'serviced_entity': self.make_new_serviced_entity_data(service_kind.value, apt_id=apt_id),
        })
        return new_service

    def _get_new_subservice_group(self, rbservice, parent_service):
        pli_ctrl = PriceListItemController()
        pli_list = pli_ctrl.get_available_pli_for_groupservice_from_rbservice(
            rbservice.id, parent_service.price_list_item.priceList_id
        )
        if len(pli_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для подуслуги {0}'.format(
                rbservice.name
            ))
        elif len(pli_list) > 1:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для подуслуги {0}'.format(
                rbservice.name
            ))
        pli_id = pli_list[0][0]
        service_kind = ServiceKind(ServiceKind.group[0])
        new_service = self.get_new_service({
            'service_kind': safe_dict(service_kind),
            'event_id': parent_service.event_id,
            'price_list_item_id': pli_id,
            'parent_service': parent_service,
            'serviced_entity': self.make_new_serviced_entity_data(service_kind.value),
        })
        return new_service

    def _format_service_data(self, data):
        result = {}

        if 'service_kind' in data or 'service_kind_id' in data:
            service_kind_id = safe_int(
                safe_traverse(data, 'service_kind', 'id') or data.get('service_kind_id')
            )
            if service_kind_id is not None and not ServiceKind(service_kind_id).is_valid():
                raise ApiException(422, u'Unknown `service_kind`: {0}'.format(service_kind_id))
            result['serviceKind_id'] = service_kind_id
            result['service_kind'] = self.session.query(rbServiceKind).get(service_kind_id)

        if 'event_id' in data:
            event_id = safe_int(data['event_id'])
            result['event_id'] = event_id
            result['event'] = self.session.query(Event).get(event_id) if event_id else None
        if 'amount' in data:
            result['amount'] = safe_double(data['amount'])
        if 'price_list_item_id' in data:
            price_list_item_id = safe_int(data['price_list_item_id'])
            result['priceListItem_id'] = price_list_item_id
            result['price_list_item'] = self.session.query(PriceListItem).get(price_list_item_id)
        if 'discount_id' in data or 'discount' in data:
            if 'discount_id' in data:
                discount_id = safe_int(data.get('discount_id'))
            else:
                discount_id = safe_int(safe_traverse(data, 'discount', 'id'))
            result['discount_id'] = discount_id
            result['discount'] = self.session.query(ServiceDiscount).get(discount_id) if discount_id else None

        if 'parent_id' in data or 'parent_service' in data:
            parent_id = safe_int(data.get('parent_id'))
            parent_service = data.get('parent_service')
            if parent_id is not None:
                result['parent_id'] = parent_id
                result['parent_service'] = self.session.query(Service).get(parent_id)
            elif parent_service is not None:
                result['parent_service'] = parent_service

        if 'serviced_entity_from_search' in data:
            result['serviced_entity_from_search'] = data['serviced_entity_from_search']
        elif 'serviced_entity_from_action' in data:
            result['serviced_entity_from_action'] = data['serviced_entity_from_action']
        elif 'serviced_entity' in data:
            result['serviced_entity'] = data['serviced_entity']

        if 'subservice_list' in data:
            # дефолтное должно быть None для корректного поведения в get_new_service
            result['subservice_list'] = data.get('subservice_list')

        if 'no_subservices' in data:
            result['no_subservices'] = safe_bool(data['no_subservices'])
        return result

    def _format_serviced_entity_data(self, service_kind_id, data):
        if service_kind_id == ServiceKind.simple_action[0]:
            fields = ['id', 'code', 'name', 'at_id']
            return dict((k, data[k]) for k in fields)
        elif service_kind_id == ServiceKind.group[0]:
            return {
                'id': None,
                'code': '',
                'name': ''
            }
        elif service_kind_id == ServiceKind.lab_action[0]:
            fields = ['id', 'code', 'name', 'at_id', 'tests_data']
            return dict((k, data[k]) for k in fields)
        elif service_kind_id == ServiceKind.lab_test[0]:
            fields = ['id', 'code', 'name', 'apt_id', 'action_id']
            return dict((k, data[k]) for k in fields)

    def search_mis_action_services(self, args):
        contract_id = safe_int(args.get('contract_id'))
        if not contract_id:
            raise ApiException(422, u'`contract_id` required')
        pl_ctrl = PriceListController()
        pricelist_id_list = pl_ctrl.get_contract_pricelist_id_list(contract_id)
        service_sphinx = ServiceSphinxSearchSelecter()
        service_sphinx.apply_filter(pricelist_id_list=pricelist_id_list, **args)
        service_sphinx.apply_limit(limit_max=safe_int(args.get('limit_max')))
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
        service_list = self.get_selecter().get_event_services(event_id)
        return service_list

    def get_paginated_services_by_event(self, event_id, page, per_page):
        res = self.get_selecter().get_event_services(event_id, page, per_page)
        return res

    def get_new_service_action(self, service, serviced_entity_data):
        event_id = service.event_id
        action_type_id = serviced_entity_data['at_id']
        if 'tests_data' in serviced_entity_data:
            assigned = serviced_entity_data['tests_data']['assigned']
            data = {
                'plannedEndDate': safe_datetime(serviced_entity_data['tests_data']['planned_end_date'])
            }
        else:
            assigned = data = None
        action = create_action(action_type_id, event_id, assigned=assigned, data=data)

        if 'tests_data' in serviced_entity_data:
            # на основе данных прайс-листа следующие apt имеют цены
            apt_prices = {apt_data[0]: apt_data[2] for apt_data in serviced_entity_data['tests_data']['assignable']}
            assignable_by_pricelist = apt_prices.keys()
            for prop in action.properties:
                if prop.type_id in assignable_by_pricelist:
                    prop.has_pricelist_service = True
                    prop.pl_price = apt_prices[prop.type_id]
        return action

    def get_new_service_action_property(self, lab_action, serviced_entity_data):
        apt_id = serviced_entity_data['apt_id']
        for prop in lab_action.properties:
            if prop.type_id == apt_id:
                return prop

    def make_new_serviced_entity_data(self, service_kind_id, **kwargs):
        if service_kind_id == ServiceKind.simple_action[0]:
            return {
                'id': None,
                'code': kwargs.get('at_code'),
                'name': kwargs.get('at_name'),
                'at_id': kwargs.get('at_id')
            }
        elif service_kind_id == ServiceKind.group[0]:
            return {
                'id': None,
                'code': '',
                'name': ''
            }
        elif service_kind_id == ServiceKind.lab_action[0]:
            at_id = kwargs['at_id']
            assignable = get_assignable_apts(at_id, kwargs.get('client_id'))

            # фильтр доступных показателей по наличию услуги в прайс-листе
            contract_id = kwargs.get('contract_id')
            if contract_id:
                assignable_apt_ids = [apt_data[0] for apt_data in assignable]
                pli_ctrl = PriceListItemController()
                filtered_apt_prices = pli_ctrl.get_apts_prices_by_pricelist(assignable_apt_ids, contract_id)
                flt_assignable = []
                flt_apt_ids = filtered_apt_prices.keys()
                for apt_data in assignable:
                    if apt_data[0] in flt_apt_ids:
                        apt_data = list(apt_data)[:2]
                        apt_data.append(filtered_apt_prices[apt_data[0]])
                        flt_assignable.append(apt_data)
                    else:
                        # без услуги и цены
                        apt_data = list(apt_data)[:2]
                        apt_data.append(None)
                        flt_assignable.append(apt_data)
                assignable = flt_assignable

            no_subservices = kwargs.get('no_subservices', False)
            # apt.id list
            assigned = [apt_data[0] for apt_data in assignable] if not no_subservices else []

            tissue_type_ids = get_at_tissue_type_ids(at_id)
            selected_tissue_type = tissue_type_ids[0] if tissue_type_ids else None
            tissue_type_visible = True

            if 'event' in kwargs:
                event = kwargs['event']
                planned_end_date = get_planned_end_datetime(at_id)
                planned_end_date = fit_planned_end_date(planned_end_date, event)
            else:
                planned_end_date = None
            ped_disabled = False
            return {
                'id': None,
                'code': kwargs.get('code'),
                'name': kwargs.get('name'),
                'at_id': at_id,
                'tests_data': {
                    'assignable': assignable,
                    'assigned': assigned,
                    'planned_end_date': planned_end_date,
                    'ped_disabled': ped_disabled,

                    'available_tissue_types': tissue_type_ids,
                    'selected_tissue_type': selected_tissue_type,
                    'tissue_type_visible': tissue_type_visible
                }
            }
        elif service_kind_id == ServiceKind.lab_test[0]:
            return {
                'id': None,
                'code': kwargs.get('code'),
                'name': kwargs.get('name'),
                'apt_id': kwargs.get('apt_id'),
                'action_id': None
            }

    def get_service(self, service_id, full_load=False):
        if full_load:
            return self.get_selecter().get_service(service_id)
        else:
            return self.get_selecter().get_by_id(service_id)

    def update_service(self, service, json_data):
        json_data = self._format_service_data(json_data)
        for attr in ('serviceKind_id', 'service_kind', 'event_id', 'event', 'amount',
                     'priceListItem_id', 'price_list_item', 'parent_id', 'parent_service',
                     'discount_id', 'discount'):
            if attr in json_data:
                setattr(service, attr, json_data.get(attr))

        if 'subservice_list' in json_data:
            # traverse subservices
            existing_ss_map = dict(
                (ss.id, ss)
                for ss in service.subservice_list
            )
            for ss_data in json_data.get('subservice_list') or []:
                ss_id = ss_data.get('id')
                if ss_id:
                    subservice = self.get_service(ss_id)
                    self.update_service(subservice, ss_data)
                    del existing_ss_map[ss_id]
                else:
                    ss_data.update({
                        'parent_service': service
                    })
                    subservice = self.get_new_service(ss_data)
                    service.subservice_list.append(subservice)
            for subservice in existing_ss_map.values():
                self._delete_service(subservice)

        if 'serviced_entity' in json_data:
            self.update_service_serviced_entity(service, json_data['serviced_entity'])

        service.sum = calc_service_total_sum(service) if service.priceListItem_id else 0
        return service

    def update_service_serviced_entity(self, service, serviced_entity_data):
        if service.serviceKind_id == ServiceKind.simple_action[0]:
            # TODO: change amount?
            # из данных экшена может меняться только количество, но сейчас кол-во услуги не меняется
            service.action = self.update_service_action(service.action, serviced_entity_data)
        elif service.serviceKind_id == ServiceKind.group[0]:
            pass
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            # из данных лабораторного экшена может меняться набор назначаемых показателей исследования,
            # т.е. ActionProperty.isAssigned
            service.action = self.update_service_lab_action(service.action, serviced_entity_data)
        elif service.serviceKind_id == ServiceKind.lab_test[0]:
            # в случае показателей исследований и конкретного свойства экшена менять нечего.
            # ActionProperty.isAssigned меняется на уровне родительской лабораторной услуги
            pass

    def update_new_service(self, service, service_data):
        if service.serviceKind_id == ServiceKind.simple_action[0]:
            create_new_action_ttjs(service.serviced_entity)
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            ttj_data = {
                'selected_tissue_type': service_data['serviced_entity']['tests_data']['selected_tissue_type']
            }
            create_new_action_ttjs(service.serviced_entity, ttj_data=ttj_data)
        elif service.serviceKind_id == ServiceKind.group[0]:
            for subservice in service.subservice_list:
                self.update_new_service(subservice, service_data)
        return service

    def update_service_sum(self, service):
        service.sum = calc_service_total_sum(service) if service.priceListItem_id else 0

    def delete_service(self, service, raw=False):
        if not self.check_can_delete_service(service):
            raise ApiException(403, u'Невозможно удалить услугу с id = {0}'.format(service.id))
        self._delete_service(service, raw)
        return service

    def _delete_service(self, service, raw=False):
        service.deleted = 1
        if not raw:
            self._delete_serviced_entity(service)
        for subservice in service.subservice_list:
            self._delete_service(subservice)
        return service

    def _delete_serviced_entity(self, service):
        ent = service.serviced_entity
        if service.serviceKind_id == ServiceKind.simple_action[0]:
            if ent:
                self._delete_serviced_entity_action(ent)
        elif service.serviceKind_id == ServiceKind.group[0]:
            # нечего удалять
            pass
        elif service.serviceKind_id == ServiceKind.lab_action[0]:
            if ent:
                self._delete_serviced_entity_action(ent)
        elif service.serviceKind_id == ServiceKind.lab_test[0]:
            # ent = ActionProperty
            # оно и так удаляется при удалении родительского лабораторного экшена
            pass

    def _delete_serviced_entity_action(self, action):
        try:
            action = delete_action(action)
        except Exception, e:
            raise ApiException(403, unicode(e))
        return action

    def get_service_action(self, action_id):
        contract = self.session.query(Action).get(action_id)
        return contract

    def update_service_action(self, action, json_data):
        return action

    def update_service_lab_action(self, action, json_data):
        assigned = json_data['tests_data']['assigned']
        action = update_action(action, properties_assigned=assigned)
        return action

    def save_service_list(self, service_list):
        result = []
        for service_data in service_list:
            service_id = service_data.get('id')
            if service_id:
                service = self.get_service(service_id)
                service = self.update_service(service, service_data)
                result.append(service)
                # добавить в список изменений все подуслуги
                result.extend(service.get_flatten_subservices())
            else:
                service = self.get_new_service(service_data)
                service = self.update_new_service(service, service_data)
                result.append(service)
                # добавить в список изменений все подуслуги
                result.extend(service.get_flatten_subservices())
        return result

    def refresh_service_subservices(self, service_data):
        """Переформировать подуслуги для переданной услуги.

        В зависимости от вида услуги процесс будет отличаться. В данный момент
        поддерживается только переформирование списка подуслуг для лабораторной
        услуги в зависимости от измененных показателей исследования (apt_id),
        а также обновление лабораторной услуги, являющейся частью набора услуг.
        Изменение состава услуг в наборе услуг не поддерживается.
        """
        service_id = service_data.get('id')
        if service_id:
            service = self.get_service(service_id, full_load=True)
            # service = self.update_service(service, service_data)
        else:
            service = self.get_new_service(service_data)

        ref_ss_list = self.get_new_subservices_from_pricelist(service)
        upd_ss_list = []
        service_kind_id = safe_int(safe_traverse(service_data, 'service_kind', 'id'))

        if service_kind_id == ServiceKind.group[0]:
            for ssd in service_data['subservice_list']:
                ss = self.refresh_service_subservices(ssd)
                upd_ss_list.append(ss)
            service.subservice_list = upd_ss_list
        elif service_kind_id == ServiceKind.lab_action[0]:
            # apt_id: service
            ref_ss_map = dict(
                (s.serviced_entity.type_id, s)
                for s in ref_ss_list
            )
            existing_ss_map = dict(
                (s.serviced_entity.type_id, s)
                for s in service.subservice_list if s.id
            )
            for apt_id in service_data['serviced_entity']['tests_data']['assigned']:
                if apt_id in ref_ss_map:
                    upd_ss_list.append(
                        existing_ss_map[apt_id] if apt_id in existing_ss_map else ref_ss_map[apt_id]
                    )
            service.subservice_list = upd_ss_list
            self.update_service_serviced_entity(service, service_data['serviced_entity'])

        service.sum = calc_service_total_sum(service) if service.priceListItem_id else 0

        return service

    def get_new_service_for_new_action(self, action, service_data):
        pli_ctrl = PriceListItemController()
        pli_list = pli_ctrl.get_available_pli_list_for_new_action(action)
        if len(pli_list) == 0:
            raise ApiException(409, u'Не найдено подходящей позиции прайса для создаваемого Action')
        elif len(pli_list) > 1:
            raise ApiException(409, u'Найдено более одной подходящей позиции прайса для создаваемого Action')
        pli = pli_list[0]
        service_pli_id = service_data['price_list_item_id']
        if pli.id != service_pli_id:
            raise ApiException(422, u'Переданная позиция прайса для услуги и найденная в прайс-листе не совпадают.')

        amount = safe_double(action.amount)
        service_data.update({
            'amount': amount,
            'serviced_entity_from_action': action
        })
        new_service = self.get_new_service(service_data)
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
        return self.session.query(Invoice).join(
            InvoiceItem, InvoiceItem.invoice_id == Invoice.id
        ).join(
            Service, Service.id == InvoiceItem.concreteService_id
        ).filter(
            InvoiceItem.deleted == 0,
            Invoice.deleted == 0,
            Service.deleted == 0,
            Service.id == service.id
        ).count() > 0

    def get_actions_pay_info(self, action_id_list):
        if not action_id_list:
            return {}
        sel = self.get_selecter()
        pay_info = sel.get_action_service_pay_info(action_id_list)
        res = {}
        for item in pay_info:
            res[item.action_id] = {
                'sum': item.sum,
                'pay_status': ActionPayStatus(item.pay_status)
            }
        return res

    def get_services_pay_info(self, service_id_list):
        if not service_id_list:
            return {}
        sel = self.get_selecter()
        pay_info = sel.get_action_service_pay_info(service_id_list=service_id_list)
        res = {}
        for item in pay_info:
            res[item.service_id] = {
                'sum': item.sum,
                'pay_status': ActionPayStatus(item.pay_status)
            }
        return res

    def check_can_edit_service(self, service):
        return not service.in_invoice

    def check_can_delete_service(self, service):
        return not service.in_invoice and not service.parent_service

    def get_service_payment_info(self, service):
        if not service.id:
            return False
        pay_data = self.get_services_pay_info([service.id])
        pay_status = pay_data[service.id]['pay_status'] if service.id in pay_data else None
        return {
            'sum': service.sum,
            'pay_status': pay_status,
            'is_paid': pay_status and pay_status.value == ActionPayStatus.paid[0]
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

    def get_service_data_for_at_tree(self, args):
        service_data_list = self.search_mis_action_services(args)
        result = {}
        for service_data in service_data_list:
            at_id = service_data['action_type_id']
            if at_id:
                result[at_id] = service_data
        return result


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
                Service.parent_id == None,
                Service.deleted == 0
            )
        return self

    def get_service(self, service_id):
        Service = self.model_provider.get('Service')

        self.query = self.query.filter(
            Service.id == service_id
        ).options(
            joinedload(Service.price_list_item, innerjoin=True).
                joinedload('service', innerjoin=True),
            joinedload(Service.service_kind, innerjoin=True),
            joinedload(Service.action).joinedload('actionType'),
            joinedload(Service.action_property).joinedload('type'),
            joinedload(Service.discount)
        )
        return self.get_one()

    def get_event_services(self, event_id, page=None, per_page=None):
        Service = self.model_provider.get('Service')

        self.query = self.query.filter(
            Service.event_id == event_id,
            Service.parent_id == None,
            Service.deleted == 0
        ).options(
            joinedload(Service.price_list_item, innerjoin=True).
                joinedload('service', innerjoin=True),
            joinedload(Service.service_kind, innerjoin=True),
            joinedload(Service.action).joinedload('actionType'),
            joinedload(Service.action_property).joinedload('type'),
            joinedload(Service.discount)
        )
        if page is not None:
            return self.paginate(page, per_page or 10)
        else:
            return self.get_all()

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
        ).options(
            joinedload(Service.price_list_item, innerjoin=True).
                joinedload('service', innerjoin=True),
            joinedload(Service.service_kind, innerjoin=True),
            joinedload(Service.action).joinedload('actionType'),
            joinedload(Service.action_property).joinedload('type'),
            joinedload(Service.discount)
        )
        return self.get_all()

    def get_action_service_pay_info(self, action_id_list=None, service_id_list=None):
        if not action_id_list and not service_id_list:
            raise ValueError('Both `action_id_list` and `service_id_list` cannot be empty')
        Action = self.model_provider.get('Action')
        Event = self.model_provider.get('Event')
        EventType = self.model_provider.get('EventType')
        rbFinance = self.model_provider.get('rbFinance')
        Service = self.model_provider.get('Service')
        Invoice = self.model_provider.get('Invoice')
        InvoiceRefund = aliased(Invoice, name='InvoiceRefund')
        InvoiceItem = self.model_provider.get('InvoiceItem')
        FinanceTransaction = self.model_provider.get('FinanceTransaction')

        refund_trx_q = self.model_provider.get_query('FinanceTransaction').filter(
            FinanceTransaction.financeOperationType_id == FinanceOperationType.invoice_cancel[0],
            FinanceTransaction.invoice_id == InvoiceRefund.id
        ).limit(1)

        invoice_trx_q = self.model_provider.get_query('FinanceTransaction').filter(
            FinanceTransaction.financeOperationType_id == FinanceOperationType.invoice_pay[0]
        ).group_by(
            FinanceTransaction.invoice_id
        ).with_entities(
            FinanceTransaction.invoice_id.label('invoice_id'),
            func.sum(FinanceTransaction.sum).label('trx_sum')
        ).subquery('InvoiceTrx')

        invoice_q = self.model_provider.get_query('Invoice').join(
            InvoiceItem, and_(InvoiceItem.invoice_id == Invoice.id,
                              InvoiceItem.parent_id.is_(None),
                              Invoice.parent_id.is_(None))
        ).outerjoin(
            invoice_trx_q, invoice_trx_q.c.invoice_id == Invoice.id
        ).filter(
            Invoice.deleted == 0, InvoiceItem.deleted == 0
        ).group_by(
            Invoice.id
        ).with_entities(
            Invoice.id.label('invoice_id'),
            label('invoice_paid', invoice_trx_q.c.trx_sum >= func.sum(InvoiceItem.sum))
        ).subquery('MainInvoice')

        if action_id_list:
            self.query = self.model_provider.get_query('Action').join(
                Service, Service.action_id == Action.id
            ).filter(Action.id.in_(action_id_list))
        else:
            self.query = self.model_provider.get_query('Service').join(
                Action, Service.action_id == Action.id
            ).filter(Service.id.in_(service_id_list))
        self.query = self.query.join(
            Event, EventType, rbFinance
        ).outerjoin(
            InvoiceItem, and_(InvoiceItem.concreteService_id == Service.id,
                              InvoiceItem.deleted == 0)
        ).outerjoin(
            InvoiceRefund, and_(InvoiceRefund.id == InvoiceItem.refund_id,
                                refund_trx_q.exists())
        ).outerjoin(
            invoice_q, and_(InvoiceRefund.id.is_(None),
                            invoice_q.c.invoice_id == InvoiceItem.invoice_id)
        ).filter(
            rbFinance.code == PAID_EVENT_CODE,
        ).with_entities(
            Action.id.label('action_id'),
            Service.id.label('service_id'),
            Service.sum.label('sum'),
            func.IF(InvoiceRefund.id.isnot(None),
                    ActionPayStatus.refunded[0],
                    func.IF(invoice_q.c.invoice_paid,
                            ActionPayStatus.paid[0],
                            ActionPayStatus.not_paid[0])
                    ).label('pay_status')
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
        self.search = self.search.limit(
            0, limit_args.get('limit_max') or 100
        ).options(
            # this assumes that server sphinx conf has increased max_matches param
            max_matches=limit_args.get('limit_max') or 1000
        )
        return self