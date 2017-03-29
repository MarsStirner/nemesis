# -*- coding: utf-8 -*-
import datetime
import re

from sqlalchemy import orm

from nemesis.models.diagnosis import ActionType_rbDiagnosisType
from nemesis.lib.vesta import Vesta
from nemesis.systemwide import db
from exists import FDRecord
from nemesis.models.enums import TTJStatus
from nemesis.models.utils import safe_current_user_id, get_model_by_name, UUIDColumn

__author__ = 'mmalkov'


apt_valueDomain_String_re = re.compile(ur"'(.*?)'")


class Action(db.Model):
    __tablename__ = u'Action'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    directionDate = db.Column(db.DateTime)
    status = db.Column(db.Integer, nullable=False)
    setPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    isUrgent = db.Column(db.Boolean, nullable=False, server_default=u"'0'")
    begDate = db.Column(db.DateTime)
    plannedEndDate = db.Column(db.DateTime)
    endDate = db.Column(db.DateTime)
    note = db.Column(db.Text, nullable=False, default='')
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    office = db.Column(db.String(16), nullable=False, default='')
    amount = db.Column(db.Float(asdecimal=True), nullable=False)
    uet = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    expose = db.Column(db.Boolean, nullable=False, server_default=u"'1'")
    payStatus = db.Column(db.Integer, nullable=False, default=0)
    account = db.Column(db.Boolean, nullable=False, default=0)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    prescription_id = db.Column(db.Integer, index=True)
    takenTissueJournal_id = db.Column(db.ForeignKey('TakenTissueJournal.id'), index=True)
    contract_id = db.Column(db.Integer, index=True)
    coordDate = db.Column(db.DateTime)
    coordPerson_id = db.Column(db.Integer, db.ForeignKey('Person.id'), index=True)
    coordAgent = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordInspector = db.Column(db.String(128), nullable=False, server_default=u"''")
    coordText = db.Column(db.String, nullable=False, default='')
    hospitalUidFrom = db.Column(db.String(128), nullable=False, server_default=u"'0'")
    pacientInQueueType = db.Column(db.Integer, server_default=u"'0'")
    AppointmentType = db.Column(
        db.Enum(u'0', u'amb', u'hospital', u'polyclinic', u'diagnostics', u'portal', u'otherLPU'),
        nullable=False, default=u'0')
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    parentAction_id = db.Column(db.Integer, index=True)
    uuid_id = db.Column(db.ForeignKey('UUID.id'), nullable=False, index=True, server_default=u"'0'")
    dcm_study_uid = db.Column(db.String(50))
    uuid = db.Column(UUIDColumn(), nullable=False)

    actionType = db.relationship(u'ActionType')
    event = db.relationship(u'Event')
    person = db.relationship(u'Person', foreign_keys='Action.person_id')
    setPerson = db.relationship(u'Person', foreign_keys='Action.setPerson_id')
    coordPerson = db.relationship(u'Person', foreign_keys='Action.coordPerson_id')
    takenTissueJournal = db.relationship(u'TakenTissueJournal')
    # tissues = db.relationship(u'Tissue', secondary=u'ActionTissue')
    properties = db.relationship(u'ActionProperty')
    self_finance = db.relationship(u'rbFinance')
    bbt_response = db.relationship(u'BbtResponse', uselist=False)

    @property
    def properties_ordered(self):
        return sorted(self.properties, key=lambda ap: ap.type.idx)

    @property
    def propsByCode(self):
        return dict(
            (prop.type.code, prop)
            for prop in self.properties
            if prop.type.code
        )

    @property
    def propsByTypeId(self):
        return dict(
            (prop.type_id, prop)
            for prop in self.properties
        )

    def setPropValue(self, pt_id, value, raw=False):
        if pt_id not in self.propsByTypeId:
            new_p = ActionProperty()
            new_p.action = self
            new_p.type_id = pt_id
            new_p.type = ActionPropertyType.query.get(pt_id)
            db.session.add(new_p)
        else:
            new_p = self.propsByTypeId[pt_id]
        new_p.set_value(value, raw)

    def get_prop_value(self, apt_code):
        if apt_code in self.propsByCode:
            return self.propsByCode[apt_code].value

    def delete(self):
        self.deleted = 1
        for prop in self.properties:
            prop.delete()

    def _load_ap_price_info(self):
        """Инициализировать свойства данными из соответствующего прайс-листа"""
        from nemesis.lib.data_ctrl.accounting.pricelist import PriceListItemController
        from nemesis.lib.data import get_assignable_apts

        assignable = get_assignable_apts(self.actionType_id)
        assignable_apt_ids = [apt_data[0] for apt_data in assignable]
        contract_id = self.event.contract_id
        pli_ctrl = PriceListItemController()

        filtered_apt_prices = pli_ctrl.get_apts_prices_by_pricelist(assignable_apt_ids, contract_id)
        flt_apt_ids = filtered_apt_prices.keys()
        for prop in self.properties:
            if prop.type_id in flt_apt_ids:
                prop.has_pricelist_service = True
                prop.pl_price = filtered_apt_prices[prop.type_id]
            else:
                prop.has_pricelist_service = False

    def __getitem__(self, item):
        return self.propsByCode[item]


