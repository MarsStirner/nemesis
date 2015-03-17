# -*- coding: utf-8 -*-
import os
import sys
import unittest
from werkzeug.utils import import_string


def run_tests():
    my_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(my_dir, '../')))
    from nemesis.app import app
    from nemesis.autoload import import_tests

    module = import_string('application.tests')
    suite = unittest.TestLoader().loadTestsFromModule(module)
    unittest.TextTestRunner(verbosity=2).run(suite)

    tests = import_tests(app.config['BLUEPRINTS_DIR'])
    if tests:
        for module_test in tests:
            suite = unittest.TestLoader().loadTestsFromModule(module_test)
            unittest.TextTestRunner(verbosity=2).run(suite)
