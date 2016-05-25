# -*- coding: utf-8 -*-
import datetime
import functools
import logging
import uuid

from functools import wraps
from decimal import Decimal

from pytz import timezone
from flask import current_app, request, abort, json, session, make_response
from flask.ext.principal import Permission, RoleNeed, ActionNeed, PermissionDenied
from flask.ext.login import current_user
from sqlalchemy import func

from nemesis.systemwide import db
from nemesis.app import app
# from nemesis.models.exists import rbUserProfile, UUID, rbCounter, rbAccountingSystem
# from nemesis.models.client import Client, ClientIdentification


logger = logging.getLogger('simple')


def public_endpoint(function):
    function.is_public = True
    return function


def public_api(func):
    func.is_public_api = True
    return func


def breadcrumb(view_title):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            title = view_title
            if request.path == u'/patients/patient':
                client_id = request.args['client_id']
                if client_id == u'new':
                    title = u"Новый пациент"
                else:
                    from nemesis.models.client import Client
                    client = Client.query.get(client_id)
                    title = client.nameText if client else ''
            elif request.path == u'/event/event.html':
                title = u"Редактирование обращения"
            session_crumbs = session.setdefault('crumbs', [])

            titles = [item[1] for item in session_crumbs]
            if (request.url, title) in session_crumbs:
                index = session_crumbs.index((request.url, title))
                session['crumbs'] = session_crumbs[:index+1]
            elif title in titles:
                index = titles.index(title)
                del session['crumbs'][index]
                session_crumbs.append((request.url, title))
            else:
                session_crumbs.append((request.url, title))
            # Call the view
            rv = f(*args, **kwargs)
            return rv
        return decorated_function
    return decorator
#
# def create_config_func(module_name, config_table):
#
#     def _config(code):
#         """Возвращает значение конфигурационной переменной, полученной из таблицы %module_name%_config"""
#         #Get app_settings
#         app_settings = dict()
#         try:
#             for item in db.session.query(Settings).all():
#                 app_settings.update({item.code: item.value})
#             # app_settings = {item.code: item.value for item in db.session.query(Settings).all()}
#         except Exception, e:
#             print e
#
#         config = getattr(g, '%s_config' % module_name, None)
#         if not config:
#             values = db.session.query(config_table).all()
#             config = dict()
#             for value in values:
#                 config[value.code] = value.value
#             setattr(g, '%s_config' % module_name, config)
#         config.update(app_settings)
#         return config.get(code, None)
#
#     return _config


class Bunch:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


_roles = dict()
_permissions = dict()


@app.before_first_request
def init_roles():
    from nemesis.models.person import rbUserProfile
    user_roles = db.session.query(rbUserProfile).all()
    if user_roles:
        for role in user_roles:
            if role.code:
                _roles[role.code] = Permission(RoleNeed(role.code))
                # _roles[role.code].name = role.name
            for right in getattr(role, 'rights', []):
                if right.code and right.code not in _permissions:
                    _permissions[right.code] = Permission(ActionNeed(right.code))
                    # _permissions[right.code].name = right.name
    # roles = Bunch(**_roles)
    # permissions = Bunch(**_permissions)