class ActionProperty(db.Model):
    __tablename__ = u'ActionProperty'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    action_id = db.Column(db.Integer, db.ForeignKey('Action.id'), nullable=False, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('ActionPropertyType.id'), nullable=False, index=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('rbUnit.id'), index=True)
    norm = db.Column(db.String(64), nullable=False, default='')
    isAssigned = db.Column(db.Boolean, nullable=False, server_default=u"'0'")
    evaluation = db.Column(db.Integer, default=None)
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    action = db.relationship(u'Action')
    type = db.relationship(u'ActionPropertyType', lazy=False, innerjoin=True)
    unit = db.relationship(u'rbUnit', lazy=False)

    def __init__(self):
        self._has_pricelist_service = None
        self._pl_price = None

    def get_value_container_class(self):
        # Следующая магия вытаскивает класс, ассоциированный с backref-пропертей, созданной этим же классом у нашего
        # ActionProperty. Объекты этого класса мы будем создавать для значений
        return getattr(self.__class__, self.__get_value_container_property_name()).property.mapper.class_

    def __get_value_container_property_name(self):
        type_name = self.type.typeName
        if type_name in ["Constructor", u"Жалобы", 'Text', 'Html']:
            class_name = 'String'
        elif type_name == u"Запись в др. ЛПУ":
            class_name = 'OtherLPURecord'
        elif type_name == "FlatDirectory":
            class_name = 'FDRecord'
        else:
            class_name = type_name
        return '_value_{0}'.format(class_name)

    @property
    def value_container(self):
        return getattr(self, self.__get_value_container_property_name())

    @value_container.setter
    def value_container(self, value):
        setattr(self, self.__get_value_container_property_name(), value)

    @property
    def value_raw(self):
        value_container = self.value_container
        if self.type.isVector:
            if value_container:
                return [item.value_ for item in value_container]
            return []
        else:
            if value_container:
                return value_container[0].value_

    @property
    def value(self):
        value_container = self.value_container
        if self.type.isVector:
            if value_container:
                return [item.value for item in value_container]
            return []
        else:
            if value_container:
                return value_container[0].value

    @value.setter
    def value(self, value):
        self.set_value(value)

    def delete(self):
        self.deleted = 1
        klass = self.get_value_container_class()
        klass.mark_as_deleted(self)

    def set_value(self, value, raw=False):
        if self.type.isVector and not (isinstance(value, (list, tuple)) or value is None):
            raise Exception(u'Tried assigning non-list value (%s) to vector action property (%s)' % (value, self.type.name))
        if not self.type.isVector and isinstance(value, (list, tuple)):
            raise Exception(u'Tried assigning list value (%s) to non-vector action property (%s)' % (value, self.type.name))
        value_container = self.value_container
        value_container_class = self.get_value_container_class()
        # объектификация значения
        if not raw:
            value = value_container_class.objectify(self, value)

        def make_value(value, index=0):
            value_container = value_container_class()
            if raw:
                value_container.set_raw_value(value)
            else:
                value_container.set_value(value)
            value_container.index = index
            value_container.property_object = self
            db.session.add(value_container)
            return value_container

        def delete_value(val_object):
            db.session.delete(val_object)

        if not self.type.isVector:
            if len(value_container) == 0:
                if value is not None:
                    value_container.append(make_value(value))
            else:
                if value is None or value == '':
                    delete_value(value_container[0])
                else:
                    value_container[0].set_value(value)
        else:
            if value:
                m = min(len(value_container), len(value))
                for i in xrange(m):
                    value_container[i].set_value(value[i])

                if len(value_container) < len(value):
                    for i in xrange(m, len(value)):
                        value_container.append(make_value(value[i], i))

                elif len(value_container) > len(value):
                    for i in xrange(len(value_container) - 1, m - 1, -1):
                        delete_value(value_container[i])
            else:
                for val in value_container:
                    delete_value(val)

    def set_value_container_and_value(self, val):
        """
        Используется в тех случаях, когда значение свойства было загружено отдельно
        и его нужно установить в ActionProperty без дополнительного запроса.

        NOTE: проверялось только на примерах с последующим чтением данных
        """
        from sqlalchemy.orm import attributes
        attributes.set_committed_value(self, self.__get_value_container_property_name(), [])
        self.set_value(val, True)

    @orm.reconstructor
    def init_on_load(self):
        self._has_pricelist_service = None
        self._pl_price = None

    @property
    def has_pricelist_service(self):
        if self._has_pricelist_service is None:
            self.action._load_ap_price_info()
        return self._has_pricelist_service

    @has_pricelist_service.setter
    def has_pricelist_service(self, value):
        self._has_pricelist_service = value

    @property
    def pl_price(self):
        if self._pl_price is None:
            self.action._load_ap_price_info()
        return self._pl_price

    @pl_price.setter
    def pl_price(self, value):
        self._pl_price = value

    def check_value_norm(self):
        """Попадает ли значение свойства в заданные нормы.

        -1: меньше нормы, 0: в норме, 1: больше нормы
        """
        if self.type.norm:
            min_, max_ = self.type.parse_norm()
            if (min_ is not None or max_ is not None) and self.value is not None:
                try:
                    val = float(self.value)
                except ValueError:
                    return 0
                if min_ is not None and val < min_:
                    return -1
                elif max_ is not None and val > max_:
                    return 1
                else:
                    return 0

    def __json__(self):
        return {
            'id': self.id,
            'idx': self.type.idx,
            'type': self.type,
            'is_assigned': self.isAssigned,
            'value': self.value,
            'value_in_norm': self.check_value_norm()
        }


