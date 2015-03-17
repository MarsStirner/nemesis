# -*- coding: utf-8 -*-
import yaml
from ..systemwide import db
from ..models.actions import Action

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


class APTLayout(object):
    """
    Класс для работы с шаблонами отображения полей для заполнения ActionPropertyType

    Using: template = APTLayout(action_id).get_layout()
    """
    def __init__(self, action_id):
        self.action_id = action_id
        self.action = None
        self.layout = None

    def __get_action(self):
        return db.session.query(Action).get(int(self.action_id))

    def __get_action_property_types(self):
        self.action = self.__get_action()
        if self.action:
            return self.action.actionType.property_types
        return []

    @property
    def default_template(self):
        template = {
            'tag': 'root',
            'attrs': {
                'title': self.action.actionType.name if self.action else '',
            },
            'children': []
        }
        return template

    def __find_values(self, source_dict, key):
        for k, v in source_dict.iteritems():
            if k == key:
                yield v
            elif isinstance(v, dict):
                for result in self.__find_values(v, key):
                    yield result
            elif isinstance(v, list):
                for element in v:
                    if isinstance(element, dict):
                        for result in self.__find_values(element, key):
                            yield result

    def __get_template(self):
        template = None
        if not self.action:
            self.action = self.__get_action()
        layout = self.action.actionType.layout
        if getattr(layout, 'template', None):
            template = yaml.dump(yaml.load(layout.template))
        if not template:
            template = self.default_template
        return template

    def get_layout(self):
        property_types = self.__get_action_property_types()
        self.layout = self.__get_template()
        used_apts = list(self.__find_values(self.layout, 'primary'))
        if property_types:
            for property_type in property_types:
                if property_type.id not in used_apts:
                    self.layout['children'].append({
                        'tag': 'ap',
                        'primary': property_type.id})
        return self.layout

    def __json__(self):
        if not self.layout:
            self.get_layout()
        return self.layout