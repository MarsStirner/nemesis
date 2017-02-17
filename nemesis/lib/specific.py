# coding: utf-8

from nemesis.lib.utils import safe_traverse
from nemesis.app import app


class NemesisSpecificsManager(object):
    @classmethod
    def update_vesta_search_kwargs(cls, collection_name, kwargs):
        extra_kwargs = safe_traverse(app.config, 'system_prefs', 'vesta_specific_search', collection_name, default={})
        kwargs.update(extra_kwargs)