class ActionPropertyTemplate(db.Model):
    __tablename__ = u'ActionPropertyTemplate'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.Integer, index=True)
    parentCode = db.Column(db.String(20), nullable=False)
    code = db.Column(db.String(64), nullable=False, index=True)
    federalCode = db.Column(db.String(64), nullable=False, index=True)
    regionalCode = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(120), nullable=False, index=True)
    abbrev = db.Column(db.String(64), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    service_id = db.Column(db.Integer, index=True)


class ActionPropertyType(db.Model):

    __tablename__ = u'ActionPropertyType'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    template_id = db.Column(db.ForeignKey('ActionPropertyTemplate.id'), index=True)
    name = db.Column(db.String(128), nullable=False)
    descr = db.Column(db.String(128), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('rbUnit.id'), index=True)
    typeName = db.Column(db.String(64), nullable=False)
    valueDomain = db.Column(db.Text, nullable=False)
    defaultValue = db.Column(db.String(5000), nullable=False)
    isVector = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    norm = db.Column(db.String(64), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    penalty = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    visibleInJobTicket = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isAssignable = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    test_id = db.Column(db.Integer, db.ForeignKey('rbTest.id'), index=True)
    defaultEvaluation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    toEpicrisis = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(25), index=True)
    mandatory = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    readOnly = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    createDatetime = db.Column(db.DateTime, nullable=False, index=True)
    createPerson_id = db.Column(db.Integer)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer)
    notLoadableWithTemplate = db.Column(db.SmallInteger)

    unit = db.relationship('rbUnit')
    template = db.relationship('ActionPropertyTemplate')
    test = db.relationship('rbTest')

    def parse_value_domain(self):
        if self.typeName == 'Diagnosis':
            from nemesis.lib.utils import parse_json
            return parse_json(self.valueDomain)
        elif self.typeName == 'String':
            values = [match.strip() for match in apt_valueDomain_String_re.findall(self.valueDomain)]
            if not self.valueDomain.strip():
                return {
                    'subtype': None,
                    'values': [],
                }
            elif '*' in values:
                return {
                    'subtype': 'Free',
                    'values': filter(lambda x: x != '*', values),
                }
            else:
                return {
                    'subtype': 'Select',
                    'values': values,
                }
        return None

    def parse_norm(self):
        try:
            # "0 - 100.0"
            min_, max_ = [float(v.strip().replace(',', '.')) for v in self.norm.split('-')]
        except:
            try:
                # "< 100"
                min_, max_ = None, float(self.norm.split('<')[1].strip().replace(',', '.'))
            except:
                try:
                    # "> 100"
                    min_, max_ = float(self.norm.split('>')[1].strip().replace(',', '.')), None
                except:
                    return None, None
        return min_, max_

    def __json__(self):
        value_domain = self.parse_value_domain()
        norm_min, norm_max = self.parse_norm()
        result = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'domain': self.valueDomain,
            'domain_obj': value_domain,
            'is_assignable': self.isAssignable,
            'ro': self.readOnly,
            'mandatory': self.mandatory,
            'type_name': self.typeName,
            'unit': self.unit,
            'norm': self.norm,
            'norm_min': norm_min,
            'norm_max': norm_max,
            'vector': bool(self.isVector),
            'description': self.descr,
            'not_loadable_with_template': bool(self.notLoadableWithTemplate)
        }
        if self.typeName == 'String' and value_domain['subtype']:
            result['type_name'] = 'String/{0}'.format(value_domain['subtype'])
        return result


class ActionProperty__ValueType(db.Model):
    __abstract__ = True

    @classmethod
    def objectify(cls, prop, json_data):
        return json_data

    @classmethod
    def mark_as_deleted(cls, prop):
        pass

    def set_raw_value(self, value):
        if isinstance(value, dict):
            value = value['id']
        if hasattr(self, 'value_'):
            self.value_ = value
        else:
            self.value = value

    def set_value(self, value):
        if isinstance(value, dict):
            return self.set_raw_value(value)
        else:
            self.value = value


class ActionProperty_Action(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Action'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Action.id'), index=True)

    value = db.relationship('Action')
    property_object = db.relationship('ActionProperty', backref='_value_Action')