def roles_require(*role_codes):
    http_exception = 403

    def factory(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if current_user.is_admin():
                return func(*args, **kwargs)
            checked_roles = list()
            for role_code in role_codes:
                if role_code in _roles:
                    role_permission = _roles[role_code]
                    role_permission.require(http_exception)
                    if role_permission.can():
                        return func(*args, **kwargs)
                    checked_roles.append(role_permission)
            if http_exception:
                abort(http_exception, checked_roles)
            raise PermissionDenied(checked_roles)
        return decorator

    return factory


def rights_require(*right_codes):
    http_exception = 403

    def factory(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            if current_user.is_admin():
                return func(*args, **kwargs)
            checked_rights = list()
            for right_code in right_codes:
                if right_code in _permissions:
                    right_permission = _permissions[right_code]
                    right_permission.require(http_exception)
                    if right_permission.can():
                        return func(*args, **kwargs)
                    checked_rights.append(right_permission)
            if http_exception:
                abort(http_exception, checked_rights)
            raise PermissionDenied(checked_rights)
        return decorator

    return factory


class WebMisJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            try:
                return timezone(app.config['TIME_ZONE']).localize(o).astimezone(tz=timezone('UTC')).isoformat()
            except OverflowError:
                return o.isoformat()
        elif isinstance(o, (datetime.date, datetime.time)):
            return o.isoformat()
        elif isinstance(o, Decimal):
            return float(o)
        elif hasattr(o, '__json__'):
            return o.__json__()
        elif isinstance(o, db.Model) and hasattr(o, '__unicode__'):
            return unicode(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = WebMisJsonEncoder


def jsonify_int(obj, result_code=200, result_name='OK', indent=None):
    """
    Преобразование объекта к стандартному json-ответу с данными и метаданными без формирования http-ответа
    :param obj: сериализуемый объект
    :param result_code: код результата
    :param result_name: наименование результата
    :return: json-строка
    :type obj: any
    :type result_code: int
    :type result_name: str|unicode
    :rtype: str
    """
    return json.dumps({
        'result': obj,
        'meta': {
            'code': result_code,
            'name': result_name,
        }
    }, indent=indent, cls=WebMisJsonEncoder, encoding='utf-8', ensure_ascii=False)


def jsonify_response(body, result_code=200, extra_headers=None):
    """
    Формирование http-ответа из json-ифицированного тела
    :param body: json-ифицированное тело (jsonify_int)
    :param result_code: http-код результата
    :param extra_headers: дополнительные http-заголовки
    :return: flask response
    :type body: str
    :type result_code: int
    :type extra_headers: list
    :rtype: flask.wrappers.Response
    """
    headers = [('content-type', 'application/json; charset=utf-8')]
    if extra_headers:
        headers.extend(extra_headers)
    return make_response((body, result_code, headers))


def jsonify(obj, result_code=200, result_name='OK', extra_headers=None, indent=None):
    """
    Convenience-функция, преобразуцющая объект к стандартному http-json-ответу
    :param obj: сериализуемый объект
    :param result_code: код результата, http-код
    :param result_name: наименование результата
    :param extra_headers: дополнительные заголовки
    :return: flask response
    :type obj: any
    :type result_code: int
    :type result_name: str|unicode
    :type extra_headers: list
    :rtype: flask.wrappers.Response
    """
    return jsonify_response(jsonify_int(obj, result_code, result_name, indent), result_code, extra_headers)


# TODO: разобратсья c декоратором @crossdomain
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, datetime.timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return functools.update_wrapper(wrapped_function, f)
    return decorator


def safe_unicode(obj):
    if obj is None:
        return None
    return unicode(obj)


def safe_int(obj):
    if obj is None:
        return None
    return int(obj)


def safe_dict(obj):
    if obj is None:
        return None
    elif isinstance(obj, dict):
        for k, v in obj.iteritems():
            obj[k] = safe_dict(v)
        return obj
    elif hasattr(obj, '__json__'):
        return safe_dict(obj.__json__())
    return obj


def string_to_datetime(date_string, formats=None):
    if formats is None:
        formats = ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S+00:00', '%Y-%m-%dT%H:%M:%S.%f+00:00')
    elif not isinstance(formats, (tuple, list)):
        formats = (formats, )

    if date_string:
        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(date_string, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError
        return timezone('UTC').localize(dt).astimezone(tz=timezone(app.config['TIME_ZONE'])).replace(tzinfo=None)
    else:
        return date_string


def safe_datetime(val):
    if not val:
        return None
    if isinstance(val, basestring):
        try:
            val = string_to_datetime(val)
        except ValueError:
            try:
                val = string_to_datetime(val, '%Y-%m-%d')
            except ValueError:
                return None
        return val
    elif isinstance(val, datetime.datetime):
        return val
    elif isinstance(val, datetime.date):
        return datetime.datetime(val.year, val.month, val.day)
    else:
        return None


def safe_date(val):
    if not val:
        return None
    if isinstance(val, basestring):
        try:
            val = string_to_datetime(val)
        except ValueError:
            try:
                val = string_to_datetime(val, '%Y-%m-%d')
            except ValueError:
                return None
        return val.date()
    elif isinstance(val, datetime.datetime):
        return val.date()
    elif isinstance(val, datetime.date):
        return val
    else:
        return None


def safe_time_as_dt(val):
    if not val:
        return None
    if isinstance(val, basestring):
        for fmt in ('%H:%M:%S', '%H:%M'):
            try:
                val = datetime.datetime.strptime(val, fmt)
                break
            except ValueError:
                continue
        return val
    elif isinstance(val, datetime.datetime):
        return val
    else:
        return None


def safe_time(val):
    if not val:
        return None
    val = safe_time_as_dt(val)
    if isinstance(val, datetime.datetime):
        return val.time()
    else:
        return None


def safe_traverse(obj, *args, **kwargs):
    """Безопасное копание вглубь dict'а
    @param obj: точка входя для копания
    @param *args: ключи, по которым надо проходить
    @param default=None: возвращаемое значение, если раскопки не удались
    @rtype: any
    """
    default = kwargs.get('default', None)
    if obj is None:
        return default
    if len(args) == 0:
        raise ValueError(u'len(args) must be > 0')
    elif len(args) == 1:
        return obj.get(args[0], default)
    else:
        return safe_traverse(obj.get(args[0]), *args[1:], **kwargs)


def safe_traverse_attrs(obj, *args, **kwargs):
    default = kwargs.get('default', None)
    if obj is None:
        return default
    if len(args) == 0:
        raise ValueError(u'len(args) must be > 0')
    elif len(args) == 1:
        return getattr(obj, args[0], default)
    else:
        return safe_traverse_attrs(getattr(obj, args[0]), *args[1:], **kwargs)


def safe_bool(val):
    if isinstance(val, (str, unicode)):
        return val.lower() not in ('0', 'false', '\x00', '')
    return bool(val)


def safe_double(val):
    if val is None:
        return None
    if isinstance(val, basestring):
        val = val.replace(',', '.')
    try:
        val = float(val)
    except ValueError:
        val = None
    return val


def safe_decimal(val):
    if val is None:
        return None
    val = Decimal(str(val))
    return val


def format_money(val, scale=2):
    if val is None:
        return None
    if isinstance(val, Decimal):
        twoplaces = Decimal(10) ** -scale
        val = val.quantize(twoplaces)
    return '{{0:.{0}f}}'.format(scale).format(val)


def safe_uuid(val):
    if not isinstance(val, basestring):
        return None
    u_obj = uuid.UUID(val)
    return u_obj


def safe_hex_color(val):
    if not isinstance(val, basestring):
        return None
    if val.startswith('#') and len(val) == 7:
        return val[1:]


def format_hex_color(val):
    if not isinstance(val, basestring):
        return None
    if len(val) == 6:
        val = '#' + val
    if val.startswith('#') and len(val) == 7:
        return val


def format_date(d):
    if isinstance(d, datetime.date):
        return d.strftime('%d.%m.%Y')
    else:
        return d


def parse_json(json_string):
    try:
        result = json.loads(json_string)
    except ValueError:
        result = None
    return result


def get_utc_datetime_with_tz(dt=None):
    """Получить датувремя в ютс с таймзоной.
    С последующим .isoformat() результат будет в таком же формате,
    как в запросе из браузера"""
    if not dt:
        dt = datetime.datetime.now()
    dt_with_tz = timezone(app.config['TIME_ZONE']).localize(dt)
    return dt_with_tz.astimezone(timezone('UTC'))


def get_new_uuid():
    """Сгенерировать новый uuid уникальный в пределах бд.
    @rtype: application.models.exist.UUID
    """
    from nemesis.models.exists import UUID

    uuid_model = UUID()
    # paranoia mode on
    unique = False
    while not unique:
        new_uuid = str(uuid.uuid4())
        unique = uuid_model.query.filter_by(uuid=new_uuid).count() == 0
    uuid_model.uuid = new_uuid

    return uuid_model


def get_new_event_ext_id(event_type_id, client_id):
    """Формирование externalId (номер обращения/истории болезни)."""
    from nemesis.models.event import EventType
    et = EventType.query.get(event_type_id)
    if not et.counter_id:
        return ''

    from nemesis.models.exists import rbCounter
    counter = rbCounter.query.filter_by(id=et.counter_id).with_for_update().first()
    if not counter:
        return ''
    external_id = _get_external_id_from_counter(counter.prefix,
                                                counter.value + 1,
                                                counter.separator,
                                                client_id)
    counter.value += 1
    db.session.add(counter)
    return external_id


def _get_external_id_from_counter(prefix, value, separator, client_id):
    def get_date_prefix(val):
        val = val.replace('Y', 'y').replace('m', 'M').replace('D', 'd')
        if val.count('y') not in [0, 2, 4] or val.count('M') > 2 or val.count('d') > 2:
            return None
        # qt -> python date format
        _map = {'yyyy': '%Y', 'yy': '%y', 'mm': '%m', 'dd': '%d'}
        try:
            format_ = _map.get(val, '%Y')
            date_val = datetime.date.today().strftime(format_)
            check = datetime.datetime.strptime(date_val, format_)
        except ValueError, e:
            logger.error(e, exc_info=True)
            return None
        return date_val

    def get_id_prefix(val):
        if val == '':
            return str(client_id)
        from nemesis.models.client import ClientIdentification
        from nemesis.models.exists import rbAccountingSystem
        ext_val = ClientIdentification.query.join(rbAccountingSystem).filter(
            ClientIdentification.client_id == client_id, rbAccountingSystem.code == val).first()
        return ext_val.identifier if ext_val else None

    prefix_types = {'date': get_date_prefix, 'id': get_id_prefix}

    prefix_parts = prefix.split(';')
    prefix = []
    for p in prefix_parts:
        for t in prefix_types:
            pos = p.find(t)
            if pos == 0:
                val = p[len(t):]
                if val.startswith('(') and val.endswith(')'):
                    val = prefix_types[t](val[1:-1])
                    if val:
                        prefix.append(val)
    return separator.join(prefix + ['%d' % value])


def request_wants_json():
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def parse_id(request_data, identifier, allow_empty=False):
    """
    :param request_data:
    :param identifier:
    :param allow_empty:
    :return: None - empty identifier (new entity), False - parse error, int - correct identifier
    """
    _id = request_data.get(identifier)
    if _id is None and allow_empty or _id == 'new':
        return None
    elif _id is None and not allow_empty:
        return False
    else:
        try:
            _id = int(_id)
        except ValueError:
            return False
    return _id


def initialize_name(last_name, first_name, patr_name):
    last_name, first_name, patr_name = [name if name else u'' for name in (last_name, first_name, patr_name)]
    words = first_name.split() + patr_name.split()
    initials = ['%s.' % word[0].upper() for word in words if word]
    return u'%s %s' % (last_name, u' '.join(initials))


from sqlalchemy.sql import expression
from sqlalchemy.ext import compiler


class group_concat(expression.FunctionElement):
    name = "group_concat"


@compiler.compiles(group_concat) # , 'mysql'
def _group_concat_mysql(element, cmplr, **kw):
    if len(element.clauses) == 2:
        separator = cmplr.process(element.clauses.clauses[1])
    elif len(element.clauses) == 1:
        separator = ','
    else:
        raise SyntaxError(u'group_concat must have 1 or 2 arguments!')

    return 'GROUP_CONCAT({0} SEPARATOR {1})'.format(
        cmplr.process(element.clauses.clauses[0]),
        separator,
    )


def transfer_fields(src, dst, names):
    for name in names:
        setattr(dst, name, getattr(src, name))


def blend(dest, src):
    """
    Слияние двух dict'ов
    :param dest: приёмник
    :type dest: dict
    :param src: исочник
    :type src: dict
    :return: None
    """
    for k, v in src.iteritems():
        if k not in dest:
            dest[k] = {}
        if isinstance(v, dict):
            blend(dest[k], v)
        else:
            dest[k] = v


def encode_file_name(filename):
    if isinstance(filename, unicode):
        filename = filename.encode('utf-8')
    return filename


def get_max_item_attribute_value(model, attr):
    """
    Получение максимального значения атрибута сущности из бд.
    :param model: класс модели
    :type model: db.Model
    :param attr: атрибут модели
    :type attr: db.Column
    :return: max value или None
    :rtype: int? | None
    """
    selectable = db.select((func.max(attr), ), from_obj=model)
    if hasattr(model, 'deleted'):
        selectable.append_whereclause(model.deleted == 0)
    row = db.session.execute(selectable).first()
    if not row:
        return None
    return row[0]


def bail_out(exc):
    """
    Extremely small function to bail out with exception
    @type exc: Exception
    @raise: exc
    """
    raise exc
