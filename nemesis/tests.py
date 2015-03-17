# -*- coding: utf-8 -*-
import unittest
from mock import Mock, patch, MagicMock
from copy import deepcopy
from nemesis.lib import apt_layout
from .app import app


class APTLayoutTestCase(unittest.TestCase):

    @patch.object(apt_layout.APTLayout, '_APTLayout__get_action')
    def test_get_default_layout(self, get_action_method):
        with app.app_context():
            mock_action = Mock()
            mock_action.actionType.name.return_value = 'test'
            mock_action.actionType.layout.template = None
            mock_action.actionType.property_types = MagicMock()

            assert_result = {'tag': 'root',
                             'attrs': {'title': mock_action.actionType.name},
                             'children': []}
            property_types = []
            for i in xrange(1, 6):
                property_type = Mock()
                property_type.id = i
                property_types.append(property_type)
                assert_result['children'].append({'tag': 'ap', 'primary': i})

            mock_action.actionType.property_types.__iter__.return_value = property_types

            get_action_method.return_value = mock_action

            layout = apt_layout.APTLayout(-1)
            result = layout.get_layout()
            self.assertDictEqual(assert_result, result)

    @patch.object(apt_layout.APTLayout, '_APTLayout__get_template')
    @patch.object(apt_layout.APTLayout, '_APTLayout__get_action')
    def test_get_layout(self, get_action_method, get_template_method):
        with app.app_context():
            mock_action = Mock()
            mock_action.actionType.name.return_value = 'test'
            mock_action.actionType.property_types = MagicMock()

            template = {'tag': 'root',
                        'attrs': {'title': mock_action.actionType.name.return_value},
                        'children': [
                            {'tag': 'ap',
                             'primary': 1,
                             'attrs': {'cols': 2}},
                            {'tag': 'ap',
                             'primary': 2,
                             'attrs': {'cols': 2}}
                        ]}

            assert_result = deepcopy(template)
            property_types = []
            for i in xrange(1, 6):
                property_type = Mock()
                property_type.id = i
                property_types.append(property_type)
                if i > 2:
                    assert_result['children'].append({'tag': 'ap', 'primary': i})

            mock_action.actionType.property_types.__iter__.return_value = property_types

            get_action_method.return_value = mock_action
            get_template_method.return_value = template

            layout = apt_layout.APTLayout(-1)
            result = layout.get_layout()
            self.assertDictEqual(assert_result, result)


if __name__ == '__main__':
    unittest.main()
