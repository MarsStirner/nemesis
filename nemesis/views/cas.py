# -*- coding: utf-8 -*-
import urllib2

import requests
from requests.exceptions import ConnectionError
from flask import render_template, abort, request, redirect, url_for, session, current_app
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, UserNeed, ActionNeed
from flask.ext.login import login_user, logout_user, current_user
from itsdangerous import json

from nemesis.systemwide import login_manager
from nemesis.lib.utils import public_endpoint
from nemesis.lib.user import UserAuth, AnonymousUser, UserProfileManager
from nemesis.forms import LoginForm, RoleForm
from nemesis.app import app

__author__ = 'viruzzz-kun'


semi_public_endpoints = ('config_js', 'current_user_js', 'select_role', 'logout')

login_manager.login_view = 'login'
login_manager.anonymous_user = AnonymousUser


@app.before_request
def check_user_profile_settings():
    free_endpoints = ('doctor_to_assist', 'api_doctors_to_assist') + semi_public_endpoints
    if request.endpoint and 'static' not in request.endpoint:
        if (request.endpoint not in free_endpoints and
                UserProfileManager.has_ui_assistant() and
                not current_user.master):
            return redirect(url_for('doctor_to_assist', next=request.url))


@app.before_request
def check_valid_login():
    if (request.endpoint and 'static' not in request.endpoint and
            not getattr(app.view_functions[request.endpoint], 'is_public', False)):

        login_valid = False

        # На доменах кука дублируется для всех поддоменов/хостов, поэтому получить её из dict'а невозможно - попадает
        # наименее специфичное значение. Надо разбирать вручную и брать первое.
        auth_token = None
        http_cookie = request.environ.get('HTTP_COOKIE')
        if http_cookie:
            for cook in http_cookie.split(';'):
                name, value = cook.split('=', 1)
                if name.strip() == app.config['CASTIEL_AUTH_TOKEN']:
                    auth_token = value.strip()
                    break

        if request.method == 'GET' and 'token' in request.args and request.args.get('token') != auth_token:
            auth_token = request.args.get('token')
            # убираем token из url, чтобы при протухшем токене не было циклического редиректа на CAS
            query = '&'.join(u'{0}={1}'.format(key, value) for (key, value) in request.args.items() if key != 'token')
            request.url = u'{0}?{1}'.format(request.base_url, query)

            # если нет токена, то current_user должен быть AnonymousUser
            if not isinstance(current_user._get_current_object(), AnonymousUser):
                _logout_user()

        if auth_token:
            try:
                result = requests.post(
                    app.config['COLDSTAR_URL'] + 'cas/api/check',
                    data=json.dumps({'token': auth_token, 'prolong': True}),
                    headers={'Referer': request.url.encode('utf-8')}
                )
            except ConnectionError:
                raise CasNotAvailable
            else:
                if result.status_code == 200:
                    answer = result.json()
                    if answer['success']:
                        if ('BEAKER_SESSION' in app.config and
                                    app.config['BEAKER_SESSION'].get('session.key') in request.cookies and
                                not request.cookies.get(app.config['BEAKER_SESSION'].get('session.key'))):
                            response = redirect(request.url)
                            response.delete_cookie(app.config['BEAKER_SESSION'].get('session.key'))
                            return response
                        if not current_user.is_authenticated() or current_user.id != answer['user_id']:
                            user = UserAuth.get_by_id(answer['user_id'])
                            if login_user(user):
                                session_save_user(user)
                                # Tell Flask-Principal the identity changed
                                identity_changed.send(current_app._get_current_object(), identity=Identity(answer['user_id']))
                                response = redirect(request.url or UserProfileManager.get_default_url())
                                # Если эту строку раскомментировать, то в домене не будет работать никогда.
                                # response.set_cookie(app.config['CASTIEL_AUTH_TOKEN'], auth_token)
                                return response
                            else:
                                pass
                                # errors.append(u'Аккаунт неактивен')
                        login_valid = True
                    else:
                        _logout_user()

        if not login_valid:
            # return redirect(url_for('login', next=request.url))
            return redirect(app.config['COLDSTAR_URL'] + 'cas/login?back=%s' % urllib2.quote(request.url.encode('utf-8')))
        if not getattr(current_user, 'current_role', None) and request.endpoint not in semi_public_endpoints:
            if len(current_user.roles) == 1:
                current_user.current_role = current_user.roles[0]
                identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
                if not UserProfileManager.has_ui_assistant() and current_user.master:
                    current_user.set_master(None)
                    identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
            elif request.args.get('role') and current_user.has_role(request.args.get('role')):
                _req_role = request.args.get('role')
                if _req_role not in (UserProfileManager.doctor_otd, UserProfileManager.doctor_anest):
                    current_user.current_role = current_user.find_role(_req_role)
                else:
                    # Если передан врач отделения или анестезиолог, то заменяем его на врача поликлиники
                    _current_role = current_user.find_role(UserProfileManager.doctor_clinic)
                    if not _current_role:
                        # Если у пользователя нет роли "Врач поликлиники", пробуем заменить на роль "Мед. сестра (ассистент врача)"
                        _current_role = current_user.find_role(UserProfileManager.nurse_assist)
                    current_user.current_role = _current_role
                identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
                if not UserProfileManager.has_ui_assistant() and current_user.master:
                    current_user.set_master(None)
                    identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
            else:
                return redirect(url_for('select_role', next=request.url))


@app.route('/')
def index():
    default_url = UserProfileManager.get_default_url()
    if default_url != '/':
        return redirect(default_url)
    return render_template(app.config['INDEX_HTML'])


@app.route('/login/', methods=['GET', 'POST'])
def login():
    abort(404)
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


def session_save_user(user):
    session['hippo_user'] = user


def redirect_after_user_change():
    next_url = request.args.get('next') or request.referrer or UserProfileManager.get_default_url()
    if UserProfileManager.has_ui_assistant() and not current_user.master:
        next_url = url_for('.doctor_to_assist', next=next_url)
    return redirect(next_url)


@app.route('/select_role/', methods=['GET', 'POST'])
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
    _logout_user()
    response = redirect(request.args.get('next') or '/')
    token = request.cookies.get(app.config['CASTIEL_AUTH_TOKEN'])
    if token:
        requests.post(app.config['COLDSTAR_URL'] + 'cas/api/release', data=json.dumps({'token': token}))
        response.delete_cookie(app.config['CASTIEL_AUTH_TOKEN'])
    if 'BEAKER_SESSION' in app.config:
        response.delete_cookie(app.config['BEAKER_SESSION'].get('session.key'))
    return response


class CasNotAvailable(Exception):
    pass


@app.errorhandler(CasNotAvailable)
def cas_not_found(e):
    return u'Нет связи с подсистемой централизованной аутентификации'


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


def _logout_user():
    # Remove the user information from the session
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type', 'hippo_user', 'crumbs'):
        session.pop(key, None)
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
