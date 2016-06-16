# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_cache import Cache

__author__ = 'viruzzz-kun'

module = Blueprint('rb', __name__)
rb_cache = Cache()
