# -*- coding: utf-8 -*
import datetime

import itertools
from sqlalchemy import Table, between
from sqlalchemy.dialects.mysql.base import MEDIUMBLOB

from nemesis.systemwide import db
from nemesis.lib.agesex import AgeSex
from nemesis.models.utils import safe_current_user_id, UUIDColumn



# temp TODO: fix imports in projects
from .organisation import Organisation, OrganisationAccount, organisation_mkb_assoc
from .person import Person, rbAcademicDegree, rbAcademicTitle, PersonProfiles, \
    rbUserProfile, rbUserProfileRight, rbUserRight, vrbPersonWithSpeciality, rbPost, \
    rbSpeciality
from .refbooks import rbFinance
from .accounting import Contract, ContractTariff


class rbThesaurus(db.Model):
    __tablename__ = u'rbThesaurus'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, index=True)
    code = db.Column(db.String(30), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, server_default=u"''")
    template = db.Column(db.String(255), nullable=False, server_default=u"''")


class rbDocumentTypeGroup(db.Model):
    __tablename__ = 'rbDocumentTypeGroup'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbPacientModel(db.Model):
    __tablename__ = u'rbPacientModel'
    _table_description = u'Модели пациента'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbTreatment(db.Model):
    __tablename__ = u'rbTreatment'
    _table_description = u'Методы лечения'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')
    treatmentType_id = db.Column(db.ForeignKey('rbTreatmentType.id'))

    treatmentType = db.relationship('rbTreatmentType')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbTreatmentType(db.Model):
    __tablename__ = u'rbTreatmentType'
    _table_description = u'Виды лечения'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbTest(db.Model):
    __tablename__ = u'rbTest'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbTest_Service(db.Model):
    __tablename__ = u'rbTest_Service'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('rbTest.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date)


class rbTestTubeType(db.Model):
    __tablename__ = u'rbTestTubeType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64))
    name = db.Column(db.String(128), nullable=False)
    volume = db.Column(db.Float(asdecimal=True), nullable=False)
    unit_id = db.Column(db.ForeignKey('rbUnit.id'), nullable=False, index=True)
    covCol = db.Column(db.String(64))
    image = db.Column(MEDIUMBLOB)
    color = db.Column(db.String(8))

    unit = db.relationship(u'rbUnit')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'covCol': self.covCol,
            'unit': self.unit
        }


class rbBloodType(db.Model):
    __tablename__ = 'rbBloodType'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbBloodPhenotype(db.Model):
    __tablename__ = 'rbBloodPhenotype'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbBloodKell(db.Model):
    __tablename__ = 'rbBloodKell'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class OrgStructure(db.Model):
    __tablename__ = 'OrgStructure'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    organisation_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    code = db.Column(db.Unicode(255), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), index=True)
    type = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    net_id = db.Column(db.Integer, db.ForeignKey('rbNet.id'), index=True)
    isArea = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    hasHospitalBeds = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    hasStocks = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    infisCode = db.Column(db.String(16), nullable=False)
    infisInternalCode = db.Column(db.String(16), nullable=False)
    infisDepTypeCode = db.Column(db.String(16), nullable=False)
    infisTariffCode = db.Column(db.String(16), nullable=False)
    availableForExternal = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    Address = db.Column(db.String(255), nullable=False)
    inheritEventTypes = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    inheritActionTypes = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    inheritGaps = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    uuid_id = db.Column(db.Integer, nullable=False, index=True, server_default=u"'0'")
    show = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    uuid = db.Column(UUIDColumn(), nullable=False)

    parent = db.relationship('OrgStructure', remote_side=[id])
    organisation = db.relationship('Organisation')
    Net = db.relationship('rbNet')

    def getNet(self):
        if self.Net is None:
            if self.parent:
                self.Net = self.parent.getNet()
            elif self.organisation:
                self.Net = self.organisation.net
        return self.Net

    def get_org_structure_full_name(self, org_structure_id):
        names = [self.code]
        ids = {self.id}
        parent_id = self.parent_id
        parent = self.parent

        while parent_id:
            if parent_id in ids:
                parent_id = None
            else:
                ids.add(parent_id)
                names.append(parent.code)
                parent_id = parent.parent_id
                parent = parent.parent
        return '/'.join(reversed(names))

    def getFullName(self):
        return self.get_org_structure_full_name(self.id)

    def getAddress(self):
        if not self.Address:
            if self.parent:
                self.Address = self.parent.getAddress()
            elif self.organisation:
                self.Address = self.organisation.address
            else:
                self.Address = ''
        return self.Address

    net = property(getNet)
    fullName = property(getFullName)
    address = property(getAddress)

    def __unicode__(self):
        return self.getFullName()

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'show': self.show,
            'parent_id': self.parent_id,
        }


