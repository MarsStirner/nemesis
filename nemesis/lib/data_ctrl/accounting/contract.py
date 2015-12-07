# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import or_, and_
from sqlalchemy.sql.expression import between, union, func

from nemesis.lib.data_ctrl.base import BaseModelController, BaseSelecter
from nemesis.models.accounting import Contract, rbContractType, Contract_Contragent, Contract_Contingent, PriceList
from nemesis.models.refbooks import rbFinance
from nemesis.models.client import Client, ClientPolicy
from nemesis.models.exists import rbPolicyType
from nemesis.models.organisation import Organisation
from nemesis.models.enums import ContragentType, ContractTypeInsurance, ContractContragentType
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_traverse
from nemesis.lib.const import COMP_POLICY_CODES, VOL_POLICY_CODES, OMS_EVENT_CODE, DMS_EVENT_CODE
from nemesis.lib.apiutils import ApiException
from nemesis.lib.data_ctrl.utils import get_default_org
from .utils import calc_payer_balance
from .pricelist import PriceListController


class ContractController(BaseModelController):

    def __init__(self):
        super(ContractController, self).__init__()
        self.contragent_ctrl = ContragentController()
        self.contingent_ctrl = ContingentController()
        self.pricelist_ctrl = PriceListController()

    def get_selecter(self):
        return ContractSelecter()

    def get_new_contract(self, params=None):
        if params is None:
            params = {}
        now = datetime.datetime.now()
        contract = Contract()
        contract.date = now
        contract.begDate = now
        finance_id = safe_int(params.get('finance_id'))
        if finance_id:
            contract.finance = self.session.query(rbFinance).filter(rbFinance.id == finance_id).first()
        contract.deleted = 0

        contract.payer = self.contragent_ctrl.get_new_contragent()
        default_org = get_default_org()
        contract.recipient = self.contragent_ctrl.get_new_contragent({
            'org_id': default_org.id
        })

        contract.contingent_list = []
        if 'client_id' in params:
            contract.contingent_list.append(self.contingent_ctrl.get_new_contingent({
                'client_id': params['client_id']
            }))
        return contract

    def get_contract(self, contract_id):
        contract = self.session.query(Contract).get(contract_id)
        return contract

    def update_contract(self, contract, json_data):
        json_data = self._format_contract_data(json_data)
        for attr in ('number', 'date', 'begDate', 'endDate', 'finance', 'contract_type', 'resolution', ):
            if attr in json_data:
                setattr(contract, attr, json_data.get(attr))
        self.update_contract_ca_payer(contract, json_data['payer'])
        self.update_contract_ca_recipient(contract, json_data['recipient'])
        self.update_contract_pricelist(contract, json_data['pricelist_list'])
        self.update_contract_contingent(contract, json_data['contingent_list'])
        return contract

    def delete_contract(self, contract):
        contract.deleted = 1
        return contract

    def update_contract_ca_payer(self, contract, ca_data):
        contragent_id = safe_int(ca_data.get('id'))
        if contragent_id:
            contragent = self.contragent_ctrl.get_contragent(contragent_id)
        else:
            contragent = self.contragent_ctrl.get_new_contragent()
            contragent = self.contragent_ctrl.update_contragent(contragent, ca_data)

        contract.payer = contragent
        return contragent

    def update_contract_ca_recipient(self, contract, ca_data):
        contragent_id = safe_int(ca_data.get('id'))
        if contragent_id:
            ca_recipient = self.contragent_ctrl.get_contragent(contragent_id)
        else:
            ca_recipient = self.contragent_ctrl.update_contragent(contract.recipient, ca_data)
        contract.recipient = ca_recipient
        return ca_recipient

    def update_contract_contingent(self, contract, cont_data):
        contingent_list = []
        for cont_d in cont_data:
            contingent_id = safe_int(cont_d.get('id'))
            if contingent_id:
                contingent = self.contingent_ctrl.get_contingent(contingent_id)
            else:
                contingent = self.contingent_ctrl.get_new_contingent()
            contingent = self.contingent_ctrl.update_contingent(contingent, cont_d, contract)
            contingent_list.append(contingent)
        contract.contingent_list = contingent_list

    def update_contract_pricelist(self, contract, pl_data):
        pricelist_list = []
        for pl_d in pl_data:
            pricelist_id = safe_int(pl_d.get('id'))
            pricelist = self.pricelist_ctrl.get_pricelist(pricelist_id)
            pricelist_list.append(pricelist)
        contract.pricelist_list = pricelist_list

    def _format_contract_data(self, data):
        finance_id = safe_traverse(data, 'finance', 'id')
        contract_type_id = safe_traverse(data, 'contract_type', 'id')
        data['number'] = data['number']
        data['date'] = safe_date(data['date'])
        data['begDate'] = safe_date(data['beg_date'])
        data['endDate'] = safe_date(data['end_date'])
        data['finance'] = self.session.query(rbFinance).get(finance_id)
        data['contract_type'] = self.session.query(rbContractType).get(contract_type_id)
        data['resolution'] = safe_unicode(data['resolution'])
        return data

    def get_avalable_contracts(self, client_id, finance_id, set_date):
        selecter = self.get_selecter()
        selecter.set_available_contracts(client_id, finance_id, set_date)
        available_contracts = selecter.get_all()
        return available_contracts

    def get_contract_pricelist_id_list(self, contract_id):
        selecter = self.get_selecter()
        selecter.set_availalble_pl_id_list(contract_id)
        data_list = selecter.get_all()
        pl_id_list = [safe_int(item[0]) for item in data_list]
        return pl_id_list


