# coding: utf-8
import logging
import uuid
import time

from kombu import Connection
from kombu.pools import producers

from nemesis.lib.data_ctrl.accounting.utils import get_contragent_type
from nemesis.models.enums import ContragentType
from nemesis.lib.apiutils import json_dumps
from nemesis.lib.utils import safe_traverse
from nemesis.app import app


logger = logging.getLogger('simple')


class InvoiceIntegrationNotifier(object):

    def __init__(self):
        self._is_ready = False
        self._conf = None
        self._amqp_url = None
        self._exchange = None
        self._routing_key = None
        self._msg_type = None
        self._init_conf()

    def _init_conf(self, operation=None):
        if self._conf is None:
            conf = safe_traverse(app.config, 'AMQP_INTEGRATIONS', default={})
            if 'amqp_url' not in conf:
                self._is_ready = False
                return
            self._conf = conf
            self._amqp_url = conf['amqp_url']

        if operation is not None:
            op_conf = safe_traverse(self._conf, 'bindings', 'invoice', operation, default={})
            if 'exchange' not in op_conf or 'routing_key' not in op_conf:
                self._is_ready = False
                return
            self._exchange = op_conf['exchange']
            self._routing_key = op_conf['routing_key']
            self._msg_type = 'Invoice'
            self._is_ready = True

    def notify(self, operation, data):
        if operation == 'create':
            self.send_invoice_create_message(data)
        elif operation == 'update':
            self.send_invoice_edit_message(data)
        elif operation == 'delete':
            self.send_invoice_delete_message(data)
        elif operation == 'refund':
            self.send_invoice_refund_message(data)

    def send_invoice_create_message(self, invoice):
        self._init_conf('create')
        if not self._is_ready:
            return
        invoice_data = self.get_invoice_data(invoice)
        if not invoice_data:
            return

        logger.info(u'Отправка сообщения по созданию счёта на оплату с id={0}'.format(invoice.id),
                    extra=dict(tags=['INVOICE_INTGR']))

        msg = json_dumps(invoice_data)
        self.send(msg)

    def send_invoice_edit_message(self, invoice):
        self._init_conf('update')
        if not self._is_ready:
            return
        invoice_data = self.get_invoice_data(invoice)
        if not invoice_data:
            return

        logger.info(u'Отправка сообщения по редактированию счёта на оплату с id={0}'.format(invoice.id),
                    extra=dict(tags=['INVOICE_INTGR']))

        msg = json_dumps(invoice_data)
        self.send(msg)

    def send_invoice_delete_message(self, invoice):
        self._init_conf('delete')
        if not self._is_ready:
            return
        invoice_data = self.get_invoice_data(invoice, is_refund=invoice.parent is not None)
        if not invoice_data:
            return

        logger.info(u'Отправка сообщения по удалению счёта на оплату с id={0}'.format(invoice.id),
                    extra=dict(tags=['INVOICE_INTGR']))

        msg = json_dumps(invoice_data)
        self.send(msg)

    def send_invoice_refund_message(self, refund):
        self._init_conf('refund')
        if not self._is_ready:
            return
        invoice_data = self.get_invoice_data(refund, is_refund=True)
        if not invoice_data:
            return

        logger.info(u'Отправка сообщения по возврату id={0} по счёту на оплату с id={1}'
                    .format(refund.id, refund.parent.id),
                    extra=dict(tags=['INVOICE_INTGR']))

        msg = json_dumps(invoice_data)
        self.send(msg)

    def send(self, message):
        if not self._is_ready:
            return

        with Connection(self._amqp_url) as conn:
            with producers[conn].acquire(block=True) as producer:
                producer.publish(message,
                                 exchange=self._exchange,
                                 routing_key=self._routing_key,
                                 content_type='application/json',
                                 correlation_id=str(uuid.uuid4()),
                                 type=self._msg_type,
                                 timestamp=int(time.time()))

    def get_invoice_data(self, invoice, is_refund=False):
        from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController
        invoice_ctrl = InvoiceController()
        if is_refund:
            initial_invoice = invoice.parent
            refund_invoice = invoice
        else:
            initial_invoice = invoice
            refund_invoice = None

        event = invoice_ctrl.get_invoice_event(initial_invoice, with_deleted=True)
        client = event.client
        payer = invoice.contract.payer

        if get_contragent_type(payer).value == ContragentType.individual[0]:
            res = {
                'event': {
                    'id': event.id,
                    'setDate': event.setDate,
                    'externalId': event.externalId
                },
                'client': {
                    'id': client.id,
                    'firstName': client.firstName,
                    'lastName': client.lastName,
                    'patrName': client.patrName,
                },
                'payer': {
                    'id': payer.id,
                    'firstName': payer.client.firstName,
                    'lastName': payer.client.lastName,
                    'patrName': payer.client.patrName,
                }
            }
            if not is_refund:
                res.update({
                    'invoice_data': {
                        'number': initial_invoice.number,
                        'deleted': initial_invoice.deleted != 0,
                        'sum': initial_invoice.total_sum
                    }
                })
            else:
                res.update({
                    'invoice_data': {
                        'number': refund_invoice.number,
                        'deleted': refund_invoice.deleted != 0,
                        'sum': refund_invoice.refund_sum
                    },
                    'parent': {
                        'number': initial_invoice.number,
                        'deleted': initial_invoice.deleted != 0,
                        'sum': initial_invoice.total_sum
                    }
                })
            return res
