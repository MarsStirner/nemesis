# -*- coding: utf-8 -*-

from sqlalchemy.sql.expression import between, func

from nemesis.models.accounting import ServiceDiscount
from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter


class ServiceDiscountController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return ServiceDiscountSelecter()

    def get_service_discount(self, sd_id):
        return self.get_selecter().get_by_id(sd_id)


class ServiceDiscountSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(ServiceDiscount).order_by(ServiceDiscount.begDate, ServiceDiscount.valuePct)
        super(ServiceDiscountSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        self.query = self.query.filter(
            between(
                func.curdate(),
                ServiceDiscount.begDate,
                func.coalesce(ServiceDiscount.endDate, func.curdate())
            ),
            ServiceDiscount.deleted == 0
        )
        return self
