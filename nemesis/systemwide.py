# -*- coding: utf-8 -*-
from flask.ext.babel import Babel
from flask.ext.beaker import BeakerSession
from flask.ext.login import LoginManager
from flask.ext.principal import Principal
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.cache import Cache

db = SQLAlchemy()

cache = Cache(config={'CACHE_TYPE': 'simple'})

babel = Babel()

principal = Principal()

login_manager = LoginManager()

beaker_session = BeakerSession()