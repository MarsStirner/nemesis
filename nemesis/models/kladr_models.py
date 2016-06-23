# -*- coding: utf-8 -*-
from nemesis.systemwide import db


class Kladr(db.Model):
    __bind_key__ = 'kladr'
    __tablename__ = 'KLADR'
    __table_args__ = (
        db.Index('long_name', 'prefix', 'NAME', 'SOCR', 'STATUS'),
        db.Index('NAME', 'NAME', 'SOCR'),
        db.Index('parent', 'parent', 'NAME', 'SOCR', 'CODE')
    )

    NAME = db.Column(db.Unicode(40), nullable=False)
    SOCR = db.Column(db.Unicode(10), nullable=False)
    CODE = db.Column(db.String(13), primary_key=True)
    INDEX = db.Column(db.String(6), nullable=False)
    GNINMB = db.Column(db.String(4), nullable=False)
    UNO = db.Column(db.String(4), nullable=False)
    OCATD = db.Column(db.String(11), nullable=False, index=True)
    STATUS = db.Column(db.String(1), nullable=False)
    parent = db.Column(db.String(13), nullable=False)
    infis = db.Column(db.String(5), nullable=False, index=True)
    prefix = db.Column(db.String(2), nullable=False)
    id = db.Column(db.Integer, nullable=False, unique=True)


class Street(db.Model):
    __bind_key__ = 'kladr'
    __tablename__ = 'STREET'
    __table_args__ = (
        db.Index('NAME_SOCR', 'NAME', 'SOCR', 'CODE'),
    )

    NAME = db.Column(db.Unicode(40), nullable=False)
    SOCR = db.Column(db.Unicode(10), nullable=False)
    CODE = db.Column(db.String(17), primary_key=True)
    INDEX = db.Column(db.String(6), nullable=False)
    GNINMB = db.Column(db.String(4), nullable=False)
    UNO = db.Column(db.String(4), nullable=False)
    OCATD = db.Column(db.String(11), nullable=False)
    infis = db.Column(db.String(5), nullable=False, index=True)


class AbstractKladrLocality(object):
    # I - IV KLADR levels
    code_len = 11
    level_digits = {
        1: 2,
        2: 5,
        3: 8,
        4: 11
    }
    invalid = None
    name = None
    code = None
    parent_code = None
    level = None
    parents = None
    fullname = None

    def get_region_code(self):
        if self.code:
            return self.code[:2].ljust(self.code_len, '0')

    def get_district_code(self):
        if self.code:
            return self.code[:5].ljust(self.code_len, '0')


class InvalidKladrLocality(AbstractKladrLocality):
    def __init__(self, message):
        self.invalid = message

    def __json__(self):
        return {
            'code': None,
            'name': self.invalid,
            'fullname': self.invalid,
            'parent_code': None
        }

    def __unicode__(self):
        return self.invalid


class KladrLocality(AbstractKladrLocality):
    def __init__(self, loc_info):
        self.code = loc_info.get('identcode')
        self.name = u'{0}. {1}'.format(loc_info['shorttype'], loc_info['name'])
        self.level = loc_info.get('level')
        self.parent_code = loc_info.get('identparent')

        self.parents = {
            p['level']: p
            for p in loc_info.get('parents', [])
            if p.get('level')
            }
        self.fullname = u', '.join(
            [u'{0}. {1}'.format(p['shorttype'], p['name']) for p in loc_info['parents']] + [self.name]
        )

    def get_parent(self, level):
        if 0 < level < self.level:
            if level not in self.parents:
                from nemesis.lib.vesta import Vesta
                code = self.code[:self.level_digits[level]].ljust(self.code_len, '0')
                new_loc = Vesta.get_kladr_locality(code)
                self.parents[level] = new_loc if new_loc.level == level else None
            return self.parents[level]

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
            'fullname': self.fullname,
            'parent_code': self.parent_code
        }

    def __unicode__(self):
        return self.fullname


class AbstractKladrStreet(object):
    code_len = 13
    invalid = None
    code = None
    name = None


class InvalidKladrStreet(AbstractKladrStreet):
    def __init__(self, message):
        self.invalid = message

    def __json__(self):
        return {
            'code': None,
            'name': self.invalid
        }

    def __unicode__(self):
        return self.invalid


class KladrStreet(AbstractKladrStreet):
    # V KLADR level
    code_len = 13

    def __init__(self, street_info):
        self.code = street_info.get('identcode')
        self.name = u'{0} {1}'.format(street_info['fulltype'], street_info['name'])

    def __json__(self):
        return {
            'code': self.code,
            'name': self.name,
        }

    def __unicode__(self):
        return self.name
