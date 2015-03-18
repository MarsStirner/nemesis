# -*- coding: utf-8 -*
from sqlalchemy import Table

from nemesis.systemwide import db
from nemesis.lib.agesex import AgeSex

# from application.models.actions import Action

organisation_mkb_assoc = Table(
    'Organisation_MKB', db.metadata,
    db.Column('mkb_id', db.ForeignKey('MKB.id')),
    db.Column('org_id', db.ForeignKey('Organisation.id')),
)


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


class rbFinance(db.Model):
    __tablename__ = 'rbFinance'

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

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


class rbTreatment(db.Model):
    __tablename__ = u'rbTreatment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.Unicode(32), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


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


class Organisation(db.Model):
    __tablename__ = 'Organisation'
    __table_args__ = (
        db.Index(u'shortName', u'shortName', u'INN', u'OGRN'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    fullName = db.Column(db.String(255), nullable=False)
    shortName = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False, index=True)
    net_id = db.Column(db.Integer, db.ForeignKey('rbNet.id'), index=True)
    infisCode = db.Column(db.String(12), nullable=False, index=True)
    obsoleteInfisCode = db.Column(db.String(60), nullable=False)
    OKVED = db.Column(db.String(64), nullable=False, index=True)
    INN = db.Column(db.String(15), nullable=False, index=True)
    KPP = db.Column(db.String(15), nullable=False)
    OGRN = db.Column(db.String(15), nullable=False, index=True)
    OKATO = db.Column(db.String(15), nullable=False)
    OKPF_code = db.Column(db.String(4), nullable=False)
    OKPF_id = db.Column(db.Integer, db.ForeignKey('rbOKPF.id'), index=True)
    OKFS_code = db.Column(db.Integer, nullable=False)
    OKFS_id = db.Column(db.Integer, db.ForeignKey('rbOKFS.id'), index=True)
    OKPO = db.Column(db.String(15), nullable=False)
    FSS = db.Column(db.String(10), nullable=False)
    region = db.Column(db.String(40), nullable=False)
    Address = db.Column(db.String(255), nullable=False)
    chief = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(255), nullable=False)
    accountant = db.Column(db.String(64), nullable=False)
    isInsurer = db.Column(db.Integer, nullable=False, index=True)
    compulsoryServiceStop = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    voluntaryServiceStop = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    area = db.Column(db.String(13), nullable=False)
    isHospital = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    notes = db.Column(db.String, nullable=False)
    head_id = db.Column(db.Integer, index=True)
    miacCode = db.Column(db.String(10), nullable=False)
    isOrganisation = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    uuid_id = db.Column(db.Integer, nullable=False, index=True, server_default=u"'0'")

    net = db.relationship('rbNet')
    OKPF = db.relationship('rbOKPF')
    OKFS = db.relationship('rbOKFS')
    mkbs = db.relationship('MKB', secondary=organisation_mkb_assoc)

    def __unicode__(self):
        return self.fullName

    def __json__(self):
        return {
            'id': self.id,
            'full_name': self.fullName,
            'short_name': self.shortName,
            'title': self.title,
            # 'net': self.net,
            'infis': self.infisCode,
            'is_insurer': bool(self.isInsurer),
            'is_hospital': bool(self.isHospital)
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
        }


