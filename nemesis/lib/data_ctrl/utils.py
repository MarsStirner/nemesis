# -*- coding: utf-8 -*-

from nemesis.app import app
from nemesis.systemwide import db
from nemesis.models.exists import Organisation
from nemesis.models.person import Person


def get_default_org():
    return db.session.query(Organisation).filter_by(
        infisCode=str(app.config['ORGANISATION_INFIS_CODE'])
    ).first()


def get_system_mail_person_id():
    res = db.session.query(Person.id).filter(Person.code == 'automail').first()
    return res[0] if res is not None else None