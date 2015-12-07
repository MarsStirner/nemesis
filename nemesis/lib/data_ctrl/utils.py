# -*- coding: utf-8 -*-

from nemesis.app import app
from nemesis.systemwide import db
from nemesis.models.exists import Organisation


def get_default_org():
    return db.session.query(Organisation).filter_by(
        infisCode=str(app.config['ORGANISATION_INFIS_CODE'])
    ).first()