class Person(db.Model):
    __tablename__ = 'Person'
    __table_args__ = (
        db.Index(u'lastName', u'lastName', u'firstName', u'patrName'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    code = db.Column(db.String(12), nullable=False)
    federalCode = db.Column(db.Unicode(255), nullable=False)
    regionalCode = db.Column(db.String(16), nullable=False)
    lastName = db.Column(db.Unicode(30), nullable=False)
    firstName = db.Column(db.Unicode(30), nullable=False)
    patrName = db.Column(db.Unicode(30), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('rbPost.id'), index=True)
    speciality_id = db.Column(db.Integer, db.ForeignKey('rbSpeciality.id'), index=True)
    org_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)
    orgStructure_id = db.Column(db.Integer, db.ForeignKey('OrgStructure.id'), index=True)
    office = db.Column(db.Unicode(8), nullable=False)
    office2 = db.Column(db.Unicode(8), nullable=False)
    tariffCategory_id = db.Column(db.Integer, db.ForeignKey('rbTariffCategory.id'), index=True)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), index=True)
    retireDate = db.Column(db.Date, index=True)
    ambPlan = db.Column(db.SmallInteger, nullable=False)
    ambPlan2 = db.Column(db.SmallInteger, nullable=False)
    ambNorm = db.Column(db.SmallInteger, nullable=False)
    homPlan = db.Column(db.SmallInteger, nullable=False)
    homPlan2 = db.Column(db.SmallInteger, nullable=False)
    homNorm = db.Column(db.SmallInteger, nullable=False)
    expPlan = db.Column(db.SmallInteger, nullable=False)
    expNorm = db.Column(db.SmallInteger, nullable=False)
    login = db.Column(db.Unicode(32), nullable=False)
    password = db.Column(db.String(32), nullable=False)
    userProfile_id = db.Column(db.Integer, index=True)
    retired = db.Column(db.Integer, nullable=False)
    birthDate = db.Column(db.Date, nullable=False)
    birthPlace = db.Column(db.String(64), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    SNILS = db.Column(db.String(11), nullable=False)
    INN = db.Column(db.String(15), nullable=False)
    availableForExternal = db.Column(db.Integer, nullable=False, server_default=u"'1'")
    primaryQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'50'")
    ownQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'25'")
    consultancyQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'25'")
    externalQuota = db.Column(db.SmallInteger, nullable=False, server_default=u"'10'")
    lastAccessibleTimelineDate = db.Column(db.Date)
    timelineAccessibleDays = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    typeTimeLinePerson = db.Column(db.Integer, nullable=False)
    maxOverQueue = db.Column(db.Integer, server_default=u"'0'")
    maxCito = db.Column(db.Integer, server_default=u"'0'")
    quotUnit = db.Column(db.Integer, server_default=u"'0'")
    academicdegree_id = db.Column(db.Integer, db.ForeignKey('rbAcademicDegree.id'))
    academicTitle_id = db.Column(db.Integer, db.ForeignKey('rbAcademicTitle.id'))

    post = db.relationship('rbPost')
    speciality = db.relationship('rbSpeciality', lazy=False)
    organisation = db.relationship('Organisation')
    org_structure = db.relationship('OrgStructure',)
    academicDegree = db.relationship('rbAcademicDegree')
    academicTitle = db.relationship('rbAcademicTitle')
    tariffCategory = db.relationship('rbTariffCategory')
    user_profiles = db.relation('rbUserProfile', secondary='Person_Profiles')

    @property
    def nameText(self):
        return u' '.join((u'%s %s %s' % (self.lastName, self.firstName, self.patrName)).split())

    @property
    def shortNameText(self):
        from nemesis.lib.utils import initialize_name
        return initialize_name(self.lastName, self.firstName, self.patrName)

    @property
    def full_name(self):
        return u'%s%s' % (self.nameText, u' (%s)' % self.speciality if self.speciality else '')

    def __unicode__(self):
        return self.nameText

    def __json__(self):
        return {
            'id': self.id,
            'name': self.nameText,
            'code': self.code,
            'birth_date': self.birthDate,
            'speciality': self.speciality,
            'federal_code': self.federalCode,
            'regional_code': self.regionalCode,
            'org_structure': self.org_structure,
            'full_name': self.full_name
        }

    def __int__(self):
        return self.id


class rbAcademicDegree(db.Model):
    __tablename__ = 'rbAcademicDegree'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbAcademicTitle(db.Model):
    __tablename__ = 'rbAcademicTitle'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }

    def __int__(self):
        return self.id


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


class rbPost(db.Model):
    __tablename__ = 'rbPost'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    regionalCode = db.Column(db.String(8), nullable=False)
    key = db.Column(db.String(6), nullable=False, index=True)
    high = db.Column(db.String(6), nullable=False)
    flatCode = db.Column(db.String(65), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'key': self.key,
            'high': self.high,
            'flat_code': self.flatCode,
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


class rbSpeciality(db.Model):
    __tablename__ = 'rbSpeciality'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    OKSOName = db.Column(db.Unicode(60), nullable=False)
    OKSOCode = db.Column(db.String(8), nullable=False)
    service_id = db.Column(db.ForeignKey('rbService.id'), index=True)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    mkbFilter = db.Column(db.String(32), nullable=False)
    regionalCode = db.Column(db.String(16), nullable=False)
    quotingEnabled = db.Column(db.Integer, server_default=u"'0'")

    service = db.relationship('rbService')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'OKSO_name': self.OKSOName,
            'OKSO_code': self.OKSOCode,
            'MKB_filter': self.mkbFilter,
            'regional_code': self.regionalCode,
            'quoting_enabled': bool(self.quotingEnabled),
        }

    def __int__(self):
        return self.id

    def __unicode__(self):
        return self.name


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

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    codePlace = db.Column(db.String(2))

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'code_place': self.codePlace,
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
    default = db.Column(db.Unicode, nullable=False)
    dpdAgreement = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    render = db.Column(db.Integer, nullable=False, server_default=u"'0'")


