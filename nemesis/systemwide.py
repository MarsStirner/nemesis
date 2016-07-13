# -*- coding: utf-8 -*-
from flask_babel import Babel
from flask_beaker import BeakerSession
from flask_login import LoginManager
from flask_principal import Principal
from flask_sqlalchemy import SQLAlchemy
from flask_cache import Cache
from flask_celery import Celery


db = SQLAlchemy()

cache = Cache(config={'CACHE_TYPE': 'simple'})

babel = Babel()

principal = Principal()

login_manager = LoginManager()

beaker_session = BeakerSession()

celery = Celery()