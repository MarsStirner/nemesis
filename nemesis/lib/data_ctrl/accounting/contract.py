# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import or_, and_
from sqlalchemy.sql.expression import between, union, func

from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.models.accounting import Contract, rbContractType, Contract_Contragent, Contract_Contingent, PriceList
from nemesis.models.refbooks import rbFinance
from nemesis.models.client import Client
from nemesis.models.organisation import Organisation
from nemesis.models.enums import ContragentType, ContractTypeContingent, ContractContragentType
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_traverse
from nemesis.lib.const import VOL_POLICY_CODES, DMS_EVENT_CODE
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.utils import get_default_org
from nemesis.lib.counter import ContractCounter
from .utils import calc_payer_balance
from .pricelist import PriceListController


class ContractController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return ContractSelecter()

    def get_new_contract(self, params=None):
        if params is None:
            params = {}
        now = datetime.datetime.now()
        contract = Contract()
        contract.date = now
        contract.begDate = now

        contract_counter = ContractCounter('contract')
        contract.number = contract_counter.get_next_number()

        finance_id = safe_int(params.get('finance_id'))
        if finance_id:
            contract.finance = self.session.query(rbFinance).filter(rbFinance.id == finance_id).first()
        contract.deleted = 0

        contragent_ctrl = ContragentController()
        if 'payer_client_id' in params:
            contract.payer = contragent_ctrl.get_contragent_for_new_contract({
                'client_id': params['payer_client_id']
            })
        else:
            contract.payer = contragent_ctrl.get_new_contragent()

        default_org = get_default_org()
        contract.recipient = contragent_ctrl.get_contragent_for_new_contract({
            'org_id': default_org.id
        })

        contract.contingent_list = []
        if 'client_id' in params:
            contingent_ctrl = ContingentController()
            contract.contingent_list.append(contingent_ctrl.get_new_contingent({
                'client_id': params['client_id']
            }))
        return contract

    def get_contract(self, contract_id):
        return self.get_selecter().get_by_id(contract_id)

    def update_contract(self, contract, json_data):
        json_data = self._format_contract_data(json_data)
        for attr in ('date', 'begDate', 'endDate', 'finance', 'contract_type', 'resolution', ):
            if attr in json_data:
                setattr(contract, attr, json_data.get(attr))

        self.update_contract_number(contract, json_data['number'])
        self.update_contract_ca_payer(contract, json_data['payer'])
        self.update_contract_ca_recipient(contract, json_data['recipient'])
        self.update_contract_pricelist(contract, json_data['pricelist_list'])
        self.update_contract_contingent(contract, json_data['contingent_list'])
        return contract

    def delete_contract(self, contract):
        contract.deleted = 1
        return contract

    def update_contract_number(self, contract, number):
        number = safe_int(number)
        if not contract.id or contract.number != number:
            contract_counter = ContractCounter("contract")
            self.check_number_used(number, contract_counter)
            setattr(contract, 'number', number)
            if number == contract_counter.counter.value + 1:
                contract_counter.increment_value()
                self.session.add(contract_counter.counter)

    def update_contract_ca_payer(self, contract, ca_data):
        self.check_existing_ca(ca_data)
        contragent_ctrl = ContragentController()
        contragent_id = safe_int(ca_data.get('id'))
        if contragent_id:
            contragent = contragent_ctrl.get_contragent(contragent_id)
        else:
            contragent = contragent_ctrl.get_new_contragent()
            contragent = contragent_ctrl.update_contragent(contragent, ca_data)

        contract.payer = contragent
        return contragent

    def update_contract_ca_recipient(self, contract, ca_data):
        self.check_existing_ca(ca_data)
        contragent_ctrl = ContragentController()
        contragent_id = safe_int(ca_data.get('id'))
        if contragent_id:
            ca_recipient = contragent_ctrl.get_contragent(contragent_id)
        else:
            ca_recipient = contragent_ctrl.update_contragent(contract.recipient, ca_data)
        contract.recipient = ca_recipient
        return ca_recipient

    def check_number_used(self, number, counter):
        same_number = counter.check_number_used(number)
        if same_number:
            raise ApiException(409, u'Невозможно сохранить контракт: контракт с таким номером уже существует')

    def check_existing_ca(self, ca_data):
        contragent_id = safe_int(ca_data.get('id'))
        client_id = safe_traverse(ca_data, 'client', 'id')
        org_id = safe_traverse(ca_data, 'org', 'id')
        contragent_ctrl = ContragentController()
        ca = contragent_ctrl.get_existing_contragent(client_id, org_id, contragent_id)
        if ca is not None:
            raise ApiException(409, u'Невозможно сохранить контрагента: контрагент с такими параметрами уже существует')

    def update_contract_contingent(self, contract, cont_data):
        contingent_list = []
        contingent_ctrl = ContingentController()
        for cont_d in cont_data:
            contingent_id = safe_int(cont_d.get('id'))
            if contingent_id:
                contingent = contingent_ctrl.get_contingent(contingent_id)
            else:
                contingent = contingent_ctrl.get_new_contingent()
            contingent = contingent_ctrl.update_contingent(contingent, cont_d, contract)
            contingent_list.append(contingent)
        contract.contingent_list = contingent_list

    def update_contract_pricelist(self, contract, pl_data):
        pricelist_list = []
        pricelist_ctrl = PriceListController()
        for pl_d in pl_data:
            pricelist_id = safe_int(pl_d.get('id'))
            pricelist = pricelist_ctrl.get_pricelist(pricelist_id)
            pricelist_list.append(pricelist)
        contract.pricelist_list = pricelist_list

    def try_add_contingent(self, contract, client_id):
        assert contract.id is not None, u'contract should be saved first'
        contingent_ctrl = ContingentController()
        existing_con = contingent_ctrl.get_existing_contingent(client_id, contract.id)
        if not existing_con:
            new_cont = contingent_ctrl.get_new_contingent({
                'contract_id': contract.id,
                'client_id': client_id
            })
            contract.contingent_list.append(new_cont)

    def _format_contract_data(self, data):
        finance_id = safe_traverse(data, 'finance', 'id')
        contract_type_id = safe_traverse(data, 'contract_type', 'id')
        data['number'] = safe_unicode(data['number'])
        data['date'] = safe_date(data['date'])
        data['begDate'] = safe_date(data['beg_date'])
        data['endDate'] = safe_date(data['end_date'])
        data['finance'] = self.session.query(rbFinance).get(finance_id)
        data['contract_type'] = self.session.query(rbContractType).get(contract_type_id)
        data['resolution'] = safe_unicode(data['resolution'])
        return data

    def get_avalable_contracts(self, client_id, finance_id, set_date):
        selecter = self.get_selecter()
        available_contracts = selecter.get_available_contracts(client_id, finance_id, set_date)
        return available_contracts

    def get_last_contract_number(self):
        sel = self.get_selecter()
        return sel.get_last_number()


