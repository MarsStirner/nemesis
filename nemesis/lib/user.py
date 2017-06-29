# -*- coding: utf-8 -*-

import hashlib
import re

from flask import url_for
from flask_login import UserMixin, AnonymousUserMixin, current_user

from nemesis.lib.const import PASSPORT_DOC_TYPE_CODE, RESIDENCE_DOC_TYPE_CODE, \
    STATIONARY_MOVING_CODE, STATIONARY_LEAVED_CODE, STATIONARY_HOSP_BED_CODE
from nemesis.systemwide import db
from nemesis.lib.utils import safe_traverse_attrs, initialize_name
from nemesis.models.exists import Person, vrbPersonWithSpeciality
from nemesis.app import app
from ..models.actions import ActionType_User
from ..models.exists import rbUserProfile

from nemesis.models.enums import ActionStatus, ContragentType
from nemesis.lib.settings import Settings
from nemesis.lib.user_rights import (urEventPoliclinicPaidCreate, urEventPoliclinicOmsCreate,
                                     urEventPoliclinicDmsCreate, urEventDiagnosticPaidCreate,
                                     urEventDiagnosticBudgetCreate, urEventAllAdmPermCreate,
                                     urEventPoliclinicPaidClose, urEventPoliclinicOmsClose,
                                     urEventPoliclinicDmsClose, urEventDiagnosticPaidClose,
                                     urEventDiagnosticBudgetClose, urEventAllAdmPermSetExecDate,
                                     urEventInvoiceAccessAll, urEventPoliclinicOmsMoCreate,
                                     urSetPersonChange, urEventPoliclinicOmsMoClose, urEventClinicClose,
                                     urEventClinicCreate, urEventHospitalClose, urEventHospitalCreate,
                                     urEventVmpCouponExpChange)


class User(UserMixin):
    def __init__(self, person):
        if not isinstance(person, Person):
            raise AttributeError(u'Not instance of models.Person')
        self.deleted = 0
        self.__dict__.update(dict((key, value)
                                  for key, value in person.__dict__.iteritems()
                                  if not callable(value) and not key.startswith('_')))
        self.roles = list()
        self._current_role = None
        self._current_role_name = None
        self.rights = dict()
        self.current_rights = []
        self.post = dict()
        if person.post_id:
            self.post.update(dict((key, value)
                             for key, value in person.post.__dict__.iteritems()
                             if not callable(value) and not key.startswith('_')))
        self.org_structure = person.org_structure if person.orgStructure_id else None
        self.set_roles_rights(person)

        orgStructure = person.org_structure
        atos = set()
        while orgStructure:
            atos.add(orgStructure.id)
            orgStructure = orgStructure.parent if orgStructure.inheritActionTypes else None
        self.action_type_org_structures = atos
        self.action_type_personally = []
        self.info = vrbPersonWithSpeciality.query.get(self.id)
        self.master = None

    @property
    def current_role(self):
        return getattr(self, '_current_role', None)

    @current_role.setter
    def current_role(self, value):
        """
        @type value: str|tuple
        :param value: profile_code|(profile_code, profile_name)
        """
        if isinstance(value, tuple):
            code, name = value
        else:
            code, name = value, ''
        if not code:
            return
        self._current_role = code
        self._current_role_name = name
        self.action_type_personally = [
            record.actionType_id
            for record in ActionType_User.query.outerjoin(rbUserProfile).filter(db.or_(
                ActionType_User.person_id == self.id,
                rbUserProfile.code == code
            ))
        ]
        self.current_rights = self.rights[code]

    def is_active(self):
        return self.deleted == 0

    def is_admin(self):
        return getattr(self, 'current_role', None) == 'admin'

    def role_in(self, *args):
        roles = []
        for arg in args:
            if isinstance(arg, list):
                roles.extend(arg)
            elif isinstance(arg, tuple):
                roles.extend(list(arg))
            else:
                roles.append(arg)
        return self.current_role in roles

    def has_role(self, role):
        # what about list?
        for r in self.roles:
            if r[0] == role:
                return True
        return False

    def find_role(self, role):
        # what about list?
        for r in self.roles:
            if r[0] == role:
                return r
        return False

    def has_right(self, *rights):
        current_rights = set(self.current_rights)
        if self.master:
            return any(
                (right in current_rights and self.master.has_right(right))
                for right in rights
            )
        else:
            return any((right in current_rights) for right in rights)

    def id_any_in(self, *id_list):
        my_ids = [self.id]
        if self.master:
            my_ids.append(self.master.id)
        return any(id_ in my_ids for id_ in id_list)

    def set_roles_rights(self, person):
        if person.user_profiles:
            for role in person.user_profiles:
                self.roles.append((role.code, role.name))
                if role.rights:
                    self.rights[role.code] = list()
                    for right in role.rights:
                        self.rights[role.code].append(right.code)

    def set_master(self, master_user):
        self.master = master_user

    def get_main_user(self):
        return self.master or self

    def format_name(self, is_master=False):
        if is_master:
            return u'{0}, {1}'.format(
                initialize_name(self.lastName, self.firstName, self.patrName),
                safe_traverse_attrs(self.speciality, 'name', default='')
            )
        else:
            return u'{0} {1}'.format(self.lastName, self.firstName)

    def export_js(self):
        return {
            'id': self.id,
            'roles': self.roles,
            'is_admin': self.is_admin(),
            'current_role': self.current_role,
            'rights': self.rights,
            'action_type_org_structures': sorted(getattr(self, 'action_type_org_structures', set())),
            'action_type_personally': sorted(getattr(self, 'action_type_personally', [])),
            'info': getattr(self, 'info', {}),
            'master': self.master.export_js() if self.master else None
        }


