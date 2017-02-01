# coding: utf-8
import logging

from nemesis.lib.data_ctrl.accounting.utils import get_contragent_type
from nemesis.lib.enum import Enum
from nemesis.models.enums import ContragentType
from nemesis.lib.apiutils import json_dumps
from nemesis.lib.const import PAID_EVENT_CODE
from .base import MQIntegrationNotifier


logger = logging.getLogger('simple')


class MQOpsInvoice(Enum):
    create = 1
    update = 2
    delete = 3
    refund = 4


def notify_invoice_changed(op, invoice):
    payer = invoice.contract.payer
    finance_code = invoice.contract.finance.code

    if finance_code == PAID_EVENT_CODE and\
            get_contragent_type(payer).value == ContragentType.individual[0]:
        notifier = InvoiceIntegrationNotifier()

        try:
            notifier.notify(op, invoice)
        except Exception, e:
            logger.exception(e.message)


class InvoiceIntegrationNotifier(MQIntegrationNotifier):

    msg_type = 'Invoice'
    bind_name = 'invoice'
    operations = MQOpsInvoice

    def notify(self, operation, data):
        self.set_operation(operation)
        if not self._is_ready:
            return

        if operation == MQOpsInvoice.create:
            self.send_invoice_create_message(data)
        elif operation == MQOpsInvoice.update:
            self.send_invoice_edit_message(data)
        elif operation == MQOpsInvoice.delete:
            self.send_invoice_delete_message(data)
        elif operation == MQOpsInvoice.refund:
            self.send_invoice_refund_message(data)

    def send_invoice_create_message(self, invoice):
        invoice_data = self._get_message_data(invoice)

        msg = json_dumps(invoice_data)
        logger.info(u'Отправка сообщения по созданию счёта на оплату с id={0}: {1}'.format(invoice.id, msg),
                    extra=dict(tags=['INVOICE_INTGR']))

        self.send(msg)

    def send_invoice_edit_message(self, invoice):
        invoice_data = self._get_message_data(invoice)
        if not invoice_data:
            return

        msg = json_dumps(invoice_data)
        logger.info(u'Отправка сообщения по редактированию счёта на оплату с id={0}: {1}'.format(invoice.id, msg),
                    extra=dict(tags=['INVOICE_INTGR']))

        self.send(msg)

    def send_invoice_delete_message(self, invoice):
        invoice_data = self._get_message_data(invoice, is_refund=invoice.parent is not None)
        if not invoice_data:
            return

        msg = json_dumps(invoice_data)
        logger.info(u'Отправка сообщения по удалению счёта на оплату с id={0}: {1}'.format(invoice.id, msg),
                    extra=dict(tags=['INVOICE_INTGR']))

        self.send(msg)

    def send_invoice_refund_message(self, refund):
        invoice_data = self._get_message_data(refund, is_refund=True)
        if not invoice_data:
            return

        msg = json_dumps(invoice_data)
        logger.info(u'Отправка сообщения по возврату id={0} по счёту на оплату с id={1}: {2}'
                    .format(refund.id, refund.parent.id, msg),
                    extra=dict(tags=['INVOICE_INTGR']))

        self.send(msg)

    def _get_message_data(self, invoice, is_refund=False):
        from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController
        invoice_ctrl = InvoiceController()
        if is_refund:
            initial_invoice = invoice.parent
            refund_invoice = invoice
        else:
            initial_invoice = invoice
            refund_invoice = None
        event = invoice_ctrl.get_invoice_event(initial_invoice, with_deleted=True)

        res = {
            'event': self._make_event(event)
        }

        if not is_refund:
            res['invoice'] = self._make_invoice(initial_invoice)
        else:
            res['invoice'] = self._make_invoice(refund_invoice, parent_invoice=initial_invoice)
        return res

    def _make_invoice(self, invoice, parent_invoice=None):
        return {
            'id': invoice.id,
            'number': invoice.number,
            'deleted': invoice.deleted != 0,
            'contract': self._make_contract(invoice.contract),
            'sum': invoice.total_sum if invoice.parent_id is None else invoice.refund_sum,
            'parent': self._make_invoice(parent_invoice) if parent_invoice is not None else None
        }