class ContragentController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return ContragentSelecter()

    def get_new_contragent(self, params=None):
        if params is None:
            params = {}
        ca = Contract_Contragent()
        if 'client_id' in params:
            client_id = safe_int(params.get('client_id'))
            client = self.session.query(Client).get(client_id)
            ca.client_id = client_id
            ca.client = client
        elif 'org_id' in params:
            org_id = safe_int(params.get('org_id'))
            org = self.session.query(Organisation).get(org_id)
            ca.organisation_id = org_id
            ca.org = org
        ca.deleted = 0
        return ca

    def get_contragent(self, ca_id):
        return self.get_selecter().get_by_id(ca_id)

    def get_contragent_for_new_contract(self, params):
        if 'client_id' in params:
            client_id = safe_int(params['client_id'])
            ca = self.get_existing_contragent(client_id=client_id)
            if ca is None:
                ca = self.get_new_contragent(params)
        elif 'org_id' in params:
            org_id = safe_int(params['org_id'])
            ca = self.get_existing_contragent(org_id=org_id)
            if ca is None:
                ca = self.get_new_contragent(params)
        else:
            ca = self.get_new_contragent()
        return ca

    def get_existing_contragent(self, client_id=None, org_id=None, not_contragent_id=None):
        if client_id is None and org_id is None:
            raise ValueError('both `client_id` and `org_id` arguments can\'t be empty')
        sel = self.get_selecter()
        args = {}
        if client_id:
            args['client_id'] = client_id
        if org_id:
            args['org_id'] = org_id
        if not_contragent_id:
            args['not_contragent_id'] = not_contragent_id
        sel.apply_filter(**args)
        ca = sel.get_one()
        return ca

    def update_contragent(self, contragent, json_data):
        json_data = self._format_contragent_data(json_data)
        contragent.client = json_data['client']
        contragent.org = json_data['org']
        return contragent

    def _format_contragent_data(self, data):
        client_id = safe_traverse(data, 'client', 'id')
        org_id = safe_traverse(data, 'org', 'id')
        if not client_id and not org_id:
            raise ApiException(
                422,
                u'Контрагент договора должен быть физическим или юридическим лицом и не может быть пустым.'
            )
        data['client'] = self.session.query(Client).filter(Client.id == client_id).first() if client_id else None
        data['org'] = self.session.query(Organisation).filter(Organisation.id == org_id).first() if org_id else None
        return data

    def search_payers(self, args):
        selecter = self.get_selecter()
        selecter.apply_filter(con_ca_type=ContractContragentType.payer[0], **args)
        selecter.apply_sort_order(**args)
        listed_data = selecter.get_all()
        return listed_data

    def get_payer(self, payer_id):
        payer = self.get_contragent(payer_id)
        if not payer:
            raise ApiException(404, u'Не найден плательщик с id = {0}'.format(payer_id))
        return payer

    def get_payer_balance(self, payer):
        return calc_payer_balance(payer)