class rbService(db.Model):
    __tablename__ = u'rbService'
    __table_args__ = (
        db.Index(u'infis', u'infis', u'eisLegacy'),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(31), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    eisLegacy = db.Column(db.Integer, nullable=False)
    nomenclatureLegacy = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    license = db.Column(db.Integer, nullable=False)
    infis = db.Column(db.String(31), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    medicalAidProfile_id = db.Column(db.ForeignKey('rbMedicalAidProfile.id'), index=True)
    adultUetDoctor = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    adultUetAverageMedWorker = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    childUetDoctor = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    childUetAverageMedWorker = db.Column(db.Float(asdecimal=True), server_default=u"'0'")
    rbMedicalKind_id = db.Column(db.ForeignKey('rbMedicalKind.id'), index=True)
    UET = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    departCode = db.Column(db.String(3))

    medicalAidProfile = db.relationship(u'rbMedicalAidProfile')
    rbMedicalKind = db.relationship(u'rbMedicalKind')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'infis': self.infis,
            'begDate': self.begDate,
            'endDate': self.endDate,
            'adult_uet_doctor': self.adultUetDoctor,
            'adult_uet_average_medical_worker': self.adultUetAverageMedWorker,
            'child_uet_doctor': self.childUetDoctor,
            'child_uet_average_medical_worker': self.childUetAverageMedWorker,
            'uet': self.UET,
            'department_code': self.departCode,
            'medical_aid_profile': self.medicalAidProfile,
            'medical_kind': self.rbMedicalKind,
        }

    def __int__(self):
        return self.id


class rbRequestType(db.Model):
    __tablename__ = u'rbRequestType'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    relevant = db.Column(db.Integer, nullable=False, server_default=u"'1'")

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'relevant': bool(self.relevant)
        }

    def __int__(self):
        return self.id


class rbResult(db.Model):
    __tablename__ = u'rbResult'

    id = db.Column(db.Integer, primary_key=True)
    eventPurpose_id = db.Column(db.ForeignKey('rbEventTypePurpose.id'), nullable=False, index=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    continued = db.Column(db.Integer, nullable=False)
    regionalCode = db.Column(db.String(8), nullable=False)

    eventPurpose = db.relationship(u'rbEventTypePurpose')

    def __json__(self):
        return {
            'id': self.id,
            'eventPurpose_id': self.eventPurpose_id,
            'code': self.code,
            'name': self.name,
            'continued': bool(self.continued),
            'regional_code': self.regionalCode,
            'event_purpose': self.eventPurpose
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


class Contract(db.Model):
    __tablename__ = u'Contract'

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    number = db.Column(db.String(64), nullable=False)
    date = db.Column(db.Date, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    recipientAccount_id = db.Column(db.Integer, db.ForeignKey('Organisation_Account.id'), index=True)
    recipientKBK = db.Column(db.String(30), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), index=True)
    payerAccount_id = db.Column(db.Integer, db.ForeignKey('Organisation_Account.id'), index=True)
    payerKBK = db.Column(db.String(30), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    finance_id = db.Column(db.Integer, db.ForeignKey('rbFinance.id'), nullable=False, index=True)
    grouping = db.Column(db.String(64), nullable=False)
    resolution = db.Column(db.String(64), nullable=False)
    format_id = db.Column(db.Integer, index=True)
    exposeUnfinishedEventVisits = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    exposeUnfinishedEventActions = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    visitExposition = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    actionExposition = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    exposeDiscipline = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    priceList_id = db.Column(db.Integer)
    coefficient = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    coefficientEx = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")

    recipient = db.relationship(u'Organisation', foreign_keys='Contract.recipient_id')
    payer = db.relationship(u'Organisation', foreign_keys='Contract.payer_id')
    finance = db.relationship(u'rbFinance')
    recipientAccount = db.relationship(u'OrganisationAccount', foreign_keys='Contract.recipientAccount_id')
    payerAccount = db.relationship(u'OrganisationAccount', foreign_keys='Contract.payerAccount_id')
    specifications = db.relationship(u'ContractSpecification',
                                     primaryjoin="and_(ContractSpecification.master_id == Contract.id, ContractSpecification.deleted == 0)")
    contingent = db.relationship(u'ContractContingent',
                                 primaryjoin="and_(ContractContingent.master_id == Contract.id, ContractContingent.deleted == 0)")
    tariff = db.relationship('ContractTariff',
                             primaryjoin='and_(ContractTariff.master_id == Contract.id, ContractTariff.deleted == 0)')

    def __unicode__(self):
        return u'%s %s' % (self.number, self.date)

    def __json__(self):
        return {
            'id': self.id,
            'number': self.number,
            'date': self.date,
            'begDate': self.begDate,
            'endDate': self.endDate,
            'grouping': self.grouping,
            'resolution': self.resolution,
            # format_id = db.Column(db.Integer, index=True)
            'exposeUnfinishedEventVisits': bool(self.exposeUnfinishedEventVisits),
            'exposeUnfinishedEventActions': bool(self.exposeUnfinishedEventActions),
            'visitExposition': self.visitExposition,
            'actionExposition': self.actionExposition,
            'exposeDiscipline': self.exposeDiscipline,
            # priceList_id = db.Column(db.Integer)
            'coefficient': float(self.coefficient),
            'coefficientEx': float(self.coefficientEx),

            'recipient': self.recipient,
            'recipientKBK': self.recipientKBK,
            'recipientAccount': self.recipientAccount,

            'payer': self.payer,
            'payerKBK': self.payerKBK,
            'payerAccount': self.payerAccount,

            'finance': self.finance,
            'specifications': self.specifications,
            'contingent': self.contingent
        }

    def __int__(self):
        return self.id


class ContractContingent(db.Model):
    __tablename__ = u'Contract_Contingent'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), nullable=False, index=True)
    client_id = db.Column(db.Integer, index=True)
    attachType_id = db.Column(db.Integer, index=True)
    org_id = db.Column(db.Integer, index=True)
    socStatusType_id = db.Column(db.Integer, index=True)
    insurer_id = db.Column(db.Integer, index=True)
    policyType_id = db.Column(db.Integer, index=True)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)

    def __json__(self):
        return {
            'id': self.id,
            'master_id': self.master_id,
            'client_id': self.client_id,
            'insurer_id': self.insurer_id,
            'org_id': self.org_id,
            'policyType_id': self.policyType_id,
            'sex': self.sex
        }