class rbAccountingSystem(db.Model):
    __tablename__ = u'rbAccountingSystem'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    isEditable = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    showInClientInfo = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'is_editable': bool(self.isEditable),
            'show_in_client_info': bool(self.showInClientInfo),
        }

    def __int__(self):
        return self.id


class rbAttachType(db.Model):
    __tablename__ = u'rbAttachType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    temporary = db.Column(db.Integer, nullable=False)
    outcome = db.Column(db.Integer, nullable=False)
    finance_id = db.Column(db.Integer, nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

    def __int__(self):
        return self.id


class rbContactType(db.Model):
    __tablename__ = 'rbContactType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    idx = db.Column(db.Integer, nullable=False, default=0)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'idx': self.idx,
        }

    def __int__(self):
        return self.id


class rbDocumentType(db.Model):
    __tablename__ = 'rbDocumentType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    regionalCode = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(64), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('rbDocumentTypeGroup.id'), nullable=False, index=True)
    serial_format = db.Column(db.Integer, nullable=False)
    number_format = db.Column(db.Integer, nullable=False)
    federalCode = db.Column(db.String(16), nullable=False)
    socCode = db.Column(db.String(8), nullable=False, index=True)
    TFOMSCode = db.Column(db.Integer)
    serial_regexp = db.Column(db.Unicode(256))
    number_regexp = db.Column(db.Unicode(256))
    serial_mask = db.Column(db.Unicode(256))
    number_mask = db.Column(db.Unicode(256))

    group = db.relationship(u'rbDocumentTypeGroup', lazy=False)

    def __json__(self):
        return {
            'id': self.id,
            'group': self.group,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'federal_code': self.federalCode,
            'soc_code': self.socCode,
            'TFOMS_code': self.TFOMSCode,
            'validators': {
                'serial': self.serial_regexp,
                'number': self.number_regexp,
            },
            'masks': {
                'serial': self.serial_mask,
                'number': self.number_mask,
            }
        }

    def __int__(self):
        return self.id


class rbNet(db.Model):
    __tablename__ = 'rbNet'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    sex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'restrictions': AgeSex(self),
        }

    def __int__(self):
        return self.id


class rbOKFS(db.Model):
    __tablename__ = 'rbOKFS'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    ownership = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'ownership': self.ownership,
        }

    def __int__(self):
        return self.id


class rbOKPF(db.Model):
    __tablename__ = 'rbOKPF'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbPolicyType(db.Model):
    __tablename__ = 'rbPolicyType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False, unique=True)
    name = db.Column(db.Unicode(256), nullable=False, index=True)
    TFOMSCode = db.Column(db.String(8))
    serial_regexp = db.Column(db.Unicode(256))
    number_regexp = db.Column(db.Unicode(256))
    serial_mask = db.Column(db.Unicode(256))
    number_mask = db.Column(db.Unicode(256))

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'TFOMS_code': self.TFOMSCode,
            'validators': {
                'serial': self.serial_regexp,
                'number': self.number_regexp,
            },
            'masks': {
                'serial': self.serial_mask,
                'number': self.number_mask,
            }
        }

    def __int__(self):
        return self.id


class rbReasonOfAbsence(db.Model):
    __tablename__ = 'rbReasonOfAbsence'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbRelationType(db.Model):
    __tablename__ = u'rbRelationType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    leftName = db.Column(db.String(64), nullable=False)
    rightName = db.Column(db.String(64), nullable=False)
    isDirectGenetic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardGenetic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isDirectRepresentative = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardRepresentative = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isDirectEpidemic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardEpidemic = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isDirectDonation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    isBackwardDonation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    leftSex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    rightSex = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    regionalCode = db.Column(db.String(64), nullable=False)
    regionalReverseCode = db.Column(db.String(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'leftName': self.leftName,
            'rightName': self.rightName,
            'leftSex': self.leftSex,
            'rightSex': self.rightSex,
        }

    def __int__(self):
        return self.id


class rbSocStatusClass(db.Model):
    __tablename__ = u'rbSocStatusClass'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.ForeignKey('rbSocStatusClass.id'), index=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    group = db.relationship(u'rbSocStatusClass', remote_side=[id])

    def __unicode__(self):
        return self.name

    def __int__(self):
        return self.id

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }

