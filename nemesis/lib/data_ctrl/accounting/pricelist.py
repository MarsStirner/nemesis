# -*- coding: utf-8 -*-

from sqlalchemy.sql.expression import func, between
from sqlalchemy.sql import and_

from nemesis.models.accounting import PriceList, PriceListItem, Contract_PriceListAssoc, Contract
from nemesis.models.exists import rbService
from nemesis.models.actions import ActionType, ActionType_Service
from nemesis.lib.utils import safe_int

from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter


class PriceListController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return PriceListSelecter()

    def get_pricelist(self, pricelist_id):
        pl = self.session.query(PriceList).get(pricelist_id)
        return pl


class PriceListSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(PriceList).order_by(PriceList.begDate)
        super(PriceListSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        if 'finance_id' in flt_args:
            finance_id = safe_int(flt_args['finance_id'])
            self.query = self.query.filter(PriceList.finance_id == finance_id)
        return self


class PriceListItemController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return PriceListItemSelecter()

    def get_pricelist_item(self, pricelist_item_id):
        pli = self.session.query(PriceListItem).get(pricelist_item_id)
        return pli

    def get_available_pli_list_for_new_action(self, action):
        action_type_id = action.actionType.id
        contract_id = action.event.contract.id
        selecter = self.get_selecter()
        selecter.set_search_pli_by_at(action_type_id, contract_id)
        available_pli_list = selecter.get_all()
        return available_pli_list


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
