# coding: utf-8
import logging

from kombu import Connection

from nemesis.lib.data_ctrl.accounting.utils import get_contragent_type
from nemesis.models.enums import ContragentType
from nemesis.lib.apiutils import json_dumps
from nemesis.lib.utils import safe_traverse
from nemesis.app import app


logger = logging.getLogger('simple')


def get_invoice_integr_params():
    conf = safe_traverse(app.config, 'MIS_MQ_INTEGRATIONS', default={})
    is_enabled = 'rabbit_url' in conf and safe_traverse(conf, '1C_PAYMENT', 'invoice_queue')
    return bool(is_enabled), conf


def send_invoice_edit_message(invoice):
    ok, conf = get_invoice_integr_params()
    if not ok:
        return
    invoice_data = get_invoice_message(invoice)
    if not invoice_data:
        return

    logger.info(u'Отправка сообщения по редактированию счёта на оплату с id={0}'.format(invoice.id),
                extra=dict(tags=['INVOICE_INTGR']))

    with Connection(conf['rabbit_url']) as conn:
        sq = conn.SimpleQueue(conf['1C_PAYMENT']['invoice_queue'])
        msg = json_dumps(invoice_data)
        sq.put(msg)
        sq.close()


def get_invoice_message(invoice):
    from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController
    invoice_ctrl = InvoiceController()
    event = invoice_ctrl.get_invoice_event(invoice, with_deleted=True)
    client = event.client
    payer = invoice.contract.payer
    if get_contragent_type(payer).value == ContragentType.individual[0]:
        res = {
            'event': {
                'id': event.id,
                'setDate': event.setDate,
                'externalId': event.externalId
            },
            'invoice_data': {
                'number': invoice.number,
                'deleted': invoice.deleted != 0,
                'sum': invoice.total_sum
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
        return res