class ActionProperty_Date(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Date'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Date)

    property_object = db.relationship('ActionProperty', backref='_value_Date')

    @classmethod
    def objectify(cls, prop, json_data):
        from nemesis.lib.utils import safe_date  # fixme: reorganize utils module
        return safe_date(json_data)


class ActionProperty_Double(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Double'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Float(asdecimal=True), nullable=False)
    property_object = db.relationship('ActionProperty', backref='_value_Double')


class ActionProperty_FDRecord(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_FDRecord'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('FDRecord.id'), nullable=False, index=True)

    value = db.relationship(u'FDRecord')
    property_object = db.relationship('ActionProperty', backref='_value_FDRecord')

    def get_value(self):
        return FDRecord.query.filter(FDRecord.id == self.value).first().get_value(u'Наименование')


class ActionProperty_HospitalBed(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_HospitalBed'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('OrgStructure_HospitalBed.id'), index=True)

    value = db.relationship(u'OrgStructure_HospitalBed')
    property_object = db.relationship('ActionProperty', backref='_value_HospitalBed')


class ActionProperty_HospitalBedProfile(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_HospitalBedProfile'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('rbHospitalBedProfile.id'), index=True)

    value = db.relationship('rbHospitalBedProfile')
    property_object = db.relationship('ActionProperty', backref='_value_HospitalBedProfile')


class ActionProperty_Image(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Image'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.BLOB)
    property_object = db.relationship('ActionProperty', backref='_value_Image')


class ActionProperty_ImageMap(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_ImageMap'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.String)
    property_object = db.relationship('ActionProperty', backref='_value_ImageMap')


class ActionProperty_Diagnosis(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Diagnosis'
    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Diagnostic.id'), nullable=False)

    value_model = db.relationship('Diagnostic')
    property_object = db.relationship('ActionProperty', backref='_value_Diagnosis')

    @property
    def value(self):
        return self.value_model

    @value.setter
    def value(self, val):
        if self.value_model is not None and self.value_model in db.session and self.value_model.id == val.id:
            self.value_model = db.session.merge(val)
        else:
            self.value_model = val

    @classmethod
    def objectify(cls, prop, json_data):
        from nemesis.lib.diagnosis import delete_diagnosis, create_or_update_diagnosis
        from nemesis.lib.utils import safe_traverse

        action = prop.action
        if prop.type.isVector:
            diag_list = []
            json_data = json_data or []
            for diag_data in json_data:
                if isinstance(diag_data, dict):
                    d = create_or_update_diagnosis(action.event, diag_data, action)
                    deleted = safe_traverse(diag_data, 'deleted')
                    db.session.add(d)
                else:
                    d = diag_data
                    deleted = d.deleted
                if deleted:
                    delete_diagnosis(d)
                else:
                    diag_list.append(d)
            return diag_list
        else:
            current_value = prop.value_raw
            if json_data is not None:
                if isinstance(json_data, dict):
                    d = create_or_update_diagnosis(action.event, json_data, action)
                    db.session.add(d)
                else:
                    d = json_data
                if current_value is not None and current_value != d.id:
                    delete_diagnosis(None, current_value)
            else:
                if current_value is not None:
                    delete_diagnosis(None, current_value)
                d = None
            return d

    @classmethod
    def mark_as_deleted(cls, prop):
        from nemesis.lib.diagnosis import delete_diagnosis

        value = prop.value
        if prop.type.isVector:
            if value:
                for diag in value:
                    delete_diagnosis(diag)
        else:
            if value:
                delete_diagnosis(value)


class ActionProperty_Integer_Base(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Integer'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.Integer, nullable=False)


class ActionProperty_Integer(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_Integer')

    @property
    def value(self):
        return self.value_

    @value.setter
    def value(self, val):
        self.value_ = val


class ActionProperty_AnalysisStatus(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_AnalysisStatus')

    @property
    def value(self):
        return rbAnalysisStatus.query.get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None


class ActionProperty_OperationType(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_OperationType')

    @property
    def value(self):
        return rbOperationType.query.get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val.id if val is not None else None


class ActionProperty_Boolean(ActionProperty_Integer_Base):
    property_object = db.relationship('ActionProperty', backref='_value_Boolean')

    @property
    def value(self):
        return bool(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = 1 if val else 0


class ActionProperty_RLS(ActionProperty_Integer_Base):

    def get_value(self):
        return v_Nomen.query.get(self.value).first() if self.value else None
    property_object = db.relationship('ActionProperty', backref='_value_RLS')


class ActionProperty_ReferenceRb(ActionProperty_Integer_Base):

    @property
    def value(self):
        if not hasattr(self, 'table_name'):
            domain = ActionProperty.query.get(self.id).type.valueDomain
            self.table_name = domain.split(';')[0]
        model = get_model_by_name(self.table_name)
        return model.query.get(self.value_)

    @value.setter
    def value(self, val):
        self.value_ = val['id'] if val is not None else None

    property_object = db.relationship('ActionProperty', backref='_value_ReferenceRb')


class ActionProperty_ExtReferenceRb(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_ExtRef'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.Text, nullable=False)

    def set_raw_value(self, value):
        if isinstance(value, dict):
            value = value['code']
        if hasattr(self, 'value_'):
            self.value_ = value
        else:
            self.value = value

    @property
    def value(self):
        if not hasattr(self, 'table_name'):
            domain = ActionProperty.query.get(self.id).type.valueDomain
            self.table_name = domain.split(';')[0]
        try:
            result = Vesta.get_rb(self.table_name, self.value_)
        except Exception, e:
            import traceback
            traceback.print_exc()
            return
        else:
            return {'id': result['_id'], 'name': result['name'], 'code': result['code']}

    @value.setter
    def value(self, val):
        self.value_ = val['code'] if val is not None else None

    property_object = db.relationship('ActionProperty', backref='_value_ExtReferenceRb')


class ActionProperty_Table(ActionProperty_Integer_Base):

    def get_value(self):
        return {}

    property_object = db.relationship('ActionProperty', backref='_value_Table')


class ActionProperty_JobTicket(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Job_Ticket'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Job_Ticket.id'), index=True)

    value = db.relationship('JobTicket')
    property_object = db.relationship('ActionProperty', backref='_value_JobTicket')


class ActionProperty_MKB(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_MKB'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('MKB.id'), index=True)

    value = db.relationship('MKB')
    property_object = db.relationship('ActionProperty', backref='_value_MKB')

    @classmethod
    def objectify(cls, prop, json_data):
        from nemesis.models.exists import MKB
        return MKB.query.get(json_data['id']) if json_data and 'id' in json_data else json_data


class ActionProperty_OrgStructure(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_OrgStructure'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('OrgStructure.id'), index=True)

    value = db.relationship('OrgStructure')
    property_object = db.relationship('ActionProperty', backref='_value_OrgStructure')


class ActionProperty_Organisation(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Organisation'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Organisation.id'), index=True)

    value = db.relationship('Organisation')
    property_object = db.relationship('ActionProperty', backref='_value_Organisation')


class ActionProperty_OtherLPURecord(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_OtherLPURecord'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Text(collation=u'utf8_unicode_ci'), nullable=False)


class ActionProperty_Person(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Person'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('Person.id'), index=True)

    value = db.relationship(u'Person')
    property_object = db.relationship('ActionProperty', backref='_value_Person')


class ActionProperty_String(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_String'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Text, nullable=False)
    property_object = db.relationship('ActionProperty', backref='_value_String')


class ActionProperty_URL(ActionProperty_String):
    property_object = db.relationship('ActionProperty', backref='_value_URL')


class ActionProperty_Time(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_Time'

    id = db.Column(db.Integer, db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value = db.Column(db.Time, nullable=False)
    property_object = db.relationship('ActionProperty', backref='_value_Time')

    @classmethod
    def objectify(cls, prop, json_data):
        from nemesis.lib.utils import safe_time  # fixme: reorganize utils module
        return safe_time(json_data)


class ActionProperty_rbBloodComponentType(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbBloodComponentType'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False)
    value_ = db.Column('value', db.ForeignKey('rbTrfuBloodComponentType.id'), nullable=False)

    value = db.relationship('rbBloodComponentType')
    property_object = db.relationship('ActionProperty', backref='_value_rbBloodComponentType')


class ActionProperty_rbFinance(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbFinance'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('rbFinance.id'), index=True)

    value = db.relationship('rbFinance')
    property_object = db.relationship('ActionProperty', backref='_value_rbFinance')


typeName_Value_map = {
    'String': ActionProperty_String,
    'Text': ActionProperty_String,
    'Constructor': ActionProperty_String,
    'Html': ActionProperty_String,
    'Integer': ActionProperty_Integer,
    'Double': ActionProperty_Double,
    'Date': ActionProperty_Date,
    'Time': ActionProperty_Time,
    'ReferenceRb': ActionProperty_Integer,
    'ExtReferenceRb': ActionProperty_ExtReferenceRb,
    'Person': ActionProperty_Person,
    'MKB': ActionProperty_MKB,
    'Organisation': ActionProperty_Organisation,
    'OrgStructure': ActionProperty_OrgStructure,
    'HospitalBed': ActionProperty_HospitalBed,
    'HospitalBedProfile': ActionProperty_HospitalBedProfile,
    'URL': ActionProperty_String,
    'Table': ActionProperty_Table,

    # not welcome
    'Diagnosis': ActionProperty_Diagnosis,
    'AnalysisStatus': ActionProperty_AnalysisStatus,
    'Image': ActionProperty_Image,
    'OperationType': ActionProperty_OperationType,
    'RLS': ActionProperty_RLS,
    'JobTicket': ActionProperty_JobTicket,
}


class ActionProperty_rbReasonOfAbsence(ActionProperty__ValueType):
    __tablename__ = u'ActionProperty_rbReasonOfAbsence'

    id = db.Column(db.ForeignKey('ActionProperty.id'), primary_key=True, nullable=False)
    index = db.Column(db.Integer, primary_key=True, nullable=False, server_default=u"'0'")
    value_ = db.Column('value', db.ForeignKey('rbReasonOfAbsence.id'), index=True)

    value = db.relationship('rbReasonOfAbsence')
    property_object = db.relationship('ActionProperty', backref='_value_rbReasonOfAbsence')


class ActionTemplate(db.Model):
    __tablename__ = u'ActionTemplate'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    deleted = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.ForeignKey('ActionTemplate.id'), index=True)
    code = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    owner_id = db.Column(db.ForeignKey('Person.id'), index=True)
    speciality_id = db.Column(db.ForeignKey('rbSpeciality.id'), index=True)
    action_id = db.Column(db.ForeignKey('Action.id'), index=True)

    action = db.relationship('Action')


# t_ActionTissue = db.Table(
#     u'ActionTissue', db.metadata,
#     db.Column(u'action_id', db.ForeignKey('Action.id'), primary_key=True, nullable=False, index=True),
#     db.Column(u'tissue_id', db.ForeignKey('Tissue.id'), primary_key=True, nullable=False, index=True)
# )


class ActionType(db.Model):
    __tablename__ = u'ActionType'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    hidden = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    class_ = db.Column(u'class', db.Integer, nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), index=True)
    code = db.Column(db.String(25), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    title = db.Column(db.Unicode(255), nullable=False)
    flatCode = db.Column(db.String(64), nullable=False, index=True)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    office = db.Column(db.String(32), nullable=False)
    showInForm = db.Column(db.Integer, nullable=False)
    genTimetable = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)
    quotaType_id = db.Column(db.Integer, index=True)
    context = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'1'")
    amountEvaluation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultStatus = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultDirectionDate = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultPlannedEndDate = db.Column(db.Integer, nullable=False)
    defaultEndDate = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultExecPerson_id = db.Column(db.Integer, index=True)
    defaultPersonInEvent = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defaultPersonInEditor = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    maxOccursInEvent = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showTime = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isMES = db.Column(db.Integer)
    nomenclativeService_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)
    isPreferable = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    prescribedType_id = db.Column(db.Integer, index=True)
    shedule_id = db.Column(db.Integer, index=True)
    isRequiredCoordination = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isRequiredTissue = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    testTubeType_id = db.Column(db.Integer, index=True)
    jobType_id = db.Column(db.ForeignKey('rbJobType.id'), index=True)
    mnem = db.Column(db.String(32), server_default=u"''")
    layout = db.Column(db.Text)
    hasPrescriptions = db.Column(db.Integer, index=True)

    services = db.relationship(u'ActionType_Service')
    nomenclatureService = db.relationship(u'rbService', foreign_keys='ActionType.nomenclativeService_id')
    property_types = db.relationship(u'ActionPropertyType', lazy='dynamic')
    group = db.relationship(u'ActionType', remote_side=[id])
    jobType = db.relationship(u'rbJobType')
    tissue_types = db.relationship('ActionType_TissueType')
    diagnosis_types = db.relationship('rbDiagnosisTypeN', secondary=ActionType_rbDiagnosisType)

    def get_property_type_by_name(self, name):
        return self.property_types.filter(ActionPropertyType.name == name).first()

    def get_property_type_by_code(self, code):
        return self.property_types.filter(ActionPropertyType.code == code).first()

    def __json__(self):
        from nemesis.lib.action.utils import get_action_type_class
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'class': self.class_,
            'flat_code': self.flatCode,
            'title': self.title,
            'context_name': self.context,
            'diagnosis_types': self.diagnosis_types,
            'hidden': self.hidden,
            'action_type_class': get_action_type_class(self.class_, self.isRequiredTissue).__json__()
        }


class ActionType_EventType_check(db.Model):
    __tablename__ = u'ActionType_EventType_check'

    id = db.Column(db.Integer, primary_key=True)
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False, index=True)
    eventType_id = db.Column(db.ForeignKey('EventType.id'), nullable=False, index=True)
    related_actionType_id = db.Column(db.ForeignKey('ActionType.id'), index=True)
    relationType = db.Column(db.Integer)

    actionType = db.relationship(u'ActionType', primaryjoin='ActionType_EventType_check.actionType_id == ActionType.id')
    eventType = db.relationship(u'EventType')
    related_actionType = db.relationship(u'ActionType', primaryjoin='ActionType_EventType_check.related_actionType_id == ActionType.id')


class ActionType_QuotaType(db.Model):
    __tablename__ = u'ActionType_QuotaType'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    quotaClass = db.Column(db.Integer)
    finance_id = db.Column(db.Integer, index=True)
    quotaType_id = db.Column(db.Integer, index=True)


class ActionType_Service(db.Model):
    __tablename__ = u'ActionType_Service'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True, nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date)


class ActionType_TissueType(db.Model):
    __tablename__ = u'ActionType_TissueType'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    tissueType_id = db.Column(db.ForeignKey('rbTissueType.id'), index=True)
    amount = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    unit_id = db.Column(db.ForeignKey('rbUnit.id'), index=True)
    testTubeType_id = db.Column(db.ForeignKey('rbTestTubeType.id'), index=True)

    master = db.relationship(u'ActionType')
    tissueType = db.relationship(u'rbTissueType')
    testTubeType = db.relationship(u'rbTestTubeType')
    unit = db.relationship(u'rbUnit')


class ActionType_User(db.Model):
    __tablename__ = u'ActionType_User'
    __table_args__ = (
        db.Index(u'person_id_profile_id', u'person_id', u'profile_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), nullable=False, index=True)
    person_id = db.Column(db.ForeignKey('Person.id'))
    profile_id = db.Column(db.ForeignKey('rbUserProfile.id'), index=True)

    actionType = db.relationship(u'ActionType')
    person = db.relationship(u'Person')
    profile = db.relationship(u'rbUserProfile')


class rbUnit(db.Model):
    __tablename__ = u'rbUnit'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(256), index=True)
    name = db.Column(db.Unicode(256), index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbTissueType(db.Model):
    __tablename__ = u'rbTissueType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    group_id = db.Column(db.ForeignKey('rbTissueType.id'), index=True)
    sexCode = db.Column("sex", db.Integer, nullable=False, server_default=u"'0'")

    group = db.relationship(u'rbTissueType', remote_side=[id])

    @property
    def sex(self):
        return {0: u'Любой',
                1: u'М',
                2: u'Ж'}[self.sexCode]

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'sex': self.sex,
        }


class Action_TakenTissueJournalAssoc(db.Model):
    __tablename__ = u'Action_TakenTissueJournal'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), index=True)
    takenTissueJournal_id = db.Column(db.ForeignKey('TakenTissueJournal.id'), index=True)

    action = db.relationship(u'Action')
    taken_tissue_journal = db.relationship(u'TakenTissueJournal')


class TakenTissueJournal(db.Model):
    __tablename__ = u'TakenTissueJournal'
    __table_args__ = (
        db.Index(u'period_barcode', u'period', u'barcode'),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.ForeignKey('Event.id'))
    client_id = db.Column(db.ForeignKey('Client.id'))
    tissueType_id = db.Column(db.ForeignKey('rbTissueType.id'), nullable=False, index=True)
    externalId = db.Column(db.String(30))
    amount = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    unit_id = db.Column(db.ForeignKey('rbUnit.id'), index=True)
    datetimePlanned = db.Column(db.DateTime, nullable=False)
    datetimeTaken = db.Column(db.DateTime)
    execPerson_id = db.Column(db.ForeignKey('Person.id'), index=True)
    note = db.Column(db.String(128), nullable=False, default='')
    barcode = db.Column(db.Integer, nullable=False)  # set with trigger
    period = db.Column(db.Integer, nullable=False)  # set with trigger
    testTubeType_id = db.Column(db.ForeignKey('rbTestTubeType.id'), index=True)
    statusCode = db.Column("status", db.Integer, nullable=False, server_default=u"'0'")

    event = db.relationship(u'Event')
    client = db.relationship(u'Client')
    execPerson = db.relationship(u'Person')
    tissueType = db.relationship(u'rbTissueType')
    testTubeType = db.relationship(u'rbTestTubeType')
    unit = db.relationship(u'rbUnit')
    actions = db.relationship(u'Action', secondary='Action_TakenTissueJournal', backref='tissues')

    @property
    def barcode_s(self):
        return code128C(self.barcode).decode('windows-1252')

    @property
    def status(self):
        return TTJStatus(self.statusCode) if self.statusCode is not None else None

    def __json__(self):
        return {
            'id': self.id,
            'datetime_taken': self.datetimeTaken,
            'datetime_planned': self.datetimePlanned,
            'event_id': self.event_id,
            'execPerson': self.execPerson,
            'barcode': self.barcode,
            'tissueType': self.tissueType,
            'testTubeType': self.testTubeType,
            'amount': self.amount,
            'status': self.status,
            'isUrgent': any(a.isUrgent for a in self.actions),
        }


class OrgStructure_HospitalBed(db.Model):
    __tablename__ = u'OrgStructure_HospitalBed'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(16), nullable=False, server_default=u"''")
    name = db.Column(db.String(64), nullable=False, server_default=u"''")
    isPermanentCode = db.Column("isPermanent", db.Integer, nullable=False, server_default=u"'0'")
    type_id = db.Column(db.Integer, db.ForeignKey('rbHospitalBedType.id'), index=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('rbHospitalBedProfile.id'), index=True)
    relief = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    schedule_id = db.Column(db.Integer, db.ForeignKey('rbHospitalBedSchedule.id'), index=True)
    begDate = db.Column(db.Date)
    endDate = db.Column(db.Date)
    sex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    involution = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    begDateInvolute = db.Column(db.Date)
    endDateInvolute = db.Column(db.Date)

    orgStructure = db.relationship(u'OrgStructure')
    type = db.relationship(u'rbHospitalBedType')
    profile = db.relationship(u'rbHospitalBedProfile')
    schedule = db.relationship(u'rbHospitalBedSchedule')

    def __json__(self):
        return {
            'id': self.id,
            'org_structure_id': self.master_id,
            'code': self.code,
            'name': self.name,
        }

    @property
    def isPermanent(self):
        return self.isPermanentCode == 1


class rbHospitalBedSchedule(db.Model):
    __tablename__ = u'rbHospitalBedSchedule'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbHospitalBedType(db.Model):
    __tablename__ = u'rbHospitalBedType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbHospitalBedProfile(db.Model):
    __tablename__ = u'rbHospitalBedProfile'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), index=True)

    # service = db.relationship('rbService')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbOperationType(db.Model):
    __tablename__ = u'rbOperationType'

    id = db.Column(db.Integer, primary_key=True)
    cd_r = db.Column(db.Integer, nullable=False)
    cd_subr = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(8), nullable=False, index=True)
    ktso = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbAnalysisStatus(db.Model):
    __tablename__ = u'rbAnalysisStatus'

    id = db.Column(db.Integer, primary_key=True)
    statusName = db.Column(db.String(80), nullable=False, unique=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.statusName,
            'name': self.statusName
        }


class Job(db.Model):
    __tablename__ = u'Job'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    jobType_id = db.Column(db.Integer, db.ForeignKey('rbJobType.id'), nullable=False, index=True)
    orgStructure_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    begTime = db.Column(db.Time, nullable=False)
    endTime = db.Column(db.Time, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    job_type = db.relationship(u'rbJobType')
    org_structure = db.relationship(u'OrgStructure')

    def __json__(self):
        return {
            'id': self.id,
            'jobType_id': self.jobType_id,
            'org_structure': self.org_structure,
        }


class JobTicket(db.Model):
    __tablename__ = u'Job_Ticket'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('Job.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    datetime = db.Column(db.DateTime, nullable=False)
    resTimestamp = db.Column(db.DateTime)
    resConnectionId = db.Column(db.Integer)
    status = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    begDateTime = db.Column(db.DateTime)
    endDateTime = db.Column(db.DateTime)
    label = db.Column(db.String(64), nullable=False, server_default=u"''")
    note = db.Column(db.String(128), nullable=False, server_default=u"''")

    job = db.relationship(u'Job')

    @property
    def jobType(self):
        return self.job.job_type

    @property
    def orgStructure(self):
        return self.job.org_structure

    def __unicode__(self):
        return u'%s, %s, %s' % (unicode(self.jobType),
                                unicode(self.datetime),
                                unicode(self.orgStructure))

    def __json__(self):
        return {
            'id': self.id,
            'job': self.job,
            'datetime': self.datetime,
            'status': self.status,
            'beg_datetime': self.begDateTime,
            'end_datetime': self.endDateTime,
            'label': self.label,
            'note': self.note,
        }


class rbJobType(db.Model):
    __tablename__ = u'rbJobType'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, index=True)
    code = db.Column(db.String(64), nullable=False)
    regionalCode = db.Column(db.String(64), nullable=False)
    name = db.Column(db.Unicode(128), nullable=False)
    laboratory_id = db.Column(db.Integer, index=True)
    isInstant = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class OrgStructure_ActionType(db.Model):
    __tablename__ = u'OrgStructure_ActionType'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.ForeignKey('OrgStructure.id'), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionType_id = db.Column(db.ForeignKey('ActionType.id'), index=True)


class BbtResponse(db.Model):
    __tablename__ = u'bbtResponse'

    id = db.Column(db.ForeignKey('Action.id'), primary_key=True)
    final = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    defects = db.Column(db.Text)
    doctor_id = db.Column(db.ForeignKey('Person.id'), nullable=False, index=True)
    codeLIS = db.Column(db.String(20), nullable=False)

    doctor = db.relationship(u'Person')
    values_organism = db.relationship(
        u'BbtResultOrganism',
        primaryjoin='BbtResponse.id == BbtResultOrganism.action_id',
        foreign_keys=[id],
        uselist=True
    )
    values_text = db.relationship(
        u'BbtResultText',
        primaryjoin='BbtResponse.id == BbtResultText.action_id',
        foreign_keys=[id],
        uselist=True
    )
    # values_table = db.relationship(u'BbtResultTable')
    # values_image = db.relationship(u'BbtResultImage')


class BbtResultOrganism(db.Model):
    __tablename__ = u'bbtResult_Organism'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), nullable=False, index=True)
    organism_id = db.Column(db.ForeignKey('rbMicroorganism.id'), nullable=False, index=True)
    concentration = db.Column(db.String(256), nullable=False)

    microorganism = db.relationship(u'rbMicroorganism', lazy='joined')
    sens_values = db.relationship(u'BbtOrganism_SensValues', lazy='joined')


class BbtOrganism_SensValues(db.Model):
    __tablename__ = u'bbtOrganism_SensValues'
    __table_args__ = (
        db.Index(u'bbtResult_Organism_id_index', u'bbtResult_Organism_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    bbtResult_Organism_id = db.Column(db.ForeignKey('bbtResult_Organism.id'), nullable=False)
    antibiotic_id = db.Column(db.ForeignKey('rbAntibiotic.id'), index=True)
    MIC = db.Column(db.String(20), nullable=False)
    activity = db.Column(db.String(5), nullable=False)

    antibiotic = db.relationship(u'rbAntibiotic', lazy='joined')


class BbtResultText(db.Model):
    __tablename__ = u'bbtResult_Text'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), nullable=False, index=True)
    valueText = db.Column(db.Text)


class BbtResultTable(db.Model):
    __tablename__ = u'bbtResult_Table'

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), nullable=False, index=True)
    indicator_id = db.Column(db.ForeignKey('rbBacIndicator.id'), nullable=False, index=True)
    normString = db.Column(db.String(256))
    normalityIndex = db.Column(db.Float)
    unit = db.Column(db.String(20))
    signDateTime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Text)
    comment = db.Column(db.Text)

    indicator = db.relationship(u'rbBacIndicator')


class BbtResultImage(db.Model):
    __tablename__ = u'bbtResult_Image'
    __table_args__ = (
        db.Index(u'action_id_index', u'action_id', u'idx'),
    )

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.ForeignKey('Action.id'), nullable=False)
    idx = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(256))
    image = db.Column(db.BLOB, nullable=False)


class rbAntibiotic(db.Model):
    __tablename__ = u'rbAntibiotic'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(256), nullable=False)


class rbBacIndicator(db.Model):
    __tablename__ = u'rbBacIndicator'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(256), nullable=False)


class rbMicroorganism(db.Model):
    __tablename__ = u'rbMicroorganism'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(256), nullable=False)