class ContractContragent(db.Model):
    __tablename__ = u'Contract_Contragent'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.Integer, nullable=False, index=True)
    insurer_id = db.Column(db.Integer, nullable=False, index=True)
    payer_id = db.Column(db.Integer, nullable=False, index=True)
    payerAccount_id = db.Column(db.Integer, nullable=False, index=True)
    payerKBK = db.Column(db.String(30), nullable=False)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)


class ContractSpecification(db.Model):
    __tablename__ = u'Contract_Specification'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), nullable=False, index=True)
    eventType_id = db.Column(db.Integer, db.ForeignKey('EventType.id'), nullable=False, index=True)

    def __json__(self):
        return {
            'id': self.id,
            'master_id': self.master_id,
            'event_type_id': self.eventType_id
        }


class ContractTariff(db.Model):
    __tablename__ = u'Contract_Tariff'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.Integer, db.ForeignKey('Contract.id'), nullable=False, index=True)
    eventType_id = db.Column(db.Integer, index=True)
    tariffType = db.Column(db.Integer, nullable=False)
    service_id = db.Column(db.Integer, index=True)
    code = db.Column(db.Unicode(64), nullable=True)
    name = db.Column(db.Unicode(256), nullable=True)
    tariffCategory_id = db.Column(db.Integer, index=True)
    begDate = db.Column(db.Date, nullable=False)
    endDate = db.Column(db.Date, nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    age = db.Column(db.String(9), nullable=False)
    age_bu = db.Column(db.Integer)
    age_bc = db.Column(db.SmallInteger)
    age_eu = db.Column(db.Integer)
    age_ec = db.Column(db.SmallInteger)
    unit_id = db.Column(db.Integer, index=True)
    amount = db.Column(db.Float(asdecimal=True), nullable=False)
    uet = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    price = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    limitationExceedMode = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    limitation = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    priceEx = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")
    MKB = db.Column(db.String(8), nullable=False)
    rbServiceFinance_id = db.Column(db.ForeignKey('rbServiceFinance.id'), index=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer)

    rbServiceFinance = db.relationship(u'rbServiceFinance')


class OrganisationAccount(db.Model):
    __tablename__ = u'Organisation_Account'

    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('Organisation.id'), nullable=False, index=True)
    bankName = db.Column(db.Unicode(128), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String, nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('Bank.id'), nullable=False, index=True)
    cash = db.Column(db.Integer, nullable=False)

    org = db.relationship(u'Organisation')
    bank = db.relationship(u'Bank')

    def __json__(self):
        return {
            'id': self.id,
            'bank_name': self.bankName,
            'name': self.name,
            'notes': self.notes,
            'cash': self.cash,
            # 'organisation': self.org,
            'bank': self.bank,
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


class rbUserProfile(db.Model):
    __tablename__ = u'rbUserProfile'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)
    withDep = db.Column(db.Integer, nullable=False, server_default=u"'0'")

    rights = db.relationship(u'rbUserRight', secondary=u'rbUserProfile_Right', lazy=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
        }


