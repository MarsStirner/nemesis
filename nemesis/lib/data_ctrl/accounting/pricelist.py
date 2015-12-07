# -*- coding: utf-8 -*-

from nemesis.models.accounting import PriceList
from nemesis.lib.utils import safe_int

from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter


class PriceListController(BaseModelController):

    def get_selecter(self):
        return PriceListSelecter()

    def get_pricelist(self, pricelist_id):
        contract = self.session.query(PriceList).get(pricelist_id)
        return contract


class PriceListSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(PriceList).order_by(PriceList.begDate)
        super(PriceListSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        if 'finance_id' in flt_args:
            finance_id = safe_int(flt_args['finance_id'])
            self.query = self.query.filter(PriceList.finance_id == finance_id)
        return self