rbSocStatusClassTypeAssoc = db.Table('rbSocStatusClassTypeAssoc', db.Model.metadata,
                                     db.Column('class_id', db.Integer, db.ForeignKey('rbSocStatusClass.id')),
                                     db.Column('type_id', db.Integer, db.ForeignKey('rbSocStatusType.id'))
                                     )


class rbSocStatusType(db.Model):
    __tablename__ = u'rbSocStatusType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(250), nullable=False, index=True)
    socCode = db.Column(db.String(8), nullable=False, index=True)
    TFOMSCode = db.Column(db.Integer)
    regionalCode = db.Column(db.String(8), nullable=False)

    classes = db.relationship(u'rbSocStatusClass', secondary=rbSocStatusClassTypeAssoc, lazy='joined')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'classes': self.classes,
            'TFOMS_code': self.TFOMSCode,
        }

    def __int__(self):
        return self.id


class rbCashOperation(db.Model):
    __tablename__ = 'rbCashOperation'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbTariffCategory(db.Model):
    __tablename__ = 'rbTariffCategory'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbUFMS(db.Model):
    __tablename__ = u'rbUFMS'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50, u'utf8_bin'), nullable=False)
    name = db.Column(db.Unicode(256), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbCounter(db.Model):
    __tablename__ = u'rbCounter'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    value = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    prefix = db.Column(db.String(32))
    separator = db.Column(db.String(8), server_default=u"' '")
    reset = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    startDate = db.Column(db.DateTime, nullable=False)
    resetDate = db.Column(db.DateTime)
    sequenceFlag = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbMedicalKind(db.Model):
    __tablename__ = u'rbMedicalKind'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(1, u'utf8_unicode_ci'), nullable=False)
    name = db.Column(db.String(64, u'utf8_unicode_ci'), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbEventTypePurpose(db.Model):
    __tablename__ = u'rbEventTypePurpose'
    _table_description = u'Цели обращения'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    codePlace = db.Column(db.String(2))
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'code_place': self.codePlace,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbPrintTemplate(db.Model):
    __tablename__ = u'rbPrintTemplate'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    context = db.Column(db.String(64), nullable=False)
    fileName = db.Column(db.String(128), nullable=False)
    default = db.Column(db.Text, nullable=False)
    dpdAgreement = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    render = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    templateText = db.Column(db.Text, nullable=False)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbService(db.Model):
    __tablename__ = u'rbService'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(31), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    eisLegacy = db.Column(db.Integer, nullable=False, default=0)
    nomenclatureLegacy = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    license = db.Column(db.Integer, nullable=False, default="'0'")
    infis = db.Column(db.String(31), nullable=False, default='')
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    medicalAidProfile_id = db.Column(db.ForeignKey('rbMedicalAidProfile.id'), index=True, server_default=u"'NULL'")
    adultUetDoctor = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    adultUetAverageMedWorker = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    childUetDoctor = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    childUetAverageMedWorker = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    rbMedicalKind_id = db.Column(db.ForeignKey('rbMedicalKind.id'), index=True, server_default=u"'NULL'")
    UET = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    departCode = db.Column(db.String(3), server_default=u"'NULL'")
    isComplex = db.Column(db.SmallInteger, nullable=False, server_default=u"'0'")

    medicalAidProfile = db.relationship(u'rbMedicalAidProfile')
    rbMedicalKind = db.relationship(u'rbMedicalKind')
    subservice_assoc = db.relationship(
        'rbServiceGroupAssoc',
        primaryjoin='rbService.id==rbServiceGroupAssoc.group_id'
    )

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'begDate': self.begDate,
            'endDate': self.endDate,
        }

    def __int__(self):
        return self.id


class rbServiceGroupAssoc(db.Model):
    __tablename__ = u'rbServiceGroup'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('rbService.id'), nullable=False)
    required = db.Column(db.SmallInteger, nullable=False, server_default="'0'")
    serviceKind_id = db.Column(db.Integer, db.ForeignKey('rbServiceKind.id'), nullable=False)

    subservice = db.relationship('rbService', foreign_keys=[service_id])
    service_kind = db.relationship('rbServiceKind')

    def __json__(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'service_id': self.service_id,
            'serviceKind_id': self.serviceKind_id
        }

    def __int__(self):
        return self.id