class ContingentController(BaseModelController):

    @classmethod
    def get_selecter(cls):
        return ContingentSelecter()

    def get_new_contingent(self, params=None):
        if params is None:
            params = {}
        contract_id = safe_int(params.get('contract_id'))
        cont = Contract_Contingent()
        if contract_id:
            cont.contract_id = contract_id
        client_id = safe_int(params.get('client_id'))
        cont.client_id = client_id
        if client_id:
            cont.client = self.session.query(Client).get(client_id)
        cont.deleted = 0
        return cont

    def get_contingent(self, cont_id):
        return self.get_selecter().get_by_id(cont_id)

    def get_existing_contingent(self, client_id, contract_id):
        sel = self.get_selecter()
        sel.apply_filter(client_id=client_id, contract_id=contract_id)
        contingent = sel.get_one()
        return contingent

    def update_contingent(self, contingent, json_data, contract):
        json_data = self._format_contingent_data(json_data)
        contingent.contract = contract
        contingent.contract_id = contract.id
        contingent.client = json_data['client']
        # TODO: in separate method
        contingent.deleted = json_data['deleted']
        return contingent

    def _format_contingent_data(self, data):
        client_id = safe_traverse(data, 'client', 'id')
        data['client'] = self.session.query(Client).filter(Client.id == client_id).first() if client_id else None
        return data


