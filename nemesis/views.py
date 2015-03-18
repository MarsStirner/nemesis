# -*- encoding: utf-8 -*-
import urllib2
from jinja2 import TemplateNotFound

import requests

from flask import render_template, abort, request, redirect, url_for, flash, session, current_app
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed
from flask.ext.principal import identity_loaded, Permission, RoleNeed, UserNeed, ActionNeed
from flask.ext.login import login_user, logout_user, login_required, current_user
from sqlalchemy.orm import lazyload, joinedload
from itsdangerous import json

from nemesis.systemwide import login_manager, cache
from nemesis.lib.data import get_kladr_city, get_kladr_street
from nemesis.lib.utils import public_endpoint, jsonify, request_wants_json, api_method
# from application.models import *
from nemesis.utils import admin_permission
from lib.user import UserAuth, AnonymousUser, UserProfileManager
from forms import LoginForm, RoleForm
from nemesis.lib.jsonify import PersonTreeVisualizer
from nemesis.models.exists import rbUserProfile, Person
from nemesis.app import app
from nemesis.models import enums, event, actions, exists, schedule, client
from nemesis.systemwide import db


login_manager.login_view = 'login'
login_manager.anonymous_user = AnonymousUser


@app.before_request
def check_valid_login():
    if (request.endpoint and
            'static' not in request.endpoint and
            not current_user.is_admin() and
            not getattr(app.view_functions[request.endpoint], 'is_public', False)):

        login_valid = False

        auth_token = request.cookies.get(app.config['CASTIEL_AUTH_TOKEN'])
        if auth_token:
            result = requests.post(app.config['COLDSTAR_URL'] + 'cas/api/check', data=json.dumps({'token': auth_token, 'prolong': True}))
            if result.status_code == 200:
                answer = result.json()
                if answer['success']:
                    if not current_user.is_authenticated():
                        user = UserAuth.get_by_id(answer['user_id'])
                        if login_user(user):
                            session_save_user(user)
                            # Tell Flask-Principal the identity changed
                            identity_changed.send(current_app._get_current_object(), identity=Identity(answer['user_id']))
                            return redirect(request.url or UserProfileManager.get_default_url())
                        else:
                            pass
                            # errors.append(u'Аккаунт неактивен')
                    login_valid = True
                else:
                    # Remove the user information from the session
                    logout_user()
                    # Remove session keys set by Flask-Principal
                    for key in ('identity.name', 'identity.auth_type', 'hippo_user', 'crumbs'):
                        session.pop(key, None)
                    # Tell Flask-Principal the user is anonymous
                    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

        if not login_valid:
            # return redirect(url_for('login', next=request.url))
            return redirect(app.config['COLDSTAR_URL'] + 'cas/login?back=%s' % urllib2.quote(request.url))
        if not getattr(current_user, 'current_role', None) and request.endpoint != 'wm_config':
            return redirect(url_for('select_role', next=request.url))


@app.before_request
def check_user_profile_settings():
    if request.endpoint and 'static' not in request.endpoint:
        if (request.endpoint not in ('doctor_to_assist', 'api_doctors_to_assist', 'logout', 'wm_config') and
            UserProfileManager.has_ui_assistant() and
            not current_user.master
        ):
            return redirect(url_for('doctor_to_assist', next=request.url))


@app.route('/')
def index():
    default_url = UserProfileManager.get_default_url()
    if default_url != '/':
        return redirect(default_url)
    return render_template(app.config['INDEX_HTML'])


@app.route('/settings/', methods=['GET', 'POST'])
@admin_permission.require(http_exception=403)
def settings_html():
    from nemesis.models.caesar import Settings
    from wtforms import StringField
    from wtforms.validators import DataRequired
    from flask.ext.wtf import Form
    try:
        class ConfigVariablesForm(Form):
            pass

        variables = db.session.query(Settings).order_by('id').all()
        for variable in variables:
            setattr(ConfigVariablesForm,
                    variable.code,
                    StringField(variable.code, validators=[DataRequired()], default="", description=variable.name))

        form = ConfigVariablesForm()
        for variable in variables:
            form[variable.code].value = variable.value

        if form.validate_on_submit():
            for variable in variables:
                variable.value = form.data[variable.code]
            db.session.commit()
            flash(u'Настройки изменены')
            return redirect(url_for('settings_html'))

        return render_template('settings.html', form=form)
    except TemplateNotFound:
        abort(404)