class ContragentController(BaseModelController):

    def get_selecter(self):
        return ContragentSelecter()

    def get_new_contragent(self, params=None):
        if params is None:
            params = {}
        ca = Contract_Contragent()
        if 'org_id' in params:
            org_id = safe_int(params.get('org_id'))
            org = self.session.query(Organisation).get(org_id)
            ca.organisation_id = org_id
            ca.org = org
        ca.deleted = 0
        return ca

    def get_contragent(self, ca_id):
        ca = self.session.query(Contract_Contragent).get(ca_id)
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
        payer = self.session.query(Contract_Contragent).get(payer_id)
        if not payer:
            raise ApiException(404, u'Не найден плательщик с id = {0}'.format(payer_id))
        return payer

    def get_payer_balance(self, payer):
        return calc_payer_balance(payer)


class ContingentController(BaseModelController):

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
        cont = self.session.query(Contract_Contingent).get(cont_id)
        return cont

    def update_contingent(self, contingent, json_data, contract):
        json_data = self._format_contingent_data(json_data)
        contingent.contract = contract
        contingent.client = json_data['client']
        # TODO: in separate method
        contingent.deleted = json_data['deleted']
        return contingent

    def _format_contingent_data(self, data):
        client_id = safe_traverse(data, 'client', 'id')
        data['client'] = self.session.query(Client).filter(Client.id == client_id).first() if client_id else None
        return data


class ContractSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(Contract)
        super(ContractSelecter, self).__init__(query)

    def set_available_contracts(self, client_id, finance_id, set_date):
        finance = self.session.query(rbFinance).filter(rbFinance.id == finance_id).first()
        finance_code = finance.code
        policy_codes = (
            COMP_POLICY_CODES
            if finance_code == OMS_EVENT_CODE
            else (
                VOL_POLICY_CODES
                if finance_code == DMS_EVENT_CODE
                else None
            )
        )

        contingent_query = self.session.query(Contract).join(
            rbContractType
        ).join(
            Contract_Contingent
        ).filter(
            Contract.finance_id == finance_id,
            between(
                set_date,
                Contract.begDate,
                func.coalesce(Contract.endDate, func.curdate())
            ),
            Contract.deleted == 0, Contract.draft == 0,
            Contract_Contingent.client_id == client_id,
            Contract_Contingent.deleted == 0
        )

        if policy_codes is not None:
            contingent_query = contingent_query.with_entities(Contract)
            through_policy_query = self.session.query(Contract).join(
                rbContractType, and_(Contract.contractType_id == rbContractType.id,
                                     rbContractType.usingInsurancePolicy == ContractTypeInsurance.with_policy[0])
            ).join(
                Contract_Contragent, and_(Contract.payer_id == Contract_Contragent.id,
                                          Contract_Contragent.deleted == 0)
            ).join(
                Organisation, (Contract_Contragent.organisation_id == Organisation.id)
            ).join(
                ClientPolicy, and_(ClientPolicy.insurer_id == Organisation.id,
                                   ClientPolicy.deleted == 0)
            ).join(
                rbPolicyType, and_(ClientPolicy.policyType_id == rbPolicyType.id,
                                   rbPolicyType.code.in_(policy_codes))
            ).join(
                Client, (ClientPolicy.clientId == Client.id)
            ).filter(
                ClientPolicy.id == client_id,
                Contract.finance_id == finance_id,
                between(
                    set_date,
                    Contract.begDate,
                    func.coalesce(Contract.endDate, func.curdate())
                ),
                Contract.deleted == 0, Contract.draft == 0,
                between(
                    set_date,
                    ClientPolicy.begDate,
                    func.coalesce(ClientPolicy.endDate, func.curdate())
                )
            )
            self.query = self.session.query(Contract).select_entity_from(
                union(contingent_query, through_policy_query)
            ).order_by(Contract.date)
        else:
            self.query = contingent_query.order_by(Contract.id)

    def set_availalble_pl_id_list(self, contract_id):
        self.query = self.query.join(Contract.pricelist_list).filter(
            Contract.id == contract_id,
            PriceList.deleted == 0
        ).with_entities(PriceList.id)
        return self


class ContragentSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(Contract_Contragent)
        super(ContragentSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
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
        return self

    # def apply_sort_order(self, **order_options):
    #     desc_order = order_options.get('order', 'ASC') == 'DESC'
    #     if order_options:
    #         pass
    #     else:
    #         source_action = aliased(Action, name='SourceAction')
    #         self.query = self.query.join(
    #             source_action, EventMeasure.sourceAction_id == source_action.id
    #         ).order_by(
    #             source_action.begDate.desc(),
    #             EventMeasure.begDateTime.desc(),
    #             EventMeasure.id.desc()
    #         )
    #     return self