class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False

    def get_main_user(self):
        return self

    def export_js(self):
        return {
            'id': None,
            'roles': [],
            'is_admin': self.is_admin(),
            'current_role': None,
            'rights': [],
        }


class UserAuth():
    @classmethod
    def auth_user(cls, login, password):
        person = cls.__get_by_login(login)
        if person and cls.__check_password(person.password, password):
            return User(person)
        return None

    @classmethod
    def get_by_id(cls, person_id):
        return User(Person.query.get(person_id))

    @classmethod
    def __get_by_login(cls, login):
        person = db.session.query(Person).filter(Person.login == login).first()
        if person:
            return person
        return None

    @classmethod
    def __check_password(cls, pw_hash, password):
        password = password.encode('utf-8')
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def __prepare_user(cls, pw_hash, password):
        password = password.encode('utf-8')
        return pw_hash == hashlib.md5(password).hexdigest()

    @classmethod
    def get_by_id(cls, user_id):
        return User(db.session.query(Person).get(int(user_id)))

    @classmethod
    def get_roles_by_login(cls, login):
        from ..models.exists import rbUserProfile, PersonProfiles
        return [
            {'code': role.code, 'name': role.name}
            for role in (rbUserProfile.query
                         .join(PersonProfiles)
                         .join(Person)
                         .filter(Person.login == login)
                         .order_by(rbUserProfile.name))
        ]


modeRights = (
    u'Assessment',
    u'Diagnostic',
    u'Treatment',
    u'Action'  # Общего плана, поступление-движение-выписка
)