class rbRequestType(db.Model):
    __tablename__ = u'rbRequestType'
    _table_description = u'Типы обращений'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    relevant = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'relevant': bool(self.relevant),
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbResult(db.Model):
    __tablename__ = u'rbResult'
    _table_description = u'Исходы лечения'

    id = db.Column(db.Integer, primary_key=True)
    eventPurpose_id = db.Column(db.ForeignKey('rbEventTypePurpose.id'), nullable=False, index=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    continued = db.Column(db.Integer, nullable=False)
    regionalCode = db.Column(db.String(8), nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    eventPurpose = db.relationship(u'rbEventTypePurpose', lazy='joined')

    def __json__(self):
        return {
            'id': self.id,
            'eventPurpose_id': self.eventPurpose_id,
            'code': self.code,
            'name': self.name,
            'continued': bool(self.continued),
            'regional_code': self.regionalCode,
            'event_purpose': self.eventPurpose,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class rbAcheResult(db.Model):
    __tablename__ = u'rbAcheResult'

    id = db.Column(db.Integer, primary_key=True)
    eventPurpose_id = db.Column(db.ForeignKey('rbEventTypePurpose.id'), nullable=False, index=True)
    code = db.Column(db.String(3, u'utf8_unicode_ci'), nullable=False)
    name = db.Column(db.String(64, u'utf8_unicode_ci'), nullable=False)

    eventPurpose = db.relationship(u'rbEventTypePurpose')

    def __json__(self):
        return {
            'id': self.id,
            'eventPurpose_id': self.eventPurpose_id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class Bank(db.Model):
    __tablename__ = u'Bank'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    bik = db.Column("BIK", db.String(10), nullable=False, index=True)
    name = db.Column(db.Unicode(100), nullable=False, index=True)
    branchName = db.Column(db.Unicode(100), nullable=False)
    corrAccount = db.Column(db.String(20), nullable=False)
    subAccount = db.Column(db.String(20), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'name': self.name,
            'bik': self.bik,
            'branch_name': self.branchName,
            'corr_account': self.corrAccount,
            'sub_account': self.subAccount,
        }

    def __int__(self):
        return self.id


class rbMesSpecification(db.Model):
    __tablename__ = u'rbMesSpecification'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    regionalCode = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)
    done = db.Column(db.Integer, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'done': self.done,
        }

    def __int__(self):
        return self.id


class rbEmergencyTypeAsset(db.Model):
    __tablename__ = u'rbEmergencyTypeAsset'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    codeRegional = db.Column(db.String(8), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.codeRegional,
        }

    def __int__(self):
        return self.id


class rbMedicalAidProfile(db.Model):
    __tablename__ = u'rbMedicalAidProfile'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    regionalCode = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
        }

    def __int__(self):
        return self.id


class rbDiagnosisType(db.Model):
    __tablename__ = u'rbDiagnosisType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    replaceInDiagnosis = db.Column(db.String(8), nullable=False)
    flatCode = db.Column(db.String(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'flat_code': self.flatCode,
        }

    def __int__(self):
        return self.id


class rbDiseaseCharacter(db.Model):
    __tablename__ = u'rbDiseaseCharacter'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    replaceInDiagnosis = db.Column(db.String(8), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbDiseasePhases(db.Model):
    __tablename__ = u'rbDiseasePhases'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    characterRelation = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbDiseaseStage(db.Model):
    __tablename__ = u'rbDiseaseStage'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    characterRelation = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbDispanser(db.Model):
    __tablename__ = u'rbDispanser'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    observed = db.Column(db.Integer, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'observed': self.observed,
        }

    def __int__(self):
        return self.id


class rbHospitalisationGoal(db.Model):
    __tablename__ = u'rbHospitalisationGoal'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(16), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbHospitalisationOrder(db.Model):
    __tablename__ = u'rbHospitalisationOrder'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(16), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbLaboratory(db.Model):
    __tablename__ = u'rbLaboratory'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    protocol = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(128), nullable=False)
    ownName = db.Column(db.String(128), nullable=False)
    labName = db.Column(db.String(128), nullable=False)

    tests = db.relationship('rbTest', secondary='rbLaboratory_Test', backref='labs')  # обработать удалённые тесты

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbLaboratory_TestAssoc(db.Model):
    __tablename__ = u'rbLaboratory_Test'
    __table_args__ = (
        db.Index(u'code', u'book', u'code'),
    )

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.ForeignKey('rbLaboratory.id'), nullable=False, index=True)
    test_id = db.Column(db.ForeignKey('rbTest.id'), nullable=False, index=True)
    book = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)

    test = db.relationship(u'rbTest', backref="lab_test")
    laboratory = db.relationship(u'rbLaboratory')


class rbServiceFinance(db.Model):
    __tablename__ = u'rbServiceFinance'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(2, u'utf8_unicode_ci'), nullable=False)
    name = db.Column(db.String(64, u'utf8_unicode_ci'), nullable=False)


