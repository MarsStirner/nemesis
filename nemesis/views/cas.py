# -*- coding: utf-8 -*-
import urllib2

import requests
from requests.exceptions import ConnectionError
from flask import render_template, abort, request, redirect, url_for, session, current_app, make_response
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, UserNeed, ActionNeed
from flask.ext.login import login_user, logout_user, current_user
from itsdangerous import json

from nemesis.systemwide import login_manager
from nemesis.lib.utils import public_endpoint
from nemesis.lib.apiutils import json_dumps, api_method, ApiException
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

        is_public_api = getattr(app.view_functions[request.endpoint], 'is_public_api', False)
        is_api = getattr(app.view_functions[request.endpoint], 'is_api', False)

        if is_public_api:
            return process_public_api_login(auth_token)
        elif is_api:
            return process_api_login(auth_token)
        else:
            return process_html_login(auth_token)


def check_cas_token(auth_token):
    if not auth_token:
        return None
    try:
        result = requests.post(
            app.config['COLDSTAR_URL'] + 'cas/api/check',
            data=json.dumps({'token': auth_token, 'prolong': True}),
            headers={'Referer': request.url.encode('utf-8')}
        )
    except ConnectionError:
        raise CasNotAvailable
    return result


def process_public_api_login(auth_token):
    # только аутентификация в cas, CurrentUser is Anonymous
    cas_response = check_cas_token(auth_token)
    if cas_response is None or cas_response.status_code != 200:
        raise ApiLoginException(401, u'Пользователь не аутентифицирован')


def process_api_login(auth_token):
    # аутентификация в cas + требование на авторизацию через отдельный запрос в /chose_role/,
    # в рамках которого будет создан CurrentUser с выбранной ролью.
    # Подразумевается, что перед обращением к мис будут проведены 2 предварительных запроса для
    # аутентификации и авторизации, после чего запросы к мис будут сопровождаться 2 соответствующими
    # куками.
    login_valid = False

    cas_response = check_cas_token(auth_token)
    if cas_response is not None and cas_response.status_code == 200:
        cas_data = cas_response.json()
        if cas_data['success']:
            valid_session = check_session_is_valid()
            if not valid_session:
                raise ApiLoginException(400, u'Ошибка данных сессии пользователя. Переавторизуйтесь.')

            user_id = cas_data['user_id']
            if not current_user.is_authenticated() or current_user.id != user_id:
                # only to pass it to 'chose_role' endpoint
                session['_user_id'] = user_id

            login_valid = True
        else:
            _logout_user()

    if not login_valid:
        raise ApiLoginException(401, u'Пользователь не аутентифицирован')

    current_role = getattr(current_user, 'current_role', None)
    if current_role is None and request.endpoint != 'chose_role':
        raise ApiLoginException(403, u'Пользователь не авторизован')