class UserUtils(object):
    @staticmethod
    def can_create_event(event, out_msg=None):
        if out_msg is None:
            out_msg = {'message': u'ok'}

        base_msg = u'У пользователя нет прав на создание обращений типа %s'
        event_type = event and event.eventType
        event_type_err_msg = base_msg % unicode(event_type)
        errors_stack = []
        if not event_type:
            errors_stack.append(u'У обращения не указан тип')
        if current_user.has_right('adm'):
            return True
        # есть ли ограничения на создание обращений определенных EventType
        if event.is_day_hospital:
            if not current_user.has_right(urEventClinicCreate):
                errors_stack.append(event_type_err_msg)
        elif event.is_all_day_hospital:
            if not current_user.has_right(urEventHospitalCreate):
                errors_stack.append(event_type_err_msg)
        elif event.is_policlinic and event.is_paid:
            if not current_user.has_right(urEventPoliclinicPaidCreate):
                errors_stack.append(event_type_err_msg)
        elif event.is_policlinic and (event.is_oms or event.is_oms_mo):
            if event.is_oms and not current_user.has_right(urEventPoliclinicOmsCreate):
                errors_stack.append(event_type_err_msg)
            if event.is_oms_mo and not current_user.has_right(urEventPoliclinicOmsMoCreate):
                errors_stack.append(event_type_err_msg)

            client = event.client
            if not client.reg_address:
                errors_stack.append(u'Адрес регистрации не задан')
            if not re.match("^.[^.].*$", client.firstName):
                errors_stack.append(u'Имя пациента не должно содержать инициалы')
            if client.patrName and not re.match("^.[^.].*$", client.patrName):
                errors_stack.append(u'Отчество пациента не должно содержать инициалы')
            if client.SNILS == '':
                errors_stack.append(u'СНИЛС должен быть заполнен')
            if not client.document:
                errors_stack.append(u'Не задан документ удостоверяющий личность')
            else:
                if client.document.documentType.code not in [PASSPORT_DOC_TYPE_CODE, RESIDENCE_DOC_TYPE_CODE]:
                    errors_stack.append(u'Документ удостоверяюший личность должен быть паспорт РФ или вид на жительство')
                if not client.document.serial:
                    errors_stack.append(u'Не задана серия документа удостоверяющего личность')
                if not client.document.number:
                    errors_stack.append(u'Не задан номер документа удостоверяющего личность')
                if not client.document.date:
                    errors_stack.append(u'Не задана дата выдачи документа удостоверяющего личность')
            if not (client.policy and client.policy.is_valid(event.setDate)):
                errors_stack.append(u'Нет действующего полиса ОМС')
            else:
                if not client.policy.number:
                    errors_stack.append(u'Номер полиса ОМС не задан')
                if not client.policy.serial:
                    errors_stack.append(u'Серия полиса ОМС не задана')
                if not client.policy.insurer:
                    errors_stack.append(u'Страховая медицинская организация не задана')
        elif event.is_policlinic and event.is_dms:
            if not current_user.has_right(urEventPoliclinicDmsCreate):
                errors_stack.append(event_type_err_msg)
        elif event.is_diagnostic and event.is_paid:
            if not current_user.has_right(urEventDiagnosticPaidCreate):
                errors_stack.append(event_type_err_msg)
        elif event.is_diagnostic and event.is_budget:
            if not current_user.has_right(urEventDiagnosticBudgetCreate):
                errors_stack.append(event_type_err_msg)
        if event.is_adm_permission:
            if not current_user.has_right(urEventAllAdmPermCreate):
                errors_stack.append(event_type_err_msg)

        if errors_stack:
            errors_stack = map(lambda err: u'<span class="text-bold">{0}</span>'.format(err), errors_stack)
            out_msg['message'] = u'<br/>' + u',<br/>'.join(errors_stack)
            return False
        # все остальные можно
        return True

    @staticmethod
    def can_set_event_exec_date(event):
        event_type = event and event.eventType
        if not event_type:
            return False
        if current_user.has_right('adm'):
            return True
        elif event.is_adm_permission:
            if current_user.has_right(urEventAllAdmPermSetExecDate):
                return True
        return False

    @staticmethod
    def can_read_event(event):
        return event and (
            current_user.has_right('adm') or event.deleted == 0
        )

    @staticmethod
    def can_edit_event(event):
        return event and (
            current_user.has_right('adm') or ((
                event.is_closed and
                current_user.id_any_in(event.createPerson_id, event.execPerson_id) and
                current_user.has_right('evtEditClosed')
            ) or (
                not event.is_closed and current_user.has_right('clientEventUpdate')
            ))  # TODO: or check exec_person.id?
        )

    @staticmethod
    def can_read_dignoses(event):
        return event and (
            current_user.has_right('adm') or (
                UserProfileManager.has_ui_doctor() and not event.is_diagnostic
            )
        )

    @staticmethod
    def can_edit_dignoses(event):
        return event and (
            current_user.has_right('adm') or (
                UserProfileManager.has_ui_doctor() and not UserProfileManager.has_ui_diag_doctor()
            )
        )

    @staticmethod
    def can_delete_event(event, out_msg=None):
        if out_msg is None:
            out_msg = {'message': u'ok'}

        if not event:
            out_msg['message'] = u'Обращение еще не создано'
            return False
        if current_user.has_right('adm'):
            return True

        if not current_user.has_right('evtDelWithInvoices'):
            from nemesis.lib.data_ctrl.accounting.invoice import InvoiceController
            invoice_ctrl = InvoiceController()
            has_invoice = invoice_ctrl.check_event_has_invoice(event.id)
            if has_invoice:
                out_msg['message'] = u'В обращении есть выставленные счета'
                return False

        if current_user.has_right('evtDelAll'):
            return True
        elif current_user.has_right('evtDelOwn') and not event.is_closed:
            if current_user.id_any_in(event.execPerson_id, event.createPerson_id):
                for action in event.actions:
                    # Проверка, что все действия не были изменены после создания обращения
                    # или, что не появилось новых действий
                    if action.modifyPerson_id != event.createPerson_id:
                        out_msg['message'] = u'В обращении были созданы новые или отредактированы первоначальные ' \
                                             u'документы'
                        return False
                    # не закрыто
                    if action.status == ActionStatus.finished[0]:
                        out_msg['message'] = u'В обращении есть закрытые документы'
                        return False
                return True
        out_msg['message'] = u'У пользователя нет прав на удаление обращения'
        return False

    @staticmethod
    def can_close_event(event, out_msg=None):
        """
        Имеет доступ к закрытию обращения (проверяются права)
        """
        if out_msg is None:
            out_msg = {'message': u'ok'}

        base_msg = u'У пользователя нет прав на закрытие обращений типа %s'
        event_type = event and event.eventType
        if not event:
            out_msg['message'] = u'Обращение еще не создано'
            return False
        if event.is_closed:
            out_msg['message'] = u'Обращение уже закрыто'
            return False
        if current_user.has_right('adm'):
            return True
        # Состояние пользователя
        if not current_user.id_any_in(event.execPerson_id, event.createPerson_id):
            out_msg['message'] = u'Пользователь не является создателем или ответственным за обращение'
            return False
        # есть ли ограничения на закрытие обращений определенных EventType
        if event.is_day_hospital:
            if not current_user.has_right(urEventClinicClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_all_day_hospital:
            if not current_user.has_right(urEventHospitalClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_policlinic and event.is_paid:
            if not current_user.has_right(urEventPoliclinicPaidClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_policlinic and event.is_oms:
            if not current_user.has_right(urEventPoliclinicOmsClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_policlinic and event.is_oms_mo:
            if not current_user.has_right(urEventPoliclinicOmsMoClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_policlinic and event.is_dms:
            if not current_user.has_right(urEventPoliclinicDmsClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_diagnostic and event.is_paid:
            if not current_user.has_right(urEventDiagnosticPaidClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False
        elif event.is_diagnostic and event.is_budget:
            if not current_user.has_right(urEventDiagnosticBudgetClose):
                out_msg['message'] = base_msg % unicode(event_type)
                return False

        # все остальные можно
        return True

    @staticmethod
    def can_perform_close_event(event, final_step=False, out_msg=None):
        """
        Имеет возможность закрыть обращение - все данные в обращении
        и связанные сущности приведены в состояние, удовлетворяющему
        признаку закрытия.

        final_step - True если предполагается, что обращение уже находится
            в итоговом состоянии для закрытия и сохранения;
            False - если необходимо проверять только часть параметров, а
            оставшиеся данные будут редактироваться на форме закрытия обращения.
        """
        if out_msg is None:
            out_msg = {'message': u'ok'}
        errors = []
        warnings = []

        # main attributes
        if final_step and not event.execDate:
            errors.append(u'Не задана дата закрытия')
        if final_step and not event.result:
            errors.append(u'Не задан результат')
        if final_step and Settings.getBool('Event.mandatoryResult') and not event.is_diagnostic and \
                not event.rbAcheResult:
            errors.append(u'Не задан исход заболевания/госпитализации')

        if event.is_stationary:
            # leaved
            from nemesis.lib.data import get_action
            leaved = get_action(event, STATIONARY_LEAVED_CODE)
            if not leaved:
                errors.append(u'Необходимо добавить "Выписной эпикриз"')

            # unclosed movings
            movings = [action for action in event.actions
                       if action.actionType.flatCode == STATIONARY_MOVING_CODE]
            if not movings:
                errors.append(u'Необходимо наличие минимум одного движения пациента')
            for moving in movings:
                if not moving[STATIONARY_HOSP_BED_CODE].value:
                    errors.append(u'Имеются движения без выбранной койки: разместите '
                        u'пациента на койке и закройте движение пациента в отделении')
                    break
            for moving in movings:
                if moving.status != ActionStatus.finished[0]:
                    errors.append(u'Имеются незакрытые движения: закройте движение '
                        u'пациента в отделении')
                    break

        # diagnoses
        from nemesis.lib.diagnosis import get_events_diagnoses
        event_diags = get_events_diagnoses([event.id]).get(event.id, {})
        # check main or final diagnosis exists
        found = False
        for mkb, types_info in event_diags.iteritems():
            if found:
                break
            for d_type, d_kind in types_info.iteritems():
                if d_type == 'final' or d_kind == 'main':
                    found = True
                    break
        if not found:
            errors.append(u'Необходимо указать основной или заключительный диагноз')
        # check diag results
        # TODO: check diagnostic.ache_result filled if rbDiagnosisTypeN.require_result
        # + diag's kind should not be 'associated'

        # check unclosed actions
        unclosed_a = []
        for action in event.actions:
            if action.status != ActionStatus.finished[0]:
                unclosed_a.append(action.actionType.name)
        if unclosed_a:
            msg = (
                u'Следующие документы не закрыты:<br> * {0}<br><br>'
                u'Продолжить процесс закрытия обращения и запретить '
                u'редактирование всех незакрытых документов?'
            ).format(u'<br> * '.join(unclosed_a))
            warnings.append(msg)

        if warnings:
            out_msg['warnings_message'] = u'<br>'.join(warnings)

        if errors:
            msg = (
                u'Невозможно закрыть обращение:<br> * {0}<br><br>'
            ).format(u'<br> * '.join(errors))
            out_msg['message'] = msg
            return False

        return True

    @staticmethod
    def can_delete_action(action):
        return action and (
            # админу можно всё
            current_user.has_right('adm') or (
                # остальным - только если обращение не закрыто
                not action.event.is_closed and (
                    # либо есть право на удаление любых действий
                    current_user.has_right('actDelAll') or (
                        # либо только своих
                        current_user.has_right('actDelOwn') and (
                            current_user.id_any_in(action.createPerson_id, action.person_id))))))

    @staticmethod
    def can_create_action(event_id, at_id, class_=None):
        from nemesis.models.event import Event
        from nemesis.models.actions import ActionType
        event = Event.query.get_or_404(event_id)
        class_ = class_ if class_ is not None else ActionType.query.get_or_404(at_id).class_
        createRight = u'client%sCreate' % modeRights[class_]
        return (current_user.has_right('adm') or (
                not event.is_closed and current_user.has_right(createRight)))

    @staticmethod
    def can_edit_action(action, ignore_status=False):
        updateRight = u'client%sUpdate' % modeRights[action.actionType.class_]
        return action and (
            # ещё не сохранённое действие можно редактировать, в том и суть
            not action.id or
            # админу можно всё
            current_user.has_right('adm') or (
                # действие является шаблоном действия
                not action.event) or (
                # действие не закрыто, но если это автосейв, то пофигу
                (ignore_status or action.status < 2) and
                # остальным - только если обращение не закрыто
                not action.event.is_closed and (
                    # либо есть право редактировать любые действия
                    current_user.has_right('editOtherpeopleAction') or (
                        # либо право на свои определённых классов
                        current_user.has_right(updateRight) and
                        current_user.id_any_in(action.createPerson_id, action.person_id)))))

    @staticmethod
    def can_read_action(action):
        readRight = u'client%sRead' % modeRights[action.actionType.class_]
        return action and (
            current_user.has_right('adm') or (
                current_user.has_right(readRight) and
                current_user.id_any_in(action.createPerson_id, action.person_id)))

    @staticmethod
    def can_read_actions_meddoc(event):
        readRight = u'client%sRead' % modeRights[0]
        return event and (
            current_user.has_right('adm') or (
                current_user.has_right(readRight)
            )
        )

    @staticmethod
    def can_read_actions_diagnostic(event):
        readRight = u'client%sRead' % modeRights[1]
        return event and (
            current_user.has_right('adm') or (
                current_user.has_right(readRight)
            )
        )

    @staticmethod
    def can_read_actions_lab(event):
        readRight = u'client%sRead' % modeRights[1]
        return event and (
            current_user.has_right('adm') or (
                current_user.has_right(readRight)
            )
        )

    @staticmethod
    def can_read_actions_treatment(event):
        readRight = u'client%sRead' % modeRights[2]
        return event and (
            current_user.has_right('adm') or (
                current_user.has_right(readRight)
            )
        )

    @staticmethod
    def access_invoices_all(event):
        return event and (
            current_user.has_right('adm') or (
                current_user.has_right(urEventInvoiceAccessAll)
            )
        )

    @staticmethod
    def can_create_invoice(contract, out_msg=None):
        if out_msg is None:
            out_msg = {'message': u'ok'}

        errors = []
        payer = contract.payer
        if not payer:
            errors.append('В договоре не указан плательщик')
        elif payer.get_type().value == ContragentType.individual[0]:
            client = payer.client
            if not client.has_contact_email() and not client.has_contact_mobile_phone():
                errors.append(u'не указан адрес электронной почты или мобильный телефон')
        if errors:
            out_msg['message'] = u'Невозможно сформировать счёт: ' + u'; '.join(errors)
            return False
        return True

    @property
    def can_change_set_person(self):
        return (current_user.has_right('adm') or (
                current_user.has_right(urSetPersonChange)
        ))

    @property
    def can_change_vmp_coupon(self):
        return (current_user.has_right('adm') or (
                current_user.has_right(urEventVmpCouponExpChange)
        ))


class UserProfileManager(object):
    user = None

    admin = 'admin'  # Администратор
    reg_clinic = 'clinicRegistrator'  # Регистратор поликлиники
    doctor_clinic = 'clinicDoctor'  # Врач поликлиники
    doctor_diag = 'diagDoctor'  # Врач диагностики
    doctor_stat = 'statDoctor'  # Врач медицинский статистик
    doctor_otd = 'strDoctor'  # Врач отделения
    doctor_anest = 'anestezDoctor'  # Врач отделения
    nurse_admission = 'admNurse'  # Медсестра приемного отделения
    nurse_assist = 'assistNurse'  # Медсестра (ассистент врача)
    nurse = 'strNurse'  # Медсестра отделения (постовая медсестра)
    cashier = 'kassir'  # Кассир
    obstetrician = 'obstetrician'  # Акушер-гинеколог
    overseer1 = 'overseer1'
    overseer2 = 'overseer2'
    overseer3 = 'overseer3'
    ambulance = 'ambulance'

    ui_groups = {
        'doctor': [admin, doctor_clinic, doctor_diag, nurse_assist, doctor_otd],
        'diag_doctor': [admin, doctor_diag, nurse_assist],
        'registrator': [admin, reg_clinic, doctor_otd],
        'adm_nurse': [admin, nurse_admission],
        'station_nurse': [admin, nurse],
        'registrator_cashier': [admin, reg_clinic, cashier],
        'cashier': [admin, cashier],
        'obstetrician': [admin, obstetrician],
        'risar': [admin, obstetrician, overseer1, overseer2, overseer3, ambulance],
        'overseers': [admin, overseer1, overseer2, overseer3],
        'overseers_low': [admin, overseer1, overseer2],
        'overseers_high': [admin, overseer3],
        'nurse': [admin, nurse]
    }

    @classmethod
    def _get_user(cls):
        return cls.user or current_user

    @classmethod
    def set_user(cls, user):
        cls.user = user

    @classmethod
    def _get_user_role(cls, for_master_user=False):
        user = cls.user or current_user
        if user.is_anonymous():
            return None
        if for_master_user:
            user = user.get_main_user()
        return user.current_role

    @classmethod
    def has_ui_admin(cls):
        return cls._get_user_role() == cls.admin

    @classmethod
    def has_ui_registrator(cls):
        return cls._get_user_role() in cls.ui_groups['registrator']

    @classmethod
    def has_ui_adm_nurse(cls):
        return cls._get_user_role() in cls.ui_groups['adm_nurse']

    @classmethod
    def has_ui_adm_nurse_ex(cls):
        return cls._get_user_role() in [cls.nurse_admission]

    @classmethod
    def has_ui_station_nurse(cls):
        return cls._get_user_role() in cls.ui_groups['station_nurse']

    @classmethod
    def has_ui_doctor(cls):
        return cls._get_user_role(True) in cls.ui_groups['doctor']

    @classmethod
    def has_ui_otd_doctor(cls):
        return cls._get_user_role(True) == cls.doctor_otd

    @classmethod
    def has_ui_doctor_stat(cls):
        return cls._get_user_role() == cls.doctor_stat

    @classmethod
    def has_ui_diag_doctor(cls):
        return cls._get_user_role(True) in cls.ui_groups['diag_doctor']

    @classmethod
    def has_ui_assistant(cls):
        return cls._get_user_role() == cls.nurse_assist

    @classmethod
    def has_ui_nurse(cls):
        return cls._get_user_role() in cls.ui_groups['nurse']

    @classmethod
    def has_ui_cashier(cls):
        return cls._get_user_role() in cls.ui_groups['cashier']

    @classmethod
    def has_ui_obstetrician(cls):
        return cls._get_user_role() in cls.ui_groups['obstetrician']

    @classmethod
    def has_ui_overseer_low(cls):
        return cls._get_user_role() in cls.ui_groups['overseers_low']

    @classmethod
    def has_ui_overseer_high(cls):
        return cls._get_user_role() in cls.ui_groups['overseers_high']

    @classmethod
    def has_ui_risar(cls):
        return cls._get_user_role() in cls.ui_groups['risar']

    @classmethod
    def has_ui_registrator_cashier(cls):
        return cls._get_user_role() in cls.ui_groups['registrator_cashier']

    @classmethod
    def get_default_url(cls):
        if cls._get_user_role() == cls.nurse_admission:
            return url_for('patients.index')
        if cls._get_user_role() == cls.nurse:
            return url_for('hospitalizations.html_search_hosps')
        return url_for(app.config.get('DEFAULT_ENDPOINT', 'index'))