class rbTraumaType(db.Model):
    __tablename__ = u'rbTraumaType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbHealthGroup(db.Model):
    __tablename__ = u'rbHealthGroup'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class MKB(db.Model):
    __tablename__ = u'MKB'
    __table_args__ = (
        db.Index(u'BlockID', u'BlockID', u'DiagID'),
        db.Index(u'ClassID_2', u'ClassID', u'BlockID', u'BlockName'),
        db.Index(u'ClassID', u'ClassID', u'ClassName')
    )

    id = db.Column(db.Integer, primary_key=True)
    ClassID = db.Column(db.String(8), nullable=False)
    ClassName = db.Column(db.String(150), nullable=False)
    BlockID = db.Column(db.String(9), nullable=False)
    BlockName = db.Column(db.String(160), nullable=False)
    DiagID = db.Column(db.String(8), nullable=False, index=True)
    DiagName = db.Column(db.String(160), nullable=False, index=True)
    Prim = db.Column(db.String(1), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(12), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    characters = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.Integer, index=True)
    MKBSubclass_id = db.Column(db.Integer)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    __mapper_args__ = {'order_by': DiagID}

    def __unicode__(self):
        return self.DiagID

    def __json__(self):
        return {
            'id': self.id,
            'code': self.DiagID,
            'name': self.DiagName,
        }

    def __int__(self):
        return self.id


class rbBloodComponentType(db.Model):
    __tablename__ = u'rbTrfuBloodComponentType'

    id = db.Column(db.Integer, primary_key=True)
    trfu_id = db.Column(db.Integer)
    code = db.Column(db.String(32))
    name = db.Column(db.String(256))
    unused = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class FDField(db.Model):
    __tablename__ = u'FDField'

    id = db.Column(db.Integer, primary_key=True)
    fdFieldType_id = db.Column(db.ForeignKey('FDFieldType.id'), nullable=False, index=True)
    flatDirectory_id = db.Column(db.ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    flatDirectory_code = db.Column(db.ForeignKey('FlatDirectory.code'), index=True)
    name = db.Column(db.String(4096), nullable=False)
    description = db.Column(db.String(4096))
    mask = db.Column(db.String(4096))
    mandatory = db.Column(db.Integer)
    order = db.Column(db.Integer)

    fdFieldType = db.relationship(u'FDFieldType')
    flatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDField.flatDirectory_id == FlatDirectory.id')
    values = db.relationship(u'FDFieldValue', backref=db.backref('fdField'), lazy='dynamic')

    def get_value(self, record_id):
        return self.values.filter(FDFieldValue.fdRecord_id == record_id).first().value


class FDFieldType(db.Model):
    __tablename__ = u'FDFieldType'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096), nullable=False)
    description = db.Column(db.String(4096))


class FDFieldValue(db.Model):
    __tablename__ = u'FDFieldValue'

    id = db.Column(db.Integer, primary_key=True)
    fdRecord_id = db.Column(db.ForeignKey('FDRecord.id'), nullable=False, index=True)
    fdField_id = db.Column(db.ForeignKey('FDField.id'), nullable=False, index=True)
    value = db.Column(db.String)

    fdRecord = db.relationship(u'FDRecord')