def process_html_login(auth_token):
    # аутентификация в cas + фоновое создание CurrentUser + выбор текущей роли
    # Подразумеваются, что аутентификация и авторизация производится через мис путем редиректов
    # и автоматической установкой нужных кук, а также с пользовательским взаимодействием.
    login_valid = False

    cas_response = check_cas_token(auth_token)
    if cas_response is not None and cas_response.status_code == 200:
        cas_data = cas_response.json()
        if cas_data['success']:
            valid_session = check_session_is_valid()
            if not valid_session:
                session_cookie = app.config['BEAKER_SESSION'].get('session.key')
                response = redirect(request.url)
                response.delete_cookie(session_cookie)
                return response

            user_id = cas_data['user_id']
            if not current_user.is_authenticated() or current_user.id != user_id:
                create_user_session(user_id)
                response = redirect(request.url or UserProfileManager.get_default_url())
                # Если эту строку раскомментировать, то в домене не будет работать никогда.
                # response.set_cookie(app.config['CASTIEL_AUTH_TOKEN'], auth_token)
                return response

            login_valid = True
        else:
            _logout_user()

    if not login_valid:
        # return redirect(url_for('login', next=request.url))
        return redirect(app.config['COLDSTAR_URL'] + 'cas/login?back=%s' % urllib2.quote(request.url.encode('utf-8')))

    # Для неавторизованного пользователя текущей системы (т.е. без выбранного профиля)
    current_role = getattr(current_user, 'current_role', None)
    if current_role is None and request.endpoint not in semi_public_endpoints:
        # Единственный возможный профиль выбирается сразу
        if len(current_user.roles) == 1:
            current_user.current_role = current_user.roles[0]
            identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
            if not UserProfileManager.has_ui_assistant() and current_user.master:
                current_user.set_master(None)
                identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
        # Если в аргументах url передается желаемый профиль, то попытаться его выбрать
        elif request.args.get('role') and current_user.has_role(request.args.get('role')):
            _req_role = request.args.get('role')
            if _req_role not in (UserProfileManager.doctor_otd, UserProfileManager.doctor_anest):
                current_user.current_role = current_user.find_role(_req_role)
            else:
                # Если передан врач отделения или анестезиолог, то заменяем его на врача поликлиники
                _current_role = current_user.find_role(UserProfileManager.doctor_clinic)
                if not _current_role:
                    # Если у пользователя нет роли "Врач поликлиники", пробуем заменить на роль
                    # "Мед. сестра (ассистент врача)"
                    _current_role = current_user.find_role(UserProfileManager.nurse_assist)
                current_user.current_role = _current_role
            identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
            if not UserProfileManager.has_ui_assistant() and current_user.master:
                current_user.set_master(None)
                identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))
        # Из нескольких возможных профилей нужно выбирать руками
        else:
            return redirect(url_for('select_role', next=request.url))


def check_session_is_valid():
    # Проверка на непустую куку сессии.
    # Если она пустая, то будет удалена и произойдет повтор текущего запроса,
    # что приведет к новому редиректу на форму выбора роли.
    if 'BEAKER_SESSION' in app.config:
        session_cookie = app.config['BEAKER_SESSION'].get('session.key')
        if session_cookie in request.cookies and not request.cookies.get(session_cookie):
            return False
    return True


@app.route('/')
def index():
    default_url = UserProfileManager.get_default_url()
    if default_url != url_for('index'):
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


def create_user_session(user_id):
    user = UserAuth.get_by_id(user_id)
    if login_user(user):
        session_save_user(user)
        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user_id))
    else:
        pass
        # errors.append(u'Аккаунт неактивен')


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


@app.route('/chose_role/', methods=['POST'])
@app.route('/chose_role/<role_code>', methods=['POST'])
@api_method
def chose_role(role_code=None):
    create_user_session(session.pop('_user_id'))
    if len(current_user.roles) == 0:
        raise ApiException(403, u'У текущего пользователя нет доступных ролей')
    elif len(current_user.roles) == 1:
        if role_code is not None and role_code != current_user.roles[0]:
            raise ApiException(400, u'У текущего пользователя нет роли с кодом `{0}`'.format(role_code))
        current_user.current_role = current_user.roles[0]
        current_user.current_role = role_code
    else:
        if role_code is None:
            raise ApiException(400, u'Необходимо передать код роли текущего пользователя')
        role = current_user.find_role(role_code)
        if role is False:
            raise ApiException(400, u'У текущего пользователя нет роли с кодом `{0}`'.format(role_code))
    identity_changed.send(current_app._get_current_object(), identity=Identity(current_user.id))

    session_cookie = app.config['BEAKER_SESSION'].get('session.key')
    return {
        'session_cookie': session_cookie
    }


class CasNotAvailable(Exception):
    pass


@app.errorhandler(CasNotAvailable)
def cas_not_found(e):
    return u'Нет связи с подсистемой централизованной аутентификации'


class ApiLoginException(Exception):
    """Исключение в припроверке доступа к API-функциям
    :ivar code: HTTP-код ответа
    :ivar message: текстовое пояснение ошибки
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u'<ApiException(%s, u\'%s\')>' % (self.code, self.message)


@app.errorhandler(ApiLoginException)
def api_login_error(e):
    # TODO: format like all api exceptions
    j = json_dumps({
        'code': e.code,
        'message': e.message
    })
    code = e.code
    headers = {
        'content-type': 'application/json; charset=utf-8'
    }
    return make_response(j, code, headers)


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