@app.route('/login/', methods=['GET', 'POST'])
@public_endpoint
def login():
    # login form that uses Flask-WTF
    form = LoginForm()
    errors = list()
    # Validate form input
    if form.validate_on_submit():
        user = UserAuth.auth_user(form.login.data.strip(), form.password.data.strip())
        if user:
            # Keep the user info in the session using Flask-Login
            user.current_role = request.form['role']
            if login_user(user):
                session_save_user(user)
                # Tell Flask-Principal the identity changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                return redirect_after_user_change()
            else:
                errors.append(u'Аккаунт неактивен')
        else:
            errors.append(u'Неверная пара логин/пароль')

    return render_template('user/login.html', form=form, errors=errors)


@app.route('/api/current-user.json')
@api_method
def api_current_user():
    return current_user.export_js()


@app.route('/config.js')
def config_js():
    from nemesis.lib.settings import Settings
    settings = Settings()
    return render_template('config.js', settings=settings, config=app.config)


def session_save_user(user):
    session['hippo_user'] = user


def redirect_after_user_change():
    next_url = request.args.get('next') or request.referrer or UserProfileManager.get_default_url()
    if UserProfileManager.has_ui_assistant() and not current_user.master:
        next_url = url_for('.doctor_to_assist', next=next_url)
    return redirect(next_url)


@app.route('/select_role/', methods=['GET', 'POST'])
@public_endpoint
def select_role():
    form = RoleForm()
    errors = list()
    form.roles.choices = current_user.roles

    if form.is_submitted():
        current_user.current_role = form.roles.data
        identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
        if not UserProfileManager.has_ui_assistant() and current_user.master:
            current_user.set_master(None)
            identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
        return redirect_after_user_change()
    return render_template('user/select_role.html', form=form, errors=errors)


@app.route('/logout/')
@public_endpoint
def logout():
    # Remove the user information from the session
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type', 'hippo_user', 'crumbs'):
        session.pop(key, None)
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    token = request.cookies.get(app.config['CASTIEL_AUTH_TOKEN'])
    if token:
        requests.post(app.config['COLDSTAR_URL'] + 'cas/api/release', data=json.dumps({'token': token}))
    return redirect(request.args.get('next') or '/')


@app.route('/doctor_to_assist/', methods=['GET', 'POST'])
def doctor_to_assist():
    if request.method == "POST":
        user_id = request.json['user_id']
        profile_id = request.json['profile_id']
        master_user = UserAuth.get_by_id(user_id)
        profile = rbUserProfile.query.get(profile_id)
        master_user.current_role = (profile.code, profile.name)
        current_user.set_master(master_user)
        identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
        return jsonify({
            'redirect_url': request.args.get('next') or UserProfileManager.get_default_url()
        })
    if not UserProfileManager.has_ui_assistant():
        return redirect(UserProfileManager.get_default_url())
    return render_template('user/select_master_user.html')


@cache.memoize(86400)
def api_refbook_int(name):
    if name is None:
        return []

    for mod in (enums,):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)
            return ref_book.rb()['objects']

    for mod in (exists, schedule, actions, client, event):
        if hasattr(mod, name):
            ref_book = getattr(mod, name)

            _order = ref_book.id
            if hasattr(ref_book, '__mapper_args__') and 'order_by' in ref_book.__mapper_args__:
                _order = ref_book.__mapper_args__['order_by']

            if 'deleted' in ref_book.__dict__:
                return ref_book.query.filter_by(deleted=0).order_by(_order).all()
            else:
                return ref_book.query.order_by(_order).all()

    response = requests.get(u'{0}v1/{1}/'.format(app.config['VESTA_URL'], name))
    return [
        {'id': item['_id'], 'name': item['name'], 'code': item['code']}
        for item in response.json()['data']
    ]


@app.route('/api/rb/')
@app.route('/api/rb/<name>')
@api_method
def api_refbook(name):
    return api_refbook_int(name)


@cache.memoize(86400)
def api_roles_int(user_login):
    return UserAuth.get_roles_by_login(user_login.strip())


@app.route('/api/roles/')
@app.route('/api/roles/<user_login>')
@public_endpoint
@api_method
def api_roles(user_login):
    return api_roles_int(user_login)


@app.route('/api/doctors_to_assist')
def api_doctors_to_assist():
    viz = PersonTreeVisualizer()
    persons = db.session.query(Person).add_entity(rbUserProfile).join(Person.user_profiles).filter(
        rbUserProfile.code.in_([UserProfileManager.doctor_clinic, UserProfileManager.doctor_diag])
    ).options(
        lazyload('*'),
        joinedload(Person.speciality)
    ).order_by(
        Person.lastName,
        Person.firstName
    )
    res = [viz.make_person_with_profile(person, profile) for person, profile in persons]
    return jsonify(res)