class rbUserProfileRight(db.Model):
    __tablename__ = u'rbUserProfile_Right'

    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.ForeignKey('rbUserProfile.id'), nullable=False, index=True)
    userRight_id = db.Column(db.ForeignKey('rbUserRight.id'), nullable=False, index=True)


class rbUserRight(db.Model):
    __tablename__ = u'rbUserRight'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, index=True)


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


class PersonProfiles(db.Model):
    __tablename__ = u'Person_Profiles'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.ForeignKey('Person.id'), nullable=False, index=True)
    userProfile_id = db.Column(db.ForeignKey('rbUserProfile.id'), nullable=False, index=True)


class vrbPersonWithSpeciality(db.Model):
    __tablename__ = u'vrbPersonWithSpeciality'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), nullable=False, index=True)
    name = db.Column(db.String(101), nullable=False, index=True)
    orgStructure_id = db.Column(db.ForeignKey('OrgStructure.id'))
    speciality_id = db.Column(db.ForeignKey('rbSpeciality.id'))

    orgStructure = db.relationship('OrgStructure', lazy='joined')
    speciality = db.relationship('rbSpeciality', lazy='joined')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'org_structure': self.orgStructure,
            'speciality': self.speciality,
            'short_name': self.name
        }

    def __int__(self):
        return self.id


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
    finance_id = db.Column(db.ForeignKey('rbFinance.id'), nullable=False, index=True)
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


class QuotaType(db.Model):
    __tablename__ = u'QuotaType'

    id = db.Column(db.Integer, primary_key=True)
    catalog_id = db.Column(db.ForeignKey('QuotaCatalog.id'), nullable=False, index=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    class_ = db.Column(u'class', db.Integer, nullable=False)
    profile_code = db.Column(db.String(16))
    group_code = db.Column(db.String(16))
    type_code = db.Column(db.String(16))
    code = db.Column(db.String(16), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    teenOlder = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float(asdecimal=True), nullable=False, server_default=u"'0'")

    def __unicode__(self):
        return self.name


class VMPQuotaDetails(db.Model):
    __tablename__ = u'VMPQuotaDetails'

    id = db.Column(db.Integer, primary_key=True)
    pacientModel_id = db.Column(db.ForeignKey('rbPacientModel.id'), nullable=False, index=True)
    treatment_id = db.Column(db.ForeignKey('rbTreatment.id'), nullable=False, index=True)
    quotaType_id = db.Column(db.ForeignKey('QuotaType.id'), nullable=False, index=True)


class MKB_VMPQuotaFilter(db.Model):
    __tablename__ = u'MKB_VMPQuotaFilter'

    id = db.Column(db.Integer, primary_key=True)
    MKB_id = db.Column(db.ForeignKey('MKB.id'), nullable=False, index=True)
    quotaDetails_id = db.Column(db.ForeignKey('VMPQuotaDetails.id'), nullable=False, index=True)


class ClientQuoting(db.Model):
    __tablename__ = u'Client_Quoting'
    __table_args__ = (
        db.Index(u'deleted_prevTalon_event_id', u'deleted', u'prevTalon_event_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False)
    createPerson_id = db.Column(db.Integer, index=True)
    modifyDatetime = db.Column(db.DateTime, nullable=False)
    modifyPerson_id = db.Column(db.Integer, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    master_id = db.Column(db.ForeignKey('Client.id'), index=True)
    identifier = db.Column(db.Unicode(16))
    quotaTicket = db.Column(db.Unicode(20))
    quotaDetails_id = db.Column(db.ForeignKey('VMPQuotaDetails.id'), nullable=False, index=True)
    stage = db.Column(db.Integer)
    directionDate = db.Column(db.DateTime, nullable=False)
    freeInput = db.Column(db.Unicode(128))
    org_id = db.Column(db.Integer)
    amount = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    MKB = db.Column(db.Unicode(8), nullable=False)
    status = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    request = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    statment = db.Column(db.Unicode(255))
    dateRegistration = db.Column(db.DateTime, nullable=False)
    dateEnd = db.Column(db.DateTime, nullable=False)
    orgStructure_id = db.Column(db.Integer)
    regionCode = db.Column(db.String(13), index=True)
    event_id = db.Column(db.Integer, index=True)
    prevTalon_event_id = db.Column(db.Integer)
    version = db.Column(db.Integer, nullable=False)

    master = db.relationship(u'Client')