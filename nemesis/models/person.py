# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import Table

from nemesis.models.utils import safe_current_user_id
from nemesis.systemwide import db


class Person(db.Model):
    __tablename__ = 'Person'
    __table_args__ = (
        db.Index(u'lastName', u'lastName', u'firstName', u'patrName'),
    )

    id = db.Column(db.Integer, primary_key=True)
    createDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    createPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id)
    modifyDatetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    modifyPerson_id = db.Column(db.Integer, index=True, default=safe_current_user_id, onupdate=safe_current_user_id)
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
    uuid_id = db.Column(db.Integer, db.ForeignKey('UUID.id'), nullable=False, index=True, server_default=u"'0'")

    post = db.relationship('rbPost')
    speciality = db.relationship('rbSpeciality', lazy=False)
    organisation = db.relationship('Organisation')
    org_structure = db.relationship('OrgStructure')
    academicDegree = db.relationship('rbAcademicDegree')
    academicTitle = db.relationship('rbAcademicTitle')
    tariffCategory = db.relationship('rbTariffCategory')
    user_profiles = db.relation('rbUserProfile', secondary='Person_Profiles')
    uuid = db.relationship('UUID')
    curation_levels = db.relationship('rbOrgCurationLevel', secondary='PersonCuration')

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

    @property
    def subscriptions(self):
        return list(sub.object_id for sub in self._subscriptions)

    def subscribe(self, object_id):
        if object_id in self.subscriptions:
            return
        from .useraccount import UserSubscriptions
        s = UserSubscriptions()
        s.person = self
        s.object_id = object_id
        db.session.add(s)

    def unsubscribe(self, object_id):
        object_list = [s for s in self._subscriptions if s.object_id == object_id]
        if object_list:
            self._subscriptions.remove(object_list[0])

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
            'organisation': self.organisation,
            'full_name': self.full_name,
            'snils': self.SNILS,
            'inn': self.INN,
            'short_name': self.shortNameText
        }

    def __int__(self):
        return self.id


class rbSpeciality(db.Model):
    __tablename__ = 'rbSpeciality'
    _table_description = u'Специальности'

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
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

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
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id

    def __unicode__(self):
        return self.name


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


class rbPost(db.Model):
    __tablename__ = 'rbPost'
    _table_description = u'Должности'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), nullable=False, index=True)
    name = db.Column(db.Unicode(64), nullable=False, index=True)
    regionalCode = db.Column(db.String(8), nullable=False)
    key = db.Column(db.String(6), nullable=False, index=True)
    high = db.Column(db.String(6), nullable=False)
    flatCode = db.Column(db.String(65), nullable=False)
    deleted = db.Column(db.SmallInteger, nullable=False, server_default='0')

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'regional_code': self.regionalCode,
            'key': self.key,
            'high': self.high,
            'flat_code': self.flatCode,
            'deleted': self.deleted
        }

    def __int__(self):
        return self.id


class PersonProfiles(db.Model):
    __tablename__ = u'Person_Profiles'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.ForeignKey('Person.id'), nullable=False, index=True)
    userProfile_id = db.Column(db.ForeignKey('rbUserProfile.id'), nullable=False, index=True)


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


class vrbPersonWithSpeciality(db.Model):
    __tablename__ = u'vrbPersonWithSpeciality'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), nullable=False, index=True)
    deleted = db.Column(db.Integer, nullable=False, server_default=u"'0'")
    name = db.Column(db.String(101), nullable=False, index=True)
    orgStructure_id = db.Column(db.ForeignKey('OrgStructure.id'))
    speciality_id = db.Column(db.ForeignKey('rbSpeciality.id'))
    org_id = db.Column(db.ForeignKey('Organisation.id'))

    orgStructure = db.relationship('OrgStructure', lazy='joined')
    speciality = db.relationship('rbSpeciality', lazy='joined')
    org = db.relationship('Organisation')

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


class rbOrgCurationLevel(db.Model):
    __tablename__ = u'rbOrgCurationLevel'
    _table_description = u'Уровень курирования ЛПУ'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Unicode(16), index=True, nullable=False)
    name = db.Column(db.Unicode(64), nullable=False)

    def __json__(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name
        }


class PersonCurationAssoc(db.Model):
    __tablename__ = u'PersonCuration'

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('Person.id'), nullable=False, index=True)
    orgCurationLevel_id = db.Column(db.Integer, db.ForeignKey('rbOrgCurationLevel.id'), nullable=False, index=True)

    person = db.relationship('Person')
    org_curation_level = db.relationship('rbOrgCurationLevel')