class ContractSelecter(BaseSelecter):

    def set_base_query(self):
        self.query = self.model_provider.get_query('Contract')

    def apply_filter(self, **flt_args):
        Contract = self.model_provider.get('Contract')
        Contract_Contragent = self.model_provider.get('Contract_Contragent')
        Organisation = self.model_provider.get('Organisation')
        Client = self.model_provider.get('Client')

        self.query = self.query.filter(Contract.deleted == 0)

        if 'number' in flt_args:
            query_str = u'%{0}%'.format(safe_unicode(flt_args['number']))
            self.query = self.query.filter(Contract.number.like(query_str))
        if 'finance_id' in flt_args:
            self.query = self.query.filter(Contract.finance_id == safe_int(flt_args['finance_id']))
        if 'payer_query' in flt_args:
            self.query = self.query.join(
                Contract_Contragent, Contract.payer_id == Contract_Contragent.id
            ).outerjoin(Organisation, Client)
            query_str = u'%{0}%'.format(safe_unicode(flt_args['payer_query']))
            self.query = self.query.filter(or_(
                or_(Client.firstName.like(query_str),
                    Client.lastName.like(query_str),
                    Client.patrName.like(query_str)),
                or_(Organisation.shortName.like(query_str),
                    Organisation.fullName.like(query_str))
            ))
        if 'recipient_query' in flt_args:
            self.query = self.query.join(
                Contract_Contragent, Contract.recipient_id == Contract_Contragent.id
            ).outerjoin(Organisation, Client)
            query_str = u'%{0}%'.format(safe_unicode(flt_args['recipient_query']))
            self.query = self.query.filter(or_(
                or_(Client.firstName.like(query_str),
                    Client.lastName.like(query_str),
                    Client.patrName.like(query_str)),
                or_(Organisation.shortName.like(query_str),
                    Organisation.fullName.like(query_str))
            ))
        if 'beg_date_from' in flt_args:
            self.query = self.query.filter(Contract.begDate >= safe_date(flt_args['beg_date_from']))
        if 'beg_date_to' in flt_args:
            self.query = self.query.filter(Contract.begDate <= safe_date(flt_args['beg_date_to']))
        if 'end_date_from' in flt_args:
            self.query = self.query.filter(Contract.endDate >= safe_date(flt_args['end_date_from']))
        if 'end_date_to' in flt_args:
            self.query = self.query.filter(Contract.endDate <= safe_date(flt_args['end_date_to']))
        if 'set_date_from' in flt_args:
            self.query = self.query.filter(Contract.date >= safe_date(flt_args['set_date_from']))
        if 'set_date_to' in flt_args:
            self.query = self.query.filter(Contract.date <= safe_date(flt_args['set_date_to']))

        return self

    def get_available_contracts(self, client_id, finance_id, set_date):
        rbFinance = self.model_provider.get('rbFinance')
        Contract = self.model_provider.get('Contract')
        rbContractType = self.model_provider.get('rbContractType')
        Contract_Contingent = self.model_provider.get('Contract_Contingent')
        Contract_Contragent = self.model_provider.get('Contract_Contragent')
        Organisation = self.model_provider.get('Organisation')
        ClientPolicy = self.model_provider.get('ClientPolicy')
        rbPolicyType = self.model_provider.get('rbPolicyType')
        Client = self.model_provider.get('Client')

        finance = self.model_provider.get_query('rbFinance').filter(rbFinance.id == finance_id).first()
        base_query = self.model_provider.get_query('Contract').join(
            rbContractType
        ).outerjoin(
            Contract_Contingent
        ).filter(
            Contract.finance_id == finance_id,
            between(
                set_date,
                Contract.begDate,
                func.coalesce(Contract.endDate, func.curdate())
            ),
            Contract.deleted == 0,
            Contract.draft == 0
        )

        # 1 вариант - подходящие договоры по атрибутам контракта + проверка на строгое наличие контингента
        # используется в *платных, омс и вмп* обращениях
        contingent_query = base_query.filter(
            func.IF(rbContractType.requireContingent == ContractTypeContingent.strict_presence[0],
                    and_(Contract_Contingent.client_id == client_id,
                         Contract_Contingent.deleted == 0),
                    1)
        )

        # 2 вариант - в дополнение к выборке договора по 1ому варианту, который даст договоры с контингетом или без
        # добавляется выборка подходящего договора по наличию у пациента полиса *дмс*, выданного организацией,
        # являющейся плательщиком в договоре
        if finance.code == DMS_EVENT_CODE:
            contingent_query = base_query.filter(
                and_(Contract_Contingent.client_id == client_id,
                     Contract_Contingent.deleted == 0)
            )
            through_policy_query = self.model_provider.get_query('Contract').join(
                Contract_Contragent, and_(Contract.payer_id == Contract_Contragent.id,
                                          Contract_Contragent.deleted == 0)
            ).join(
                Organisation, (Contract_Contragent.organisation_id == Organisation.id)
            ).join(
                ClientPolicy, and_(ClientPolicy.insurer_id == Organisation.id,
                                   ClientPolicy.deleted == 0)
            ).join(
                rbPolicyType, and_(ClientPolicy.policyType_id == rbPolicyType.id,
                                   rbPolicyType.code.in_(VOL_POLICY_CODES))
            ).join(
                Client, (ClientPolicy.clientId == Client.id)
            ).filter(
                Contract.finance_id == finance_id,
                between(
                    set_date,
                    Contract.begDate,
                    func.coalesce(Contract.endDate, func.curdate())
                ),
                Contract.deleted == 0, Contract.draft == 0,
                # policy date range intersects contract date range
                and_(ClientPolicy.begDate <= func.coalesce(Contract.endDate, func.curdate()),
                     func.coalesce(ClientPolicy.endDate, func.curdate()) >= Contract.begDate)
            )
            self.query = self.model_provider.get_query('Contract').select_entity_from(
                union(contingent_query, through_policy_query)
            ).order_by(Contract.date.desc())
        else:
            self.query = contingent_query.order_by(Contract.date.desc())

        return self.get_all()

    def get_last_number(self):
        Contract = self.model_provider.get('Contract')
        self.query = self.query.filter(
            Contract.deleted == 0
        ).order_by(
            Contract.id.desc()
        ).with_entities(Contract.number)
        return self.get_first()