class FDRecord(db.Model):
    __tablename__ = u'FDRecord'

    id = db.Column(db.Integer, primary_key=True)
    flatDirectory_id = db.Column(db.ForeignKey('FlatDirectory.id'), nullable=False, index=True)
    flatDirectory_code = db.Column(db.ForeignKey('FlatDirectory.code'), index=True)
    order = db.Column(db.Integer)
    name = db.Column(db.String(4096))
    description = db.Column(db.String(4096))
    dateStart = db.Column(db.DateTime)
    dateEnd = db.Column(db.DateTime)

    FlatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDRecord.flatDirectory_code == FlatDirectory.code')
    flatDirectory = db.relationship(u'FlatDirectory', primaryjoin='FDRecord.flatDirectory_id == FlatDirectory.id')

    def get_value(self, field_name):
        return self.FlatDirectory.fields.filter(FDField.name == field_name).first().get_value(self.id)


class FlatDirectory(db.Model):
    __tablename__ = u'FlatDirectory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(4096), nullable=False)
    code = db.Column(db.String(128), index=True)
    description = db.Column(db.String(4096))

    fields = db.relationship(u'FDField', foreign_keys='FDField.flatDirectory_code', backref=db.backref('FlatDirectory'),
                             lazy='dynamic')


class UUID(db.Model):
    __tablename__ = u'UUID'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(100), nullable=False, unique=True)


class Setting(db.Model):
    __tablename__ = 'Setting'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'path': self.path,
            'value': self.value,
        }


class rbMethodOfAdministration(db.Model):
    __tablename__ = u'rbMethodOfAdministration'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class FileGroupDocument(db.Model):
    __tablename__ = u'FileGroupDocument'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(128))


class FileMeta(db.Model):
    __tablename__ = u'FileMeta'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(128), nullable=False)
    mimetype = db.Column(db.String(128), nullable=False, default='')
    path = db.Column(db.Unicode(256))
    external_id = db.Column(db.Integer)
    filegroup_id = db.Column(db.Integer, db.ForeignKey('FileGroupDocument.id'), nullable=False)
    idx = db.Column(db.Integer, nullable=False, default='0')
    deleted = db.Column(db.SmallInteger, nullable=False, default='0')

    filegroup = db.relationship('FileGroupDocument', backref='files')


