# -*- coding: utf-8 -*-

import datetime

from sqlalchemy.sql.expression import func, between
from sqlalchemy.sql import and_

from nemesis.models.accounting import PriceList, PriceListItem, Contract_PriceListAssoc, Contract
from nemesis.models.exists import rbService
from nemesis.models.actions import ActionType, ActionType_Service
from nemesis.lib.utils import safe_int, safe_date
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.lib.agesex import recordAcceptableEx


class PriceListController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return PriceListSelecter()

    def get_pricelist(self, pricelist_id):
        return self.get_selecter().get_by_id(pricelist_id)

    def get_contract_pricelist_id_list(self, contract_id):
        selecter = self.get_selecter()
        selecter.get_contract_pl_id_list(contract_id)
        data_list = selecter.get_all()
        pl_id_list = [safe_int(item[0]) for item in data_list]
        return pl_id_list

    def get_actual_pricelist(self, finance_id, date):
        date = safe_date(date)
        selecter = self.get_selecter()
        return selecter.get_actual_pricelist(finance_id, date)


class PriceListSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(PriceList).order_by(PriceList.begDate)
        super(PriceListSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        self.query = self.query.filter(PriceList.deleted == 0)
        if 'finance_id' in flt_args:
            finance_id = safe_int(flt_args['finance_id'])
            self.query = self.query.filter(PriceList.finance_id == finance_id)
        if 'for_date' in flt_args:
            date = safe_date(flt_args['for_date'])
            self.query = self.query.filter(
                PriceList.begDate <= date,
                PriceList.endDate >= date,
            )
        return self

    def get_contract_pl_id_list(self, contract_id):
        self.query = self.query.join(Contract.pricelist_list).filter(
            Contract.id == contract_id,
            PriceList.deleted == 0
        ).with_entities(PriceList.id)
        return self

    def get_actual_pricelist(self, finance_id, date):
        self.query = self.query.filter(
            PriceList.deleted == 0,
            PriceList.finance_id == finance_id,
            PriceList.begDate <= date,
            PriceList.endDate >= date
        )
        return self.get_all()


class PriceListItemController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return PriceListItemSelecter()

    def get_pricelist_item(self, pricelist_item_id):
        return self.get_selecter().get_by_id(pricelist_item_id)

    def get_available_pli_list_for_new_action(self, action):
        action_type_id = action.actionType.id
        contract_id = action.event.contract.id
        selecter = self.get_selecter()
        selecter.set_search_pli_by_at(action_type_id, contract_id)
        available_pli_list = selecter.get_all()
        return available_pli_list

    def get_available_pli_at_from_rbservice(self, rbservice_id, price_list_id):
        sel = self.get_selecter()
        result_list = sel.get_pli_at_by_rbservice(rbservice_id, price_list_id)
        # TODO: filter by agesex
        return result_list

    def get_available_pli_apt_from_rbservice(self, rbservice_id, price_list_id, client_id, action_type_id):
        sel = self.get_selecter()
        result_list = sel.get_pli_apt_by_rbservice(rbservice_id, price_list_id, action_type_id)

        client = self.get_selecter().model_provider.get_query('Client').get(client_id)
        client_age = client.age_tuple(datetime.date.today())
        filtered_result_list = []
        for item in result_list:
            if recordAcceptableEx(client.sexCode, client_age, item[3], item[2]):
                filtered_result_list.append(item[:2])
        return filtered_result_list

    def get_available_pli_for_groupservice_from_rbservice(self, rbservice_id, price_list_id):
        sel = self.get_selecter()
        result_list = sel.get_pli_for_groupservice_by_rbservice(rbservice_id, price_list_id)
        return result_list

    def get_apts_prices_by_pricelist(self, apt_id_list, contract_id):
        pl_ctrl = PriceListController()
        pricelist_id_list = pl_ctrl.get_contract_pricelist_id_list(contract_id)
        sel = self.get_selecter()
        result_list = sel.get_filtered_apt_price_by_pricelist(apt_id_list, pricelist_id_list)
        return {apt_id: price for apt_id, price in result_list}


class PriceListItemSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(PriceListItem)
        super(PriceListItemSelecter, self).__init__(query)

    def set_search_pli_by_at(self, action_type_id, contract_id):
        self.query = self.query.join(
            PriceList,
            Contract_PriceListAssoc,
            Contract
        ).join(
            rbService, PriceListItem.service_id == rbService.id
        ).join(
            ActionType_Service, and_(rbService.id == ActionType_Service.service_id,
                                     between(func.curdate(),
                                             ActionType_Service.begDate,
                                             func.coalesce(ActionType_Service.endDate, func.curdate()))
                                     )
        ).join(
            ActionType
        ).filter(
            PriceListItem.deleted == 0,
            between(func.curdate(),
                    PriceListItem.begDate,
                    PriceListItem.endDate),
            PriceList.deleted == 0,
            PriceList.draft == 0,
            Contract.id == contract_id,
            ActionType.id == action_type_id
        )
        return self

    def get_pli_at_by_rbservice(self, rbservice_id, price_list_id):
        PriceListItem = self.model_provider.get('PriceListItem')
        ActionType_Service = self.model_provider.get('ActionType_Service')
        ActionType = self.model_provider.get('ActionType')
        self.query = self.query.join(
            ActionType_Service, and_(PriceListItem.service_id == ActionType_Service.service_id,
                                     between(func.curdate(),
                                             ActionType_Service.begDate,
                                             func.coalesce(ActionType_Service.endDate, func.curdate()))
                                     )
        ).join(
            ActionType
        ).filter(
            PriceListItem.service_id == rbservice_id,
            PriceListItem.priceList_id == price_list_id,
            PriceListItem.deleted == 0,
            between(func.curdate(),
                    PriceListItem.begDate,
                    PriceListItem.endDate),
            ActionType.deleted == 0
        ).with_entities(
            PriceListItem.id,
            ActionType.id
        )
        return self.get_all()

    def get_pli_apt_by_rbservice(self, rbservice_id, price_list_id, action_type_id):
        PriceListItem = self.model_provider.get('PriceListItem')
        rbTest_Service = self.model_provider.get('rbTest_Service')
        rbTest = self.model_provider.get('rbTest')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        self.query = self.query.join(
            rbTest_Service, and_(PriceListItem.service_id == rbTest_Service.service_id,
                                 between(func.curdate(),
                                         rbTest_Service.begDate,
                                         func.coalesce(rbTest_Service.endDate, func.curdate()))
                                 )
        ).join(
            rbTest,
            ActionPropertyType
        ).filter(
            PriceListItem.service_id == rbservice_id,
            PriceListItem.priceList_id == price_list_id,
            PriceListItem.deleted == 0,
            between(func.curdate(),
                    PriceListItem.begDate,
                    PriceListItem.endDate),
            rbTest.deleted == 0,
            ActionPropertyType.deleted == 0,
            ActionPropertyType.actionType_id == action_type_id
        ).with_entities(
            PriceListItem.id,
            ActionPropertyType.id,
            ActionPropertyType.age,
            ActionPropertyType.sex
        )
        return self.get_all()

    def get_pli_for_groupservice_by_rbservice(self, rbservice_id, price_list_id):
        PriceListItem = self.model_provider.get('PriceListItem')
        self.query = self.query.filter(
            PriceListItem.service_id == rbservice_id,
            PriceListItem.priceList_id == price_list_id,
            PriceListItem.deleted == 0,
            between(func.curdate(),
                    PriceListItem.begDate,
                    PriceListItem.endDate),
        ).with_entities(
            PriceListItem.id,
        )
        return self.get_all()

    def get_filtered_apt_price_by_pricelist(self, apt_id_list, pricelist_id_list):
        PriceListItem = self.model_provider.get('PriceListItem')
        rbTest_Service = self.model_provider.get('rbTest_Service')
        rbTest = self.model_provider.get('rbTest')
        ActionPropertyType = self.model_provider.get('ActionPropertyType')
        self.query = self.query.join(
            rbTest_Service, and_(PriceListItem.service_id == rbTest_Service.service_id,
                                 between(func.curdate(),
                                         rbTest_Service.begDate,
                                         func.coalesce(rbTest_Service.endDate, func.curdate()))
                                 )
        ).join(
            rbTest,
            ActionPropertyType
        ).filter(
            PriceListItem.priceList_id.in_(pricelist_id_list),
            PriceListItem.deleted == 0,
            between(func.curdate(),
                    PriceListItem.begDate,
                    PriceListItem.endDate),
            rbTest.deleted == 0,
            ActionPropertyType.deleted == 0,
            ActionPropertyType.id.in_(apt_id_list)
        ).with_entities(
            ActionPropertyType.id,
            PriceListItem.price
        )
        return self.get_all()
