# -*- coding: utf-8 -*-

import os
from flask import Blueprint, Markup, request, render_template
from itertools import chain
from os import path
from pkgutil import walk_packages
from werkzeug.utils import import_string
from werkzeug.exceptions import default_exceptions, HTTPException


def load_blueprints(app, apps_path):
    pkg_list = os.listdir(apps_path)
    base_pkg = os.path.basename(apps_path)
    if pkg_list:
        for pkg_name in pkg_list:
            if not pkg_name.startswith('__') \
                    and os.path.isdir(os.path.join(apps_path, pkg_name)) \
                    and os.path.exists(os.path.join(apps_path, pkg_name, '__init__.py')):
                register_blueprint(app, '%s.%s' % (base_pkg, pkg_name), module_name="app", blueprint_name="module")


def register_blueprint(app, app_package, module_name="app", blueprint_name="module", on_error=None):
    """Automatically load Blueprint from the specified package and registers them with Flask."""

    #TODO: simplify for our case

    if not app_package:
        raise ValueError("No apps package provided - unable to begin autoload")

    if isinstance(app_package, basestring):
        package_code = import_string(app_package)
    else:
        #: `apps_package` can be the already imported parent package
        #: (i.e. the following is a licit pattern)::
        #:
        #:      import app_package
        #:      # do something else with app_package
        #:      autoload(app, app_package)
        package_code = app_package
        app_package = app_package.__name__

    package_paths = package_code.__path__

    package_paths = [path.join(path.dirname(app.root_path), p) for p in package_paths]
    root = app_package
    app_package = app_package + u"." if not app_package.endswith(".") else app_package

    if on_error is None:
        on_error = lambda name: app.logger.warn("Unable to import {name}.".format(name=name))

    _to_import = "{base}.{module}.{symbol}"
    import_template = lambda base: _to_import.format(base=base,
                                                     module=module_name,
                                                     symbol=blueprint_name)

    #: Autoloaded apps must be Python packages
    #: The root of the package is ONLY inspected for a routing file
    package_contents = [[None, root, True]]
    for _, sub_app_name, is_pkg in package_contents:

        if not is_pkg:
            continue

        sub_app_import_path = import_template(base=sub_app_name)
        sub_app = import_string(sub_app_import_path)

        if isinstance(sub_app, Blueprint):
            app.register_blueprint(sub_app, url_prefix='/%s' % sub_app.name)
            # TODO: Check if it's necessary to import_models
            import_models(app, sub_app_name)
        else:
            app.logger.warn(("Failed to register {name} - "
                             "it does not match the registration pattern.").format(name=sub_app_name))


def import_models(app, blueprint_package_path):
    try:
        import_string('%s.models' % blueprint_package_path)
    except ImportError:
        app.logger.warn("Failed to import %s.models" % blueprint_package_path)


def import_tests(apps_path):
    pkg_list = os.listdir(apps_path)
    base_pkg = os.path.basename(apps_path)
    test_pkgs = list()
    if pkg_list:
        for pkg_path in pkg_list:
            if os.path.isdir(os.path.join(apps_path, pkg_path)):
                if os.path.isdir(os.path.join(apps_path, pkg_path, 'tests')):
                    for _test_pkg in os.listdir(os.path.join(apps_path, pkg_path, 'tests')):
                        test_pkgs.append(import_string('%s.%s.tests.%s' %
                                                       (base_pkg, pkg_path, os.path.splitext(_test_pkg)[0])))
                else:
                    test_pkgs.append(import_string('%s.%s.tests' % (base_pkg, pkg_path)))
    return test_pkgs


def setup_errors(app, error_template="errors.html"):
    def error_handler(error):
        if isinstance(error, HTTPException):
            description = error.get_description(request.environ)
            code = error.code
            name = error.name
        else:
            description = error
            code = 500
            name = "Internal Server Error"
        return render_template(error_template,
                               code=code,
                               name=Markup(name),
                               description=Markup(description))

    for exception in default_exceptions:
        app.register_error_handler(exception, error_handler)