class QuotaCatalog(db.Model):
    __tablename__ = u'QuotaCatalog'

    id = db.Column(db.Integer, primary_key=True)
    finance_id = db.Column(db.ForeignKey('rbFinance.id', ondelete='RESTRICT', onupdate='RESTRICT'),
                           nullable=False, index=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    catalogNumber = db.Column(db.Unicode(45), nullable=False, server_default=u"''")
    documentDate = db.Column(db.Date, nullable=True)
    documentNumber = db.Column(db.Unicode(45), nullable=True)
    documentCorresp = db.Column(db.Unicode(256), nullable=True)
    comment = db.Column(db.UnicodeText, nullable=True)

    finance = db.relationship('rbFinance')

    def __json__(self):
        return {'id': self.id,
                # 'finance_id': self.finance_id,
                'finance': self.finance,
                'create_datetime': self.createDatetime,
                'create_person_id': self.createPerson_id,
                'beg_date': self.begDate,
                'end_date': self.endDate,
                'catalog_number': self.catalogNumber,
                'document_date': self.documentDate,
                'document_number': self.documentNumber,
                'document_corresp': self.documentCorresp,
                'comment': self.comment}


class QuotaType(db.Model):
    __tablename__ = u'QuotaType'

    id = db.Column(db.Integer, primary_key=True)
    catalog_id = db.Column(db.ForeignKey('QuotaCatalog.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=False, index=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    class_ = db.Column(u'class', db.Integer, nullable=False, server_default=u"'0'")
    profile_code = db.Column(db.String(16))
    group_code = db.Column(db.String(16))
    type_code = db.Column(db.String(16))
    code = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    teenOlder = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    price = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")

    catalog = db.relationship('QuotaCatalog', backref='quotaTypes')

    def __json__(self):
        return {'id': self.id,
                'catalog_id': self.catalog_id,
                # 'catalog': self.catalog,
                'create_datetime': self.createDatetime,
                'create_person_id': self.createPerson_id,
                # 'deleted': self.deleted,
                'class': self.class_,
                'profile_code': self.profile_code,
                'group_code': self.group_code,
                'type_code': self.type_code,
                'code': self.code,
                'name': self.name,
                'teen_older': self.teenOlder,
                'price': self.price}

    def __unicode__(self):
        return self.name


class MKB_VMPQuotaFilter(db.Model):
    __tablename__ = u'MKB_VMPQuotaFilter'

    id = db.Column(db.Integer, primary_key=True)
    MKB_id = db.Column(db.ForeignKey('MKB.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    quotaDetails_id = db.Column(
        db.ForeignKey('VMPQuotaDetails.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)


class VMPQuotaDetails(db.Model):
    __tablename__ = u'VMPQuotaDetails'

    id = db.Column(db.Integer, primary_key=True)
    pacientModel_id = db.Column(db.ForeignKey('rbPacientModel.id', ondelete='RESTRICT', onupdate='RESTRICT'),
                                nullable=False, index=True)
    treatment_id = db.Column(db.ForeignKey('rbTreatment.id', ondelete='RESTRICT', onupdate='RESTRICT'),
                             nullable=False, index=True)
    quotaType_id = db.Column(db.ForeignKey('QuotaType.id', ondelete='CASCADE', onupdate='CASCADE'),
                             nullable=False, index=True)
    price = db.Column(db.DECIMAL)

    pacient_model = db.relation('rbPacientModel')
    treatment = db.relation('rbTreatment')
    quota_type = db.relation('QuotaType', backref='quotaDetails')
    mkb = db.relation('MKB', secondary=MKB_VMPQuotaFilter.__table__, lazy=False)

    def __json__(self):
        return {
            'id': self.id,
            # 'pacient_model_id': self.pacientModel_id,
            # 'treatment_id': self.treatment_id,
            'quota_type_id': self.quotaType_id,
            'patient_model': self.pacient_model,
            'treatment': self.treatment,
            'mkb': self.mkb,
            'treatment_type': self.treatment.treatmentType if self.treatment else None,
            'price': self.price,
            # 'quota_type': self.quota_type
        }


class ClientQuoting(db.Model):
    __tablename__ = u'Client_Quoting'
    __table_args__ = (
        db.Index(u'deleted_prevTalon_event_id', u'deleted', u'prevTalon_event_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.ForeignKey('Client.id'), index=True)
    identifier = db.Column(db.Unicode(16))
    quotaTicket = db.Column(db.Unicode(20))
    quotaDetails_id = db.Column(db.ForeignKey('VMPQuotaDetails.id', ondelete='RESTRICT', onupdate='RESTRICT'),
                                nullable=False, index=True)
    stage = db.Column(db.Integer)
    directionDate = db.Column(db.DateTime)
    freeInput = db.Column(db.Unicode(128))
    org_id = db.Column(db.Integer)
    amount = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    MKB_id = db.Column(db.ForeignKey('MKB.id'), nullable=False)
    vmpCoupon_id = db.Column(db.ForeignKey('VMPCoupon.id'), nullable=False)
    status = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    request = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    statment = db.Column(db.Unicode(255))
    dateRegistration = db.Column(db.DateTime)
    dateEnd = db.Column(db.DateTime)
    orgStructure_id = db.Column(db.Integer)
    regionCode = db.Column(db.String(13), index=True)
    event_id = db.Column(db.ForeignKey('Event.id'), index=True)
    prevTalon_event_id = db.Column(db.Integer)
    version = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    event = db.relationship('Event')
    master = db.relationship(u'Client', backref='VMP_quoting')
    MKB_object = db.relationship('MKB')
    vmpCoupon = db.relationship('VMPCoupon', backref=db.backref('clientQuoting', uselist=False))
    quotaDetails = db.relationship('VMPQuotaDetails')

    @property
    def MKB(self):
        try:
            return self.MKB_object.DiagID
        except AttributeError:
            return None

    @MKB.setter
    def MKB(self, value):
        self.MKB_object = MKB.query.filter(MKB.DiagID == value).first()

    def __json__(self):
        return {
            'id': self.id,
            'coupon': self.vmpCoupon,
            'quota_type': self.quotaDetails.quota_type,
            'patient_model': self.quotaDetails.pacient_model,
            'treatment': self.quotaDetails.treatment,
            'mkb': self.MKB_object,
        }


class VMPCoupon(db.Model):
    __tablename__ = 'VMPCoupon'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.ForeignKey('Person.id'), index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    number = db.Column(db.Integer, nullable=False)
    MKB_id = db.Column(db.ForeignKey('MKB.id'), nullable=False)
    date = db.Column(db.Date)
    quotaType_id = db.Column(db.ForeignKey('QuotaType.id'), nullable=False)
    client_id = db.Column(db.ForeignKey('Client.id'), nullable=False)
    clientQuoting_id = db.Column(db.Integer)
    fileLink = db.Column('file', db.String)

    MKB_object = db.relationship('MKB')
    quotaType = db.relationship('QuotaType')
    client = db.relationship('Client')

    def __init__(self, *args, **kwargs):
        super(VMPCoupon, self).__init__(*args, **kwargs)
        self._parsed = {}

    @property
    def MKB(self):
        return self.MKB_object.DiagID

    @MKB.setter
    def MKB(self, value):
        self.MKB_object = MKB.query.filter(MKB.DiagID == value).first()

    @property
    def parsed(self):
        return self._parsed

    @classmethod
    def from_xlsx(cls, xlsx_file):
        from nemesis.models.client import Client
        from xlsx import Workbook
        import base64
        from cStringIO import StringIO

        def read_smashed_cells(rown, cells):
            return u''.join([
                sheet_0[cell+str(rown)].value
                for cell in cells
                if sheet_0[cell+str(rown)] is not None
            ])

        xlsx_str = base64.b64decode(xlsx_file)
        f = StringIO(xlsx_str)

        book = Workbook(f)
        sheet_0 = book[1]

        self = cls()
        self.number = read_smashed_cells(10, itertools.chain('QRSTUVWXYZ', ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG']))
        self.MKB = read_smashed_cells(93, 'NOPQR')

        quota_type_code = read_smashed_cells(135, 'MNOPQRSTUVWX')
        quota_date = datetime.date(
            int(''.join(('20', sheet_0['S133'].value, sheet_0['T133'].value))),
            int(''.join((sheet_0['P133'].value, sheet_0['Q133'].value))),
            int(''.join((sheet_0['M133'].value, sheet_0['N133'].value))),
        )
        self._parsed.update({
            'quota_type_code': quota_type_code,
            'quota_date': quota_date
        })

        self.quotaType = QuotaType.query.join(QuotaCatalog).filter(
            QuotaType.code == quota_type_code,
            between(quota_date, QuotaCatalog.begDate, QuotaCatalog.endDate)
        ).first()
        self.date = datetime.date(
            int(''.join(('20', sheet_0['V137'].value, sheet_0['W137'].value))),
            int(''.join((sheet_0['S137'].value, sheet_0['T137'].value))),
            int(''.join((sheet_0['P137'].value, sheet_0['Q137'].value))),
        )

        last_name = sheet_0['H35'].value
        first_name = sheet_0['W35'].value
        patr_name = sheet_0['M37'].value
        document_type = sheet_0['S45'].value
        document_number = sheet_0['L47'].value
        birthdate = datetime.date(
            int(''.join((sheet_0['AC68'].value, sheet_0['AD68'].value, sheet_0['AE68'].value, sheet_0['AF68'].value))),
            int(''.join((sheet_0['Z68'].value, sheet_0['AA68'].value))),
            int(''.join((sheet_0['W68'].value, sheet_0['X68'].value))),
        )

        client = None
        # Round one!
        unformatted_snils = read_smashed_cells(39, itertools.chain('STUWXY', ['AA', 'AB', 'AC', 'AE', 'AF']))
        if unformatted_snils:
            client = Client.query.filter(Client.SNILS == unformatted_snils).first()
        if not client:
            # Round two!
            if first_name or last_name or birthdate:
                query = Client.query.filter(
                    Client.firstName == first_name,
                    Client.lastName == last_name,
                    Client.birthDate == birthdate,
                )
                count = query.count()
                if count > 1:
                    raise Exception(u'Слишком много совпадений по пациенту')
                elif count < 1:
                    raise Exception(u'Не найден пациент')
                client = query.first()
        if client is None:
            raise Exception(u'Не найден пациент')
        self.client = client
        return self

    def __json__(self):
        from nemesis.lib.utils import safe_traverse_attrs
        return {
            'id': self.id,
            'number': self.number,
            'mkb': self.MKB_object,
            'quota_type': self.quotaType,
            'date': self.date,
            'event': safe_traverse_attrs(self, 'clientQuoting', 'event', 'externalId'),
            'client': {'id': self.client.id,
                       'name': safe_traverse_attrs(self, 'client', 'nameText')},
            'file': self.fileLink
        }
