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


class KladrLocality(object):
    # I - IV KLADR levels
    code_len = 11
    level_digits = {
        1: 2,
        2: 5,
        3: 8,
        4: 11
    }

    def __init__(self, **kwargs):
        if 'invalid' in kwargs:
            self.invalid = kwargs['invalid']
            self.code = kwargs['code'] if 'code' in kwargs else None
            self.level = None
        else:
            self.code = kwargs['code'] if 'code' in kwargs else None
            self.name = kwargs['name'] if 'name' in kwargs else None
            self.level = int(kwargs['level']) if 'level' in kwargs else None
            self.parent_code = kwargs['parent_code'] if 'parent_code' in kwargs else None
        self._set_parents(kwargs.get('parents', []))

    def _set_parents(self, parent_list):
        self.parents = dict((p.level, p) for p in parent_list)
        fullname = ', '.join(
            filter(None, [
                (self.parents[level].name if level in self.parents else (self.name if self.level == level else None))
                for level in range(1, 5)
            ])
        )
        self.fullname = fullname

    def get_parent(self, level):
        if 0 < level < self.level:
            if level not in self.parents:
                from nemesis.lib.vesta import Vesta
                code = self.code[:self.level_digits[level]].ljust(self.code_len, '0')
                new_loc = Vesta.get_kladr_locality(code)
                self.parents[level] = new_loc if new_loc.level == level else None
            return self.parents[level]

    def get_region_code(self):
        if self.code:
            return self.code[:2].ljust(self.code_len, '0')

    def get_district_code(self):
        if self.code:
            return self.code[:5].ljust(self.code_len, '0')

    def __json__(self):
        if hasattr(self, 'invalid'):
            return {
                'code': self.code,
                'name': self.invalid,
                'fullname': self.invalid,
                'parent_code': self.invalid
            }
        else:
            return {
                'code': self.code,
                'name': self.name,
                'fullname': self.fullname,
                'parent_code': self.parent_code
            }

    def __unicode__(self):
        return self.invalid if hasattr(self, 'invalid') else self.fullname


class KladrStreet(object):
    # V KLADR level
    code_len = 13

    def __init__(self, **kwargs):
        if 'invalid' in kwargs:
            self.invalid = kwargs['invalid']
            self.code = kwargs['code'] if 'code' in kwargs else None
        else:
            self.code = kwargs['code'] if 'code' in kwargs else None
            self.name = kwargs['name'] if 'name' in kwargs else None

    def __json__(self):
        if hasattr(self, 'invalid'):
            return {
                'code': self.code,
                'name': self.invalid,
            }
        else:
            return {
                'code': self.code,
                'name': self.name,
            }

    def __unicode__(self):
        return self.invalid if hasattr(self, 'invalid') else self.name