class ContragentSelecter(BaseSelecter):

    def set_base_query(self):
        self.query = self.model_provider.get_query('Contract_Contragent')

    def apply_filter(self, **flt_args):
        Contract_Contragent = self.model_provider.get('Contract_Contragent')
        Organisation = self.model_provider.get('Organisation')
        Client = self.model_provider.get('Client')
        Contract = self.model_provider.get('Contract')

        self.query = self.query.filter(Contract_Contragent.deleted == 0)

        if 'ca_type_code' in flt_args:
            ca_type_id = ContragentType.getId(flt_args['ca_type_code'])
            if ca_type_id == ContragentType.legal[0]:
                self.query = self.query.join(Organisation)
            elif ca_type_id == ContragentType.individual[0]:
                self.query = self.query.join(Client)
            if 'query' in flt_args:
                query = u'%{0}%'.format(flt_args['query'])
                if ca_type_id == ContragentType.legal[0]:
                    self.query = self.query.filter(or_(
                        Organisation.shortName.like(query),
                        Organisation.fullName.like(query)
                    ))
                elif ca_type_id == ContragentType.individual[0]:
                    self.query = self.query.filter(or_(
                        Client.firstName.like(query),
                        Client.lastName.like(query),
                        Client.patrName.like(query)
                    ))
            return self

        if 'con_ca_type' in flt_args:
            con_ca_type_id = flt_args['con_ca_type']
            if con_ca_type_id == ContractContragentType.payer[0]:
                self.query = self.query.join(
                    (Contract, Contract.payer_id == Contract_Contragent.id)
                ).filter(
                    Contract.deleted == 0,
                    Contract_Contragent.deleted == 0
                )
            if 'query' in flt_args:
                query = u'%{0}%'.format(flt_args['query'])
                self.query = self.query.outerjoin(Client).outerjoin(Organisation).filter(or_(
                    and_(
                        Contract_Contragent.client_id.isnot(None),
                        or_(Client.firstName.like(query),
                            Client.lastName.like(query),
                            Client.patrName.like(query))
                    ),
                    and_(
                        Contract_Contragent.organisation_id.isnot(None),
                        or_(Organisation.shortName.like(query),
                            Organisation.fullName.like(query))
                    )
                ))

        if 'client_id' in flt_args:
            self.query = self.query.filter(Contract_Contragent.client_id == flt_args['client_id'])
        if 'org_id' in flt_args:
            self.query = self.query.filter(Contract_Contragent.organisation_id == flt_args['org_id'])
        if 'not_contragent_id' in flt_args:
            self.query = self.query.filter(Contract_Contragent.id != flt_args['not_contragent_id'])
        return self


class ContingentSelecter(BaseSelecter):

    def set_base_query(self):
        self.query = self.model_provider.get_query('Contract_Contingent')

    def apply_filter(self, **flt_args):
        Contract_Contingent = self.model_provider.get('Contract_Contingent')

        self.query = self.query.filter(Contract_Contingent.deleted == 0)
        if 'client_id' in flt_args:
            self.query = self.query.filter(
                Contract_Contingent.client_id == safe_int(flt_args['client_id'])
            )
        if 'contract_id' in flt_args:
            self.query = self.query.filter(
                Contract_Contingent.contract_id == safe_int(flt_args['contract_id'])
            )
        return self