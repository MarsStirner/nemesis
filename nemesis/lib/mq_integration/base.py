# coding: utf-8
import logging
import uuid
import time

from kombu import Connection
from kombu.pools import producers

from nemesis.lib.utils import safe_traverse, safe_double
from nemesis.models.enums import Gender, AddressType, ActionStatus
from nemesis.lib.const import STATIONARY_ORG_STRUCT_STAY_CODE, STATIONARY_ORG_STRUCT_RECEIVED_CODE
from nemesis.app import app


logger = logging.getLogger('simple')


class MQIntegrationNotifier(object):

    msg_type = None
    bind_name = None
    operations = None

    def __init__(self):
        self._is_ready = False
        self._conf = None
        self._amqp_url = None
        self._exchange = None
        self._routing_key = None
        self._init_conf()

    def _init_conf(self, operation=None):
        if self._conf is None:
            conf = safe_traverse(app.config, 'AMQP_INTEGRATIONS', default={})
            if 'amqp_url' not in conf:
                self._is_ready = False
                return
            self._conf = conf
            self._amqp_url = conf['amqp_url']

        if self.msg_type is None or self.bind_name is None or self.operations is None:
            self._is_ready = False
            return

        if operation is not None:
            op_conf = safe_traverse(self._conf, 'bindings', self.bind_name, operation, default={})
            if 'exchange' not in op_conf or 'routing_key' not in op_conf or \
                    op_conf['routing_key'] not in self.operations.get_codes():
                self._is_ready = False
                return
            self._exchange = op_conf['exchange']
            self._routing_key = op_conf['routing_key']
            self._is_ready = True

    def set_operation(self, operation_id):
        op = self.operations(operation_id)
        if op.is_valid():
            self._init_conf(unicode(op))

    def notify(self, operation, data):
        raise NotImplementedError

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
                                 type=self.msg_type,
                                 timestamp=int(time.time()))

    # utility

    def _make_rb(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'code': rb.code,
            'name': rb.name
        }

    def _make_rb_units(self, rb):
        if rb is None:
            return None
        return {
            'id': rb.id,
            'code': rb.code,
            'name': rb.name,
            'shortName': rb.shortname if hasattr(rb, 'shortname') else rb.name
        }

    def _make_value_and_unit(self, value, unit):
        return {
            'value': safe_double(value),
            'unit': self._make_rb_units(unit)
        }

    def _make_gender(self, sex_code):
        g = Gender(sex_code)
        if g.value == Gender.male[0]:
            return 'MALE'
        elif g.value == Gender.female[0]:
            return 'FEMALE'
        else:
            return 'UNKNOWN'

    def _make_address_type(self, type_code):
        at = AddressType(type_code)
        if at.value == AddressType.reg[0]:
            return 'REGISTRATION'
        elif at.value == AddressType.live[0]:
            return 'LIVING'
        else:
            return 'UNKNOWN'

    def _make_action_status(self, status_code):
        st = ActionStatus(status_code)
        if st.value == ActionStatus.started[0]:
            return 'STARTED'
        elif st.value == ActionStatus.waiting[0]:
            return 'WAIT'
        elif st.value == ActionStatus.finished[0]:
            return 'FINISHED'
        else:
            return 'STARTED'

    def _make_address(self, addr):
        return {
            'id': addr.id,
            'addressType': self._make_address_type(addr.type),
            'value': unicode(addr)
        }

    def _make_organisation(self, org):
        if org is None:
            return None
        return {
            'id': org.id,
            'uuid': str(org.uuid),
            'shortName': org.shortName
        }

    def _make_org_struct(self, os):
        if os is None:
            return None
        return {
            'id': os.id,
            'code': os.code,
            'name': os.name,
            'uuid': str(os.uuid)
        }

    def _make_vmp_ticket(self, client_quoting):
        if client_quoting is None:
            return None
        treatment = client_quoting.quotaDetails and client_quoting.quotaDetails.treatment
        coupon = client_quoting.vmpCoupon
        return {
            'id': client_quoting.id,
            'number': coupon.number,
            'begDate': coupon.date,
            'endDate': None,
            'treatment': self._make_rb(treatment)
        }

    # common serializers

    def _make_client(self, client):
        if client is None:
            return None
        return {
            'id': client.id,
            'lastName': client.lastName,
            'firstName': client.firstName,
            'patrName': client.patrName,
            'sex': self._make_gender(client.sexCode),
            'birthDate': client.birthDate,
            'addresses': [
                self._make_address(addr)
                for addr in client.addresses
            ],
            'telecom': self._make_client_contacts(client)
        }

    def _make_client_contacts(self, client):
        res = []
        for contact in client.contacts:
            item = {
                'id': contact.id,
                'value': contact.contact
            }
            if contact.contactType.code == '01':
                item['system'] = 'phone'
                item['use'] = 'home'
            elif contact.contactType.code == '02':
                item['system'] = 'phone'
                item['use'] = 'work'
            elif contact.contactType.code == '03':
                item['system'] = 'phone'
                item['use'] = 'mobile'
            elif contact.contactType.code == '04':
                item['system'] = 'email'
                item['use'] = 'temp'

            if 'system' in item:
                res.append(item)

        return res

    def _make_event(self, event):
        return {
            'id': event.id,
            'setDate': event.setDate,
            'externalId': event.externalId,
            'endDate': event.execDate,
            'client': self._make_client(event.client),
            'contract': self._make_contract(event.contract),
            'vmpTicket': self._make_vmp_ticket(event.VMP_quoting),
            'orgStructure': self._make_org_struct(event.current_org_structure)
        }

    def _make_person(self, person):
        if person is None:
            return None
        return {
            'id': person.id,
            'lastName': person.lastName,
            'firstName': person.firstName,
            'patrName': person.patrName,
            'sex': self._make_gender(person.sex),
            'birthDate': person.birthDate,
            'uuid': str(person.uuid)
        }

    def _make_contract(self, contract):
        if contract is None:
            return None
        return {
            'id': contract.id,
            'payer': self._make_contragent(contract.payer),
            'number': contract.number,
            'signDate': contract.date,
            'begDate': contract.begDate,
            'endDate': contract.endDate,
            'finance': self._make_rb(contract.finance)
        }

    def _make_contragent(self, ca):
        if ca is None:
            return None
        ca_type = 'JURIDICAL' if ca.org else 'PHYSICAL'
        return {
            'id': ca.id,
            'type': ca_type,
            'person': self._make_client(ca.client),
            'organisation': self._make_organisation(ca.org)
        }

    def _make_basic_action(self, action):
        if action is None:
            return None
        return {
            'id': action.id,
            'status': self._make_action_status(action.status),
            'begDate': action.begDate,
            'endDate': action.endDate,
        }

    def _make_action_type(self, at):
        if at is None:
            return None
        return {
            'id': at.id,
            'code': at.code,
            'name': at.name,
            'flatCode': at.flatCode,
            'mnemonic': at.mnem,
        }

    def _make_moving_action(self, action):
        res = self._make_basic_action(action)
        if res is not None:
            res.update({
                'orgStructReceived': self._make_org_struct(action.get_prop_value(STATIONARY_ORG_STRUCT_RECEIVED_CODE)),
                'orgStructStay': self._make_org_struct(action.get_prop_value(STATIONARY_ORG_STRUCT_STAY_CODE)),
            })
        return res