@cache.memoize(86400)
def int_api_thesaurus(code):
    from models.exists import rbThesaurus
    flat = []

    def make(item):
        """
        :type item: rbThesaurus
        :return:
        """
        flat.append((
            item.id,
            item.group_id,
            item.code,
            item.name,
            item.template,
        ))
        map(make, rbThesaurus.query.filter(rbThesaurus.group_id == item.id))
    map(make, rbThesaurus.query.filter(rbThesaurus.code == code))
    return flat


@app.route('/api/rbThesaurus/')
@app.route('/api/rbThesaurus/<code>')
@api_method
def api_thesaurus(code=None):
    if code:
        return int_api_thesaurus(code)


@app.route('/api/kladr/city/search/')
@app.route('/api/kladr/city/search/<search_query>/')
@app.route('/api/kladr/city/search/<search_query>/<limit>/')
@cache.memoize(86400)
def kladr_search_city(search_query=None, limit=300):
    result = []
    if search_query is None:
        return jsonify([])
    response = requests.get(u'{0}kladr/psg/search/{1}/{2}/'.format(app.config['VESTA_URL'],
                                                                   search_query,
                                                                   limit))
    for city in response.json()['data']:
        data = {'code': city['identcode'], 'name': u'{0}. {1}'.format(city['shorttype'], city['name'])}
        if city['parents']:
            for parent in city['parents']:
                data['name'] = u'{0}, {1}. {2}'.format(data['name'], parent['shorttype'], parent['name'])
        result.append(data)
    return jsonify(result)


@app.route('/api/kladr/street/search/')
@app.route('/api/kladr/street/search/<city_code>/<search_query>/')
@app.route('/api/kladr/street/search/<city_code>/<search_query>/<limit>/')
@cache.memoize(86400)
def kladr_search_street(city_code=None, search_query=None, limit=100):
    result = []
    if city_code is None or search_query is None:
        return jsonify([])
    response = requests.get(u'{0}kladr/street/search/{1}/{2}/{3}/'.format(app.config['VESTA_URL'],
                                                                          city_code,
                                                                          search_query,
                                                                          limit))
    for street in response.json()['data']:
        data = {'code': street['identcode'], 'name': u'{0} {1}'.format(street['fulltype'], street['name'])}
        result.append(data)
    return jsonify(result)


@app.route('/api/kladr/city/')
@app.route('/api/kladr/city/<code>/')
@cache.memoize(86400)
def kladr_city(code=None):
    if code is None:
        return jsonify([])
    return jsonify([get_kladr_city(code)])


@app.route('/api/kladr/street/')
@app.route('/api/kladr/street/<code>/')
@cache.memoize(86400)
def kladr_street(code=None):
    if code is None:
        return jsonify([])
    return jsonify([get_kladr_street(code)])


@app.route('/clear_cache/')
def clear_cache():
    cache.clear()
    import os
    import shutil
    nginx_cache_path = '/var/cache/nginx'
    try:
        cache_list = os.listdir(nginx_cache_path)
        for _name in cache_list:
            entity_path = os.path.join(nginx_cache_path, _name)
            if os.path.isdir(entity_path):
                shutil.rmtree(entity_path)
            elif os.path.isfile(entity_path):
                os.remove(entity_path)
    except Exception as e:
        print e
    return u'Кэш справочников удалён', 200, [('content-type', 'text/plain; charset=utf-8')]


@app.errorhandler(403)
def authorisation_failed(e):
    if request_wants_json():
        return jsonify(unicode(e), result_code=403, result_name=u'Forbidden')
    flash(u'У вас недостаточно прав для доступа к функционалу')
    return render_template('user/denied.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    if request_wants_json():
        return jsonify(unicode(e), result_code=404, result_name=u'Page not found')
    flash(u'Указанный вами адрес не найден')
    return render_template('404.html'), 404


#########################################

@login_manager.user_loader
def load_user(user_id):
    # Return an instance of the User model
    # Минимизируем количество обращений к БД за данными пользователя
    hippo_user = session.get('hippo_user', None)
    if not hippo_user:
        hippo_user = UserAuth.get_by_id(int(user_id))
        session['hippo_user'] = hippo_user
    # session['hippo_user'] = hippo_user
    return hippo_user


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(identity.user, 'id'):
        identity.provides.add(UserNeed(identity.user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    # for role in getattr(identity.user, 'roles', []):
    #     identity.provides.add(RoleNeed(role[0]))
    current_role = getattr(identity.user, 'current_role', None)
    if current_role:
        identity.provides = set()
        identity.provides.add(RoleNeed(identity.user.current_role))

    user_rights = getattr(identity.user, 'rights', None)
    if isinstance(user_rights, dict):
        for right in user_rights.get(current_role, []):
            identity.provides.add(ActionNeed(right))
