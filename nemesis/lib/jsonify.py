# -*- coding: utf-8 -*-

import datetime
import itertools
import os
import base64

from collections import defaultdict

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import between, func
from flask import json

from nemesis.app import app
from nemesis.systemwide import db
from nemesis.lib.data import int_get_atl_dict_all, get_patient_location, get_patient_hospital_bed, get_hosp_length
from nemesis.lib.action.utils import action_is_bak_lab, action_is_lab
from nemesis.lib.agesex import recordAcceptableEx
from nemesis.lib.utils import safe_unicode, safe_dict, logger, safe_traverse_attrs, format_date, safe_date
from nemesis.models.enums import EventPrimary, EventOrder, ActionStatus, Gender
from nemesis.models.event import Event, EventType, Diagnosis
from nemesis.models.schedule import (Schedule, rbReceptionType, ScheduleClientTicket, ScheduleTicket,
    QuotingByTime, Office, rbAttendanceType)
from nemesis.models.actions import Action, ActionProperty, ActionType, ActionType_Service
from nemesis.models.client import Client
from nemesis.models.exists import (rbRequestType, rbService, ContractTariff, Contract, Person, rbSpeciality,
    Organisation, rbContactType, FileGroupDocument, FileMeta, rbDocumentType)
from nemesis.lib.user import UserUtils, UserProfileManager
from nemesis.lib.const import VOL_POLICY_CODES, STATIONARY_EVENT_CODES


__author__ = 'mmalkov'


class Format:
    JSON = 0
    HTML = 1


class ScheduleVisualizer(object):
    def __init__(self):
        self.reception_type = None
        self.client_id = None
        self.reception_types = [at.code for at in rbReceptionType.query]

    def make_client_ticket_record(self, client_ticket):
        return {
            'id': client_ticket.id,
            'client_id': client_ticket.client_id,
            'event_id': client_ticket.event_id,
            'event_external_id': client_ticket.event.externalId if client_ticket.event else None,
            'finance': client_ticket.event.finance if client_ticket.event else None,
            'appointment_type': client_ticket.appointmentType,
            'note': client_ticket.note,
        }

    def make_ticket(self, ticket):
        client_ticket = ticket.client_ticket
        client_id = client_ticket.client_id if client_ticket else None
        return {
            'id': ticket.id,
            'begDateTime': ticket.begDateTime,
            'status': 'busy' if client_id else 'free',
            'client': ticket.client.shortNameText if client_id else None,
            'attendance_type': ticket.attendanceType,
            'office': ticket.schedule.office.code if ticket.schedule.office else None,
            'record': self.make_client_ticket_record(client_ticket) if client_ticket else None
        }

    def make_day(self, schedule):
        return {
            'id': schedule.id,
            'office': schedule.office,
            'tickets': [
                self.make_ticket(ticket)
                for ticket in schedule.tickets
                if not (self.client_id and ticket.client_ticket and ticket.client_ticket.client_id != self.client_id)
            ],
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
        }

    def make_person(self, person):
        speciality = person.speciality
        office = Office.query.filter(Office.code == person.office).first()
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': {
                'id': speciality.id,
                'name': speciality.name
            } if speciality else None,
            'office': office if office else None
        }

    def make_schedule(self, schedules, date_start, date_end):
        one_day = datetime.timedelta(days=1)

        def new_rt():
            date_iter = date_start
            rt_group = []
            while date_iter < date_end:
                rt_group.append({
                    'date': date_iter,
                    'scheds': []
                })
                date_iter += one_day
            return {
                'max_tickets': 0,
                'schedule': rt_group,
                'is_empty': True
            }
        if self.reception_type:
            result = {self.reception_type: new_rt()}
        else:
            result = dict((rt, new_rt()) for rt in self.reception_types)

        for schedule in schedules:
            if schedule.receptionType and schedule.receptionType.code in result:
                result[schedule.receptionType.code]['schedule'][(schedule.date - date_start).days]['scheds'].\
                    append(self.make_day(schedule))
                result[schedule.receptionType.code]['is_empty'] = False

        for group in result.itervalues():
            group['max_tickets'] = max(
                sum(
                    len(sched['tickets'])
                    for sched in day['scheds']
                )
                for day in group['schedule']
            )

        for group in result.itervalues():
            for day in group['schedule']:
                tickets = list(itertools.chain(*(sched['tickets'] for sched in day['scheds'])))
                planned_tickets = sorted(filter(lambda t: t['attendance_type'].code == 'planned', tickets), key=lambda t: t['begDateTime'])
                extra_tickets = filter(lambda t: t['attendance_type'].code == 'extra', tickets)
                CITO_tickets = filter(lambda t: t['attendance_type'].code == 'CITO', tickets)
                day['tickets'] = CITO_tickets + planned_tickets + extra_tickets
                roa = None
                for sched in day['scheds']:
                    if not roa and sched['roa']:
                        roa = sched['roa']
                    del sched['roa']
                day['beg_time'] = min(sched['begTime'] for sched in day['scheds']) if day['scheds'] else None
                day['end_time'] = max(sched['endTime'] for sched in day['scheds']) if day['scheds'] else None
                day['planned_count'] = len(planned_tickets) or None
                day['roa'] = roa
                del day['scheds']
        return result

    def make_persons_schedule(self, persons, start_date, end_date):
        return [{
            'person': self.make_person(person),
            'grouped': self.make_schedule(
                Schedule.query.join(Schedule.tickets).filter(
                    Schedule.person_id == person.id,
                    start_date <= Schedule.date, Schedule.date < end_date,
                    Schedule.deleted == 0
                ).order_by(Schedule.date).options(db.contains_eager(Schedule.tickets).contains_eager('schedule')),
                start_date, end_date
            )} for person in persons]

    def make_sched_description(self, schedule):
        planned = 0
        CITO = 0
        extra = 0
        busy = False
        planned_tickets = []
        extra_tickets = []
        CITO_tickets = []
        for ticket in schedule.tickets:
            at = ticket.attendanceType.code
            if at == 'planned':
                planned += 1
                planned_tickets.append(self.make_ticket(ticket))
            elif at == 'CITO':
                CITO += 1
                CITO_tickets.append(self.make_ticket(ticket))
            elif at == 'extra':
                extra += 1
                extra_tickets.append(self.make_ticket(ticket))
            if not busy and ticket.client_ticket:
                busy = True
        return {
            'id': schedule.id,
            'office': safe_dict(schedule.office),
            'planned': planned,
            'CITO': CITO,
            'extra': extra,
            'busy': busy,
            'begTime': schedule.begTime,
            'endTime': schedule.endTime,
            'roa': schedule.reasonOfAbsence,
            'reception_type': safe_dict(schedule.receptionType),
            'tickets': CITO_tickets + planned_tickets + extra_tickets
        }

    def make_quota_description(self, quota):
        return {
            'id': quota.id,
            'time_start': quota.QuotingTimeStart,
            'time_end': quota.QuotingTimeEnd,
            'quoting_type': safe_dict(quota.quotingType),
        }

    def collapse_scheds_description(self, scheds):
        info = {}
        roa = None
        busy = False
        sub_scheds = []
        for sub_sched in scheds:
            if not busy and sub_sched['busy']:
                busy = True

            if not roa and sub_sched['roa']:
                roa = sub_sched['roa']
                # На день установлена причина отсутствия - не может быть приема
                continue

            rec_type = sub_sched['reception_type']
            info_rt = info.setdefault(rec_type['code'], {'planned': 0, 'CITO': 0, 'extra': 0})

            info_rt['planned'] += sub_sched['planned']
            info_rt['CITO'] += sub_sched['CITO']
            info_rt['extra'] += sub_sched['extra']
            sub_scheds.append(sub_sched)
        return {
            'scheds': sub_scheds if not roa else [],
            'info': info,  # суммарная информация о плане, cito, extra по типам приема amb и home на день
                           # в интерфейсе на клиентской стороне не используется
            'busy': busy,
            'roa': roa
        }

    def make_schedule_description(self, schedules, date_start, date_end):

        def new_empty_day(offset):
            return {
                'date': date_start + datetime.timedelta(days=offset),
                'scheds': []
            }

        result = [new_empty_day(day_offset) for day_offset in xrange((date_end - date_start).days)]

        for schedule in schedules:
            idx = (schedule.date - date_start).days
            result[idx]['scheds'].append(self.make_sched_description(schedule))

        for day in result:
            day.update(self.collapse_scheds_description(day['scheds']))

        return result

    def make_quotas_description(self, quotas, date_start, date_end):

        def new_empty_day(offset):
            return {
                'date': date_start + datetime.timedelta(days=offset),
                'day_quotas': []
            }

        result = [new_empty_day(day_offset) for day_offset in xrange((date_end - date_start).days)]

        for quota in quotas:
            idx = (quota.quoting_date - date_start).days
            result[idx]['day_quotas'].append(self.make_quota_description(quota))

        return result

    def _clear_schedule_info(self, schedules):
        for day in schedules:
            day['busy'] = False
            day['roa'] = None
            if 'id' in day:
                del day['id']
            for sub_sched in day['scheds']:
                sub_sched['busy'] = False
                if 'id' in sub_sched:
                    del sub_sched['id']
                if 'tickets' in sub_sched:
                    del sub_sched['tickets']
        return schedules

    def _clear_quotas_info(self, quotas):
        for day in quotas:
            for q in day['day_quotas']:
                if 'id' in q:
                    del q['id']
        return quotas

    def make_person_schedule_description(self, person, start_date, end_date):
        schedules_by_date = Schedule.query.outerjoin(
            Schedule.tickets
        ).filter(
            Schedule.person_id == person.id,
            start_date <= Schedule.date, Schedule.date < end_date,
            Schedule.deleted == 0
        ).order_by(
            Schedule.date,
            Schedule.begTime,
            ScheduleTicket.begTime
        ).options(
            db.contains_eager(Schedule.tickets).contains_eager('schedule')
        )
        schedules = self.make_schedule_description(schedules_by_date, start_date, end_date)

        quoting_by_date = QuotingByTime.query.filter(
            QuotingByTime.doctor_id == person.id,
            QuotingByTime.quoting_date >= start_date,
            QuotingByTime.quoting_date < end_date
        )
        quotas = self.make_quotas_description(quoting_by_date, start_date, end_date)

        return {
            'person': self.make_person(person),
            'schedules': schedules,
            'quotas': quotas
        }

    def make_procedure_office_schedule_description(self, proc_office_id, start_date, end_date, person):
        # Пока что процедурные кабинеты являются персонами. Потом должны быть выделены в отдельную сущность.
        schedules_by_date = Schedule.query.outerjoin(
            Schedule.tickets
        ).filter(
            Schedule.person_id == proc_office_id,
            start_date <= Schedule.date, Schedule.date < end_date,
            Schedule.deleted == 0
        ).order_by(
            Schedule.date,
            Schedule.begTime,
            ScheduleTicket.begTime
        ).options(
            db.contains_eager(Schedule.tickets).contains_eager('schedule')
        )
        schedules = self.make_schedule_description(schedules_by_date, start_date, end_date)

        return {
            'schedules': schedules,
            'person': self.make_person(person),
            'proc_office': True
        }

    def make_copy_schedule_description(self, person, from_start_date, from_end_date, to_start_date, to_end_date):
        """Копировать чистое расписание без записей пациентов и причин
        отсутствия с одного месяца на другой.
        Копирование происходит по алгоритму 'цикличный месяц'. На каждый день
        целевого месяца идет копирование расписания из дня предыдущего месяца,
        выбранного с таким смещением, чтобы дни недели совпадали. Сдвиг дней
        происходит в правую сторону так, что если день недели первого дня
        месяца, который является источником расписания, позднее дня недели того
        дня, куда идет копирование, то расписание будет копироваться уже со
        следующей недели. Если в процессе копирования заканчиваются дни в
        месяце-источнике, то отсчет дней начинается с начала того же месяца
        с новым сдвигом, который опять выравнивает дни недели.
        Таким же образом копируется информация о квотах.
        """

        def get_day_shift(d_from, d_to):
            """Получить разницу между днями недели двух дат.
            Если день недели 1-ой даты раньше, чем у 2-ой, то разница считается
            в пределах недели, в противном случае - для дней текущей и следующей
            недели.
            """
            shift = d_from.weekday() - d_to.weekday()
            if shift > 0:
                shift = 7 - shift
            else:
                shift = abs(shift)
            return shift

        day_shift = get_day_shift(from_start_date, to_start_date)
        from_schedule_info = self.make_person_schedule_description(person, from_start_date, from_end_date)
        from_schedule = self._clear_schedule_info(from_schedule_info['schedules'])
        copy_schedule = []
        from_quotas = self._clear_quotas_info(from_schedule_info['quotas'])
        copy_quotas = []
        from_sched_len = len(from_schedule)
        while to_start_date <= to_end_date:
            cur_shift = to_start_date.day + day_shift
            if cur_shift > from_sched_len:
                # 2nd loop in month
                from_date = from_start_date + datetime.timedelta(days=(cur_shift - from_sched_len - 1))
                cur_shift = cur_shift - from_sched_len + get_day_shift(from_date, to_start_date)

            new_sched_day = dict(from_schedule[cur_shift - 1])
            new_sched_day['date'] = to_start_date + datetime.timedelta(days=0)
            if new_sched_day['scheds'] or new_sched_day['roa']:
                new_sched_day['altered'] = True
            copy_schedule.append(new_sched_day)

            new_quote_day = dict(from_quotas[cur_shift - 1])
            new_quote_day['date'] = to_start_date + datetime.timedelta(days=0)
            if new_quote_day['day_quotas']:
                new_quote_day['altered'] = True
            copy_quotas.append(new_quote_day)

            to_start_date += datetime.timedelta(days=1)

        from_schedule_info['schedules'] = copy_schedule
        from_schedule_info['quotas'] = copy_quotas
        return from_schedule_info


class ClientVisualizer(object):
    def __init__(self, mode=Format.JSON):
        self.__mode = mode

    def make_identification_info(self, identification):
        return {'id': identification.id,
                'deleted': identification.deleted,
                'identifier': identification.identifier,
                'accountingSystem_code': identification.accountingSystems.code,
                'accountingSystem_name': identification.accountingSystems.name,
                'checkDate': identification.checkDate or ''}

    def make_addresses_info(self, client):
        reg_addr = client.reg_address
        live_addr = client.loc_address
        if reg_addr and live_addr:
            if client.has_identical_addresses():
                live_addr = {
                    'id': live_addr.id,
                    'synced': True,
                }
        return safe_dict(reg_addr), safe_dict(live_addr)

    def make_relation_info(self, client_id, relation):
        if client_id == relation.client_id:
            return {
                'id': relation.id,
                'deleted': relation.deleted,
                'rel_type': relation.relativeType,
                'relative': self.make_short_client_info(relation.relative),
                'direct': True,
            }
        elif client_id == relation.relative_id:
            return {
                'id': relation.id,
                'deleted': relation.deleted,
                'rel_type': relation.relativeType,
                'relative': self.make_short_client_info(relation.client),
                'direct': False,
            }
        else:
            raise ValueError('Relation info does not match Client')

    def make_contacts_info(self, client):
        def make_contact(contact):
            return {
                'id': contact.id,
                'deleted': contact.deleted,
                'contact_type': contact.contactType,
                'contact_text': contact.contact,
                'notes': contact.notes
            }
        return ([make_contact(contact)
                for contact in client.contacts.join(rbContactType).order_by(rbContactType.idx)]
                if client.id else [])

    def make_client_info(self, client):
        """Полные данные пациента.
        Используется при редактировании данных пациента.
        """
        reg_addr, live_addr = self.make_addresses_info(client) if client.id else (None, None)
        relations = ([self.make_relation_info(client.id, relation) for relation in client.client_relations]
                     if client.id else [])
        documents = [safe_dict(doc) for doc in client.documents_all] if client.id else []
        policies = [safe_dict(policy) for policy in client.policies_all] if client.id else []
        document_history = documents + policies
        file_attaches_query = client.file_attaches.join(FileGroupDocument, FileMeta)
        files = [self.make_file_attach_info(fa) for fa in file_attaches_query]
        # identifications = [self.make_identification_info(identification) for identification in client.identifications]
        return {
            'info': client,
            'id_document': client.id_document if client.id else None,
            'reg_address': reg_addr,
            'live_address': live_addr,
            'compulsory_policy': client.compulsoryPolicy,
            'voluntary_policies': client.voluntaryPolicies,
            'blood_history': client.blood_history.all() if client.id else None,
            'allergies': client.allergies.all() if client.id else None,
            'intolerances': client.intolerances.all() if client.id else None,
            'soc_statuses': client.soc_statuses,
            'relations': relations,
            'contacts': self.make_contacts_info(client),
            'document_history': document_history,
            'file_attaches': files
            # 'identifications': identifications,
        }

    def make_file_attach_info(self, file_attach, with_data=True, file_idx_list=None):
        """

        :type file_attach: application.models.client.ClientFileAttach
        :return:
        """

        file_document = file_attach.file_document
        return {
            'id': file_attach.id,
            'attach_date': file_attach.attachDate,
            'doc_type': file_attach.documentType,
            'relation_type': file_attach.relationType,
            'file_document': {
                'id': file_document.id,
                'name': file_document.name,
                'files': [
                    self.make_file_info(fm, with_data) for fm in file_document.files if (
                        (fm.idx in file_idx_list) if file_idx_list else True
                    )
                ]
            }
        }

    def make_file_info(self, file_meta, with_data=True):
        def get_file_data(fullpath):
            try:
                with open(fullpath, 'rb') as f:
                    file_encoded = base64.b64encode(f.read())
            except IOError, e:
                logger.error(u'Невозможно загрузить файл %s' % fullpath, exc_info=True)
                return None
            return file_encoded

        if file_meta.id and with_data:
            fullpath = os.path.join(app.config['FILE_STORAGE_PATH'], file_meta.path)
            data = get_file_data(fullpath)
        else:
            data = None
        return {
            'id': file_meta.id,
            'name': file_meta.name,
            'idx': file_meta.idx,
            'mime': file_meta.mimetype,
            'data': data
        }

    def make_client_info_for_view_frame(self, client):
        """Данные пациента для фрейма информации о пациенте."""
        reg_addr, live_addr = self.make_addresses_info(client)
        info = {
            'info': client,
            'id_document': client.id_document,
            'reg_address': reg_addr,
            'live_address': live_addr,
            'compulsory_policy': client.compulsoryPolicy,
            'voluntary_policies': client.voluntaryPolicies,
            'contacts': self.make_contacts_info(client)
        }
        return info

    def make_client_info_for_event(self, client, event):
        """Данные пациента, используемые в интерфейсе обращения."""
        info = self.make_client_info_for_view_frame(client)
        if event.id:
            info['voluntary_policies'] = [
                vpol for vpol in client.policies_all
                if vpol.policyType.code in VOL_POLICY_CODES
            ]
        info['relations'] = [self.make_relation_info(client.id, relation) for relation in client.client_relations]
        info['work_org_id'] = client.works[0].org_id if client.works else None,  # FIXME: ...
        return info

    def make_search_client_info(self, client):
        """Данные пациента, используемые при поиске пациентов."""
        return {
            'info': client,
            'id_document': client.id_document,
            'compulsory_policy': client.compulsoryPolicy,
            'voluntary_policies': client.voluntaryPolicies,
            'contacts': self.make_contacts_info(client)
        }

    def make_short_client_info(self, client):
        """Краткие данные пациента.
        Используется при редактировании родственных связей пациента (поиск родственника).

        :type client: application.models.client.Client
        :return:
        """
        return {
            'id': client.id,
            'first_name': client.firstName,
            'patr_name': client.patrName,
            'last_name': client.lastName,
            'birth_date': client.birthDate,
            'sex': Gender(client.sexCode) if client.sexCode is not None else None,
            'full_name': client.nameText
        }

    def make_client_info_for_servicing(self, client):
        """Данные пациента, используемые в интерфейсах работы регистратора и врача."""
        if UserProfileManager.has_ui_registrator_cut():
            event_filter = 'stationary'
        else:
            event_filter = None
        return {
            'client_data': self.make_client_info_for_view_frame(client),
            'appointments': self.make_appointments(client.id),
            'events': self.make_events(client, event_filter)
        }

    def make_appointments(self, client_id, every=False):

        createPerson = aliased(Person)
        schedulePerson = aliased(Person)

        where = [ScheduleClientTicket.client_id == client_id,
                 ScheduleClientTicket.deleted == 0]
        if not every:
            # where.append(ScheduleClientTicket.event_id.isnot(None))
            where.append(Schedule.date >= datetime.date.today())

        query = db.select(
            (
                # 0
                ScheduleClientTicket.id,
                Schedule.date,
                ScheduleTicket.begTime,
                Schedule.person_id,
                ScheduleClientTicket.event_id,
                ScheduleClientTicket.ticket_id,

                # 6
                Schedule.office_id,
                Office.code,
                Office.name,

                # 9
                schedulePerson.firstName,
                schedulePerson.patrName,
                schedulePerson.lastName,

                # 12
                rbSpeciality.name,

                # 13
                createPerson.firstName,
                createPerson.patrName,
                createPerson.lastName,

                # 16
                Organisation.shortName,

                # 17
                Schedule.receptionType_id,
                rbReceptionType.code,
                rbReceptionType.name,

                # 20
                ScheduleTicket.attendanceType_id,
                rbAttendanceType.code,
                rbAttendanceType.name,

                # 23
                ScheduleClientTicket.note,
                ScheduleClientTicket.infisFrom,
                ScheduleClientTicket.createPerson_id,
            ), whereclause=db.and_(*where),
            from_obj=ScheduleClientTicket.__table__
                .join(ScheduleTicket, ScheduleTicket.id == ScheduleClientTicket.ticket_id)
                .join(Schedule, Schedule.id == ScheduleTicket.schedule_id)
                .join(rbAttendanceType, rbAttendanceType.id == ScheduleTicket.attendanceType_id)
                .join(rbReceptionType, rbReceptionType.id == Schedule.receptionType_id)
                .outerjoin(createPerson, createPerson.id == ScheduleClientTicket.createPerson_id)
                .join(schedulePerson, schedulePerson.id == Schedule.person_id)
                .join(rbSpeciality, rbSpeciality.id == schedulePerson.speciality_id)
                .outerjoin(Office, Office.id == Schedule.office_id)
                .outerjoin(Organisation, Organisation.infisCode == ScheduleClientTicket.infisFrom))
        query = query.order_by(Schedule.date.desc(), ScheduleTicket.begTime.desc())
        load_all = db.session.execute(query)

        return [
            {
                'id': row[0],
                'mark': None,
                'date': row[1],
                'begDateTime': datetime.datetime.combine(row[1], row[2]),
                'office': {
                    'id': row[6],
                    'code': row[7],
                    'name': row[8],
                },
                'person': u' '.join(filter(None, (row[9], row[10], row[11]))) or None,
                'person_speciality': row[12],
                'createPerson': {
                    'id': row[25],
                    'name': u' '.join(filter(None, (row[13], row[14], row[15]))) or None,
                },
                'note': row[23],
                'receptionType': {
                    'id': row[17],
                    'code': row[18],
                    'name': row[19],
                },
                'person_id': row[3],
                'org_from': row[16] or row[24],
                'event_id': row[4],
                'attendance_type': {
                    'id': row[20],
                    'code': row[21],
                    'name': row[22],
                },
                'ticket_id': row[5]
            }
            for row in load_all
        ]

    def make_events(self, client, event_filter):
        events = client.events
        if event_filter == 'stationary':
            events = events.join(EventType, rbRequestType).filter(rbRequestType.code.in_(STATIONARY_EVENT_CODES))
        events = events.order_by(Event.setDate.desc())
        return map(self.make_event, events)

    def make_person(self, person):
        if person is None:
            return {}
        speciality = person.speciality
        return {
            'id': person.id,
            'name': person.nameText,
            'speciality': person.speciality.name if speciality else None
        }

    def make_event(self, event):
        return {
            'id': event.id,
            'externalId': event.externalId,
            'setDate': event.setDate,
            'execDate': event.execDate,
            'person': self.make_person(event.execPerson),
            'requestType': event.eventType.requestType,
            'event_type': event.eventType,
            'result': event.result,
        }

    def make_payer_for_lc(self, client):
        id_doc = client.id_document
        return {
            'id': None,
            'first_name': client.firstName,
            'last_name': client.lastName,
            'patr_name': client.patrName,
            'birth_date': client.birthDate,
            'doc_type': safe_dict(id_doc.documentType) if id_doc else None,
            'doc_type_id': id_doc.id if id_doc else None,
            'serial_left': id_doc.serial_left if id_doc else None,
            'serial_right': id_doc.serial_right if id_doc else None,
            'number': id_doc.number if id_doc else None,
            'reg_address': safe_unicode(client.reg_address),
            'payer_org_id': None,
            'payer_org': None,
            'shared_in_events': []
        }


class PersonTreeVisualizer(object):
    def make_person(self, person):
        return {
            'id': person.id,
            'name': person.shortNameText,
        }

    def make_person_ws(self, person):
        name = person.shortNameText
        speciality = self.make_short_speciality(person.speciality) if person.speciality else None
        return {
            'id': person.id,
            'name': name,
            'speciality': speciality,
            'full_name': u'%s%s' % (name, u' (%s)' % speciality['name'] if speciality else u'')
        }

    def make_short_speciality(self, speciality):
        return {
            'id': speciality.id,
            'name': speciality.name
        }

    def make_speciality(self, speciality):
        return {
            'id': speciality.id,
            'name': speciality.name,
            'persons': [],
        }

    def make_person_with_profile(self, person, profile):
        return {
            'id': person.id,
            'full_name': person.full_name,
            'profile': profile
        }

    def make_tree(self, persons):
        specs = defaultdict(list)
        for person in persons:
            if person.speciality:
                specs[person.speciality.name].append(self.make_person(person))


class PrintTemplateVisualizer(object):
    def make_template_info(self, template):
        return {'id': template.id,
                'code': template.code,
                'name': template.name,
                }


class EventVisualizer(object):

    def make_new_event(self, event):
        return self.make_event_info_for_current_role(event, True)

    def make_event_info_for_current_role(self, event, new=False):
        data = {
            'event': self.make_event(event),
            'ro': not UserUtils.can_edit_event(event) if event.id else False,
            'has_access_to_payment_info': UserUtils.can_edit_event_payment_info(event),
            'can_read_diagnoses': UserUtils.can_read_dignoses(event),
            'can_edit_diagnoses': UserUtils.can_edit_dignoses(event),
            'can_create_actions': (
                [UserUtils.can_create_action(event.id, None, cl) for cl in range(4)]
                if event.id else [False] * 4
            )
        }
        if new:
            data['payment'] = self.make_event_payment(None)
        elif UserProfileManager.has_ui_admin():
            data['diagnoses'] = self.make_diagnoses(event)
            data['payment'] = self.make_event_payment(event)
            data['services'] = self.make_event_services(event.id)
        elif UserProfileManager.has_ui_doctor():
            data['diagnoses'] = self.make_diagnoses(event)
        elif UserProfileManager.has_ui_registrator():
            data['payment'] = self.make_event_payment(event)
            data['services'] = self.make_event_services(event.id)
        elif UserProfileManager.has_ui_cashier():
            data['payment'] = self.make_event_payment(event)
            data['services'] = self.make_event_services(event.id)
        if event.is_stationary:
            data['stationary_info'] = self.make_event_stationary_info(event)
        return data

    def make_short_event(self, event):
        event_type = event.eventType
        et_name = safe_traverse_attrs(event_type, 'name', default=u'')
        return {
            'id': event.id,
            'client_id': event.client_id,
            'client_full_name': event.client.nameText,
            'external_id': event.externalId,
            'beg_date': event.setDate,
            'beg_date_date': safe_date(event.setDate),  # ffs chrome timezones
            'end_date': event.execDate,
            'end_date_date': safe_date(event.execDate),
            'type_name': et_name,
            'person_short_name': event.execPerson.shortNameText if event.execPerson else u'Нет',
            'event_type': self.make_short_event_type(event_type),
            'result_text': safe_traverse_attrs(event, 'result', 'name', default=''),
            'text_description': u'{0} №{1} от {2}, {3}'.format(
                u'История болезни' if event.is_stationary else u'Обращение',
                event.externalId,
                format_date(event.setDate),
                et_name
            )
        }

    def make_short_event_type(self, event_type):
        return {
            'id': event_type.id,
            'name': event_type.name,
            'print_context': event_type.printContext
        }

    def make_event(self, event):
        """
        @type event: Event
        """
        cvis = ClientVisualizer()
        return {
            'id': event.id,
            'create_person_id': event.createPerson_id,
            'deleted': event.deleted,
            'external_id': event.externalId,
            'order': EventOrder(event.order),
            'order_': event.order,
            'is_primary': EventPrimary(event.isPrimaryCode),
            'is_primary_': event.isPrimaryCode,
            'client': cvis.make_client_info_for_event(event.client, event),
            'client_id': event.client.id,
            'set_date': event.setDate,
            'exec_date': event.execDate,
            'exec_person': event.execPerson,
            'result': event.result,
            'ache_result': event.rbAcheResult,
            'contract': event.contract,
            'event_type': event.eventType,
            'organisation': event.organisation,
            'org_structure': event.orgStructure,
            'note': event.note,
            'actions': map(self.make_action, event.actions),
        }

    def make_diagnoses(self, event):
        """
        @type event: Event
        """
        result = []
        for diagnostic in event.diagnostics:
            result.append(self.make_diagnostic_record(diagnostic))
        return result

    def make_diagnose_row(self, diagnostic, diagnosis):
        """
        @type diagnostic: application.models.event.Diagnostic
        @type diagnosis: Diagnosis
        """
        return {
            'diagnosis_id': diagnosis.id,
            'diagnostic_id': diagnostic.id,
            'diagnosis_type': diagnostic.diagnosisType,
            'person': diagnosis.person,
            'mkb': diagnosis.mkb,
            'mkb_ex': diagnosis.mkb_ex,
            'character': diagnosis.character,
            'phase': diagnostic.phase,
            'stage': diagnostic.stage,
            'health_group': diagnostic.healthGroup,
            'dispanser': diagnosis.dispanser,
            'trauma': diagnosis.traumaType,
            'notes': diagnostic.notes,
        }

    def make_diagnostic_record(self, diagnostic):
        """
        :type diagnostic: application.models.event.Diagnostic
        :param diagnostic:
        :return:
        """
        pvis = PersonTreeVisualizer()
        aviz = ActionVisualizer()
        return {
            'id': diagnostic.id,
            'set_date': diagnostic.setDate,
            'end_date': diagnostic.endDate,
            'diagnosis_type': diagnostic.diagnosisType,
            'deleted': diagnostic.deleted,
            'diagnosis': self.make_diagnosis_record(diagnostic.diagnosis),
            'character': diagnostic.character,
            'person': pvis.make_person_ws(diagnostic.person) if diagnostic.person else None,
            'notes': diagnostic.notes,
            'action_id': diagnostic.action_id,
            'action': aviz.make_small_action_info(diagnostic.action) if diagnostic.action else None,
            'result': diagnostic.result,
            'ache_result': diagnostic.rbAcheResult,
            'event_id': diagnostic.event_id,
            'health_group': diagnostic.healthGroup,
            'trauma_type': diagnostic.traumaType,
            'phase': diagnostic.phase,
            'stage': diagnostic.stage,
            'dispanser': diagnostic.dispanser,
            'sanatorium': diagnostic.sanatorium,
            'hospital': diagnostic.hospital,
            'diagnosis_description': diagnostic.diagnosis_description,
            'modify_person': pvis.make_person_ws(diagnostic.modifyPerson) if diagnostic.modifyPerson else None
        } if diagnostic else None

    def make_diagnosis_record(self, diagnosis):
        """
        :type diagnosis: application.models.event.Diagnosis
        :param diagnosis:
        :return:
        """
        return {
            'id': diagnosis.id,
            'mkb': diagnosis.mkb,
            'mkbex': diagnosis.mkb_ex,
            'client_id': diagnosis.client_id,
        }

    def make_action_type(self, action_type):
        """
        :type action_type: application.models.actions.ActionType
        """
        return {
            'id': action_type.id,
            'name': action_type.name,
            'code': action_type.code,
            'flat_code': action_type.flatCode,
            'class': action_type.class_,
            'is_required_tissue': action_type.isRequiredTissue,
        }

    def make_action(self, action):
        """
        @type action: Action
        """
        return {
            'id': action.id,
            'name': action.actionType.name,
            'type': self.make_action_type(action.actionType),
            'status': ActionStatus(action.status),
            'begDate': action.begDate,
            'endDate': action.endDate,
            'person_text': safe_unicode(action.person),
            'person_id': action.person_id,
            'set_person_id': action.setPerson_id,
            'create_person_id': action.createPerson_id,
            'can_read': UserUtils.can_read_action(action),
            'can_edit': UserUtils.can_edit_action(action),
            'can_delete': UserUtils.can_delete_action(action),
        }

    def make_event_payment(self, event, client=None):
        if client:
            cvis = ClientVisualizer()
            local_contract = cvis.make_payer_for_lc(client)
            payments = []
        else:
            local_contract = self.make_event_local_contract(event)
            payments = [payment
                        for payment in event.payments
                        if payment.master_id == event.id] if event else []
        return {
            'local_contract': local_contract,
            'payments': payments
        }

    def make_event_local_contract(self, event):
        if event and event.localContract:
            local_contract = event.localContract
        else:
            from blueprints.event.lib.utils import create_new_local_contract
            local_contract = create_new_local_contract({
                'date_contract': datetime.date.today(),
                'number_contract': ''
            })
        lc = {
            'id': local_contract.id,
            'number_contract': local_contract.numberContract,
            'date_contract': local_contract.dateContract,
            'coord_text': local_contract.coordText,
            'first_name': local_contract.firstName,
            'last_name': local_contract.lastName,
            'patr_name': local_contract.patrName,
            'birth_date': local_contract.birthDate,
            'doc_type_id': local_contract.documentType_id,
            'doc_type': local_contract.documentType,
            'serial_left': local_contract.serialLeft,
            'serial_right': local_contract.serialRight,
            'number': local_contract.number,
            'reg_address': local_contract.regAddress,
            'payer_org_id': local_contract.org_id,
            'payer_org': local_contract.org,
        }
        if event and event.id and local_contract.id:
            other_events = db.session.query(
                Event.id, Event.externalId
            ).filter(
                Event.localContract_id == local_contract.id,
                Event.id != event.id
            ).all()
        else:
            other_events = []
        lc['shared_in_events'] = other_events
        return lc

    def make_prev_events_contracts(self, event_list):
        def make_event_small_info(event):
            return {
                'id': event.id,
                'set_date': event.setDate,
                'exec_date': event.execDate,
                'descr': u'Обращение №{0}, {1}'.format(
                    event.externalId,
                    safe_traverse_attrs(event, 'eventType', 'name', default=u'')
                )
            }

        result = []
        for event in event_list:
            lc = self.make_event_local_contract(event)
            if not lc['id']:
                continue

            result.append({
                'local_contract': lc,
                'event_info': make_event_small_info(event)
            })
        return result

    def make_event_services(self, event_id):

        def make_raw_service_group(action, service_id, at_code, at_name, ct_code, ct_name, price, at_context):
            service = {
                'at_id': action.actionType_id,
                'service_id': service_id,
                'code': ct_code,
                'name': ct_name,
                'at_code': at_code,
                'at_name': at_name,
                'action': action,
                'price': price,
                'is_lab': False,
                'print_context': at_context
            }

            client = Client.query.get(action.event.client_id)
            client_age = client.age_tuple(datetime.date.today())

            at_id = service['at_id']
            at_data = ats_apts.get(at_id)
            if at_data and at_data[9]:
                prop_types = at_data[9]
                prop_types = [prop_type[:2] for prop_type in prop_types if recordAcceptableEx(client.sexCode,
                                                                                              client_age,
                                                                                              prop_type[3],
                                                                                              prop_type[2])]
                if prop_types:
                    service['is_lab'] = True
                    service['assignable'] = prop_types
            return service

        def make_action_as_service(a, service):
            action = {
                'action_id': a.id,
                'account': a.account,
                'amount': a.amount,
                'beg_date': a.begDate,
                'end_date': a.endDate,
                'status': a.status,
                'coord_date': a.coordDate,
                'coord_person': person_vis.make_person(a.coordPerson) if a.coordPerson else None,
                'sum': service['price'] * a.amount,
            }
            if service['is_lab']:
                action['assigned'] = [prop.type_id for prop in a.properties if prop.isAssigned]
                action['planned_end_date'] = a.plannedEndDate
            return action

        def shrink_service_group(group):
            actions = [make_action_as_service(act_serv.pop('action'), act_serv) for act_serv in service_group]
            total_amount = sum([act['amount'] for act in actions])
            total_sum = sum([act['sum'] for act in actions])

            def calc_all_assigned(actions):
                # [] - all have same assignments, False - have different assignments
                ref_asgn_list = actions[0]['assigned']
                return all(map(lambda act: act['assigned'] == ref_asgn_list, actions)) and ref_asgn_list

            def calc_all_ped(actions):
                # datetime.datetime - all have same planned end date, False - have different dates
                ref_action_ped = actions[0]['planned_end_date']
                return all(map(lambda act: act['planned_end_date'] == ref_action_ped, actions)) and ref_action_ped

            result_service = dict(
                group[0],
                actions=actions,
                total_amount=total_amount,
                sum=total_sum
            )
            if result_service['is_lab']:
                result_service['all_assigned'] = calc_all_assigned(actions)
                result_service['all_planned_end_date'] = calc_all_ped(actions)

            return result_service

        person_vis = PersonTreeVisualizer()
        query = db.session.query(
            Action,
            ActionType_Service.service_id,
            ActionType.code,
            ActionType.name,
            ContractTariff.code,
            ContractTariff.name,
            ContractTariff.price,
            ActionType.context
        ).join(
            Event,
            EventType,
            Contract,
            ContractTariff,
            ActionType,
            ActionType_Service
        ).join(
            rbService, ActionType_Service.service_id == rbService.id
        ).filter(
            Action.event_id == event_id,
            ContractTariff.eventType_id == EventType.id,
            ContractTariff.service_id == ActionType_Service.service_id,
            Action.deleted == 0,
            ContractTariff.deleted == 0,
            between(func.date(Event.setDate),
                    ActionType_Service.begDate,
                    func.coalesce(ActionType_Service.endDate, func.curdate())),
            between(func.date(Event.setDate), ContractTariff.begDate, ContractTariff.endDate)
        )

        ats_apts = int_get_atl_dict_all()

        services_by_at = defaultdict(list)
        for a, service_id, at_code, at_name, ct_code, ct_name, price, at_context in query:
            services_by_at[(a.actionType_id, service_id)].append(
                make_raw_service_group(a, service_id, at_code, at_name, ct_code, ct_name, price, at_context)
            )
        services_grouped = []
        for key, service_group in services_by_at.iteritems():
            services_grouped.append(
                shrink_service_group(service_group)
            )

        return services_grouped

    def make_search_event_info(self, event):
        pviz = PersonTreeVisualizer()
        cviz = ClientVisualizer()

        return {
            'id': event.id,
            'external_id': event.externalId,
            'exec_person': pviz.make_person_ws(event.execPerson) if event.execPerson else None,
            'set_date': event.setDate,
            'beg_date_date': safe_date(event.setDate),  # ffs chrome timezones
            'exec_date': event.execDate,
            'end_date_date': safe_date(event.execDate),
            'event_type': self.make_short_event_type(event.eventType),
            'client': cviz.make_short_client_info(event.client),
            'contract': self.make_event_local_contract(event)
        }

    def make_search_payments_list(self, payment):
        pviz = PersonTreeVisualizer()
        cviz = ClientVisualizer()
        return {
            'id': payment.id,
            'date': payment.date,
            'cashbox': payment.cashBox,
            'cashier_person': pviz.make_person(payment.createPerson),
            'cash_operation': payment.cashOperation,
            'sum': payment.sum,
            'client': cviz.make_short_client_info(payment.event.client),
            'event': self.make_short_event(payment.event)
        }

    def make_event_stationary_info(self, event):
        pviz = PersonTreeVisualizer()
        hosp_length = get_hosp_length(event)
        patient_cur_os = get_patient_location(event)
        hospital_bed = get_patient_hospital_bed(event)
        return {
            'admission_date': event.setDate,
            'discharge_date': event.execDate,
            'hosp_length': hosp_length,
            'patient_current_os': patient_cur_os,
            'hospital_bed': hospital_bed,
            'attending_doctor': pviz.make_person_ws(event.execPerson) if event.execPerson else None
        }


class ActionVisualizer(object):
    ro = True

    def make_action(self, action):
        """
        @type action: Action
        """
        result = {
            'action': {
                'id': action.id,
                'action_type': action.actionType,
                'event_id': action.event_id,
                'client': action.event.client,
                'direction_date': action.directionDate,
                'beg_date': action.begDate,
                'end_date': action.endDate,
                'planned_end_date': action.plannedEndDate,
                'status': ActionStatus(action.status),
                'set_person': action.setPerson,
                'person': action.person,
                'note': action.note,
                'office': action.office,
                'amount': action.amount,
                'uet': action.uet,
                'pay_status': action.payStatus,
                'account': action.account,
                'is_urgent': action.isUrgent,
                'coord_date': action.coordDate,
                'properties': [
                    self.make_property(prop)
                    for prop in action.properties
                ]
            },
            #FIXME: Мелочь, конечно, но использование двойного отрицания не особо красиво. Зачем здесь делать "not", чтобы потом в интефейсе проверять "!ro".
            'ro': not UserUtils.can_edit_action(action) if action.id else False,
            'layout': self.make_action_layout(action),
        }
        if action_is_bak_lab(action):
            result['bak_lab_info'] = self.make_bak_lab_info(action)
        return result

    def make_small_action_info(self, action):
        return {
            'id': action.id,
            'action_type': action.actionType,
            'event_id': action.event_id,
            'beg_date': action.begDate,
            'end_date': action.endDate,
            'planned_end_date': action.plannedEndDate,
            'status': ActionStatus(action.status),
            'set_person_id': action.setPerson_id,
            'person_id': action.person_id,
        }

    def make_action_layout(self, action):
        """
        :type action: Action
        :param action:
        :return:
        """
        at_layout = action.actionType.layout
        if at_layout:
            try:
                at_layout = json.loads(at_layout)
            except ValueError:
                logger.warning('Bad layout for ActionType with id = %s' % action.actionType.id)
            else:
                return at_layout
        if action_is_lab(action):
            layout = self.make_table_layout(action)
        else:
            layout = self.make_default_two_cols_layout(action)
        return layout

    def make_default_layout(self, action):
        layout = {
            'tagName': 'root',
            'children': [{
                'tagName': 'ap',
                'id': ap.type.id,
            } for ap in action.properties_ordered]
        }
        return layout

    def make_default_two_cols_layout(self, action):
        def pairwise(iterable):
            from itertools import izip_longest
            a = iter(iterable)
            return izip_longest(a, a)

        def make_row(ap, ap2):
            return {
                'tagName': 'row',
                'cols': 2,
                'children': [{
                    'tagName': 'ap',
                    'id': ap.type.id
                }, {
                    'tagName': 'ap',
                    'id': ap2.type.id
                } if ap2 else {}]
            }

        layout = {
            'tagName': 'root',
            'children': []
        }
        for ap, next_ap in pairwise(action.properties_ordered):
            layout['children'].append(make_row(ap, next_ap))
        return layout

    def make_table_layout(self, action):
        layout = {
            'tagName': 'root',
            'children': [{
                'tagName': 'table',
                'children': [{
                    'tagName': 'ap',
                    'id': ap.type.id
                } for ap in action.properties_ordered]
            }]
        }

        if action_is_bak_lab(action):
            layout['children'].append({
                'tagName': 'bak_lab_view',
            })
        return layout

    def make_property(self, prop):
        """
        @type prop: ActionProperty
        """
        if prop.value is None:
            value = [] if prop.type.isVector else None
        elif prop.type.isVector:
            maker = getattr(self, 'make_ap_%s' % prop.type.typeName, None)
            value = [maker(v) for v in prop.value] if maker else [v for v in prop.value]
        else:
            maker = getattr(self, 'make_ap_%s' % prop.type.typeName, None)
            value = maker(prop.value) if maker else prop.value
        return {
            'id': prop.id,
            'idx': prop.type.idx,
            'type': prop.type,
            'is_assigned': prop.isAssigned,
            'value': value,
            'unit': prop.unit,
            'norm': prop.norm
        }

    # Здесь будут кастомные мейкеры экшон пропертей.

    @staticmethod
    def make_ap_OrgStructure(value):
        """
        :type value: application.models.exists.OrgStructure
        :param value:
        :return:
        """
        return {
            'id': value.id,
            'name': value.name,
            'code': value.code,
            'parent_id': value.parent_id, # for compatibility with Reference
        }

    @staticmethod
    def make_ap_Diagnosis(value):
        """
        :type value: application.models.event.Diagnostic
        :param value:
        :return:
        """
        evis = EventVisualizer()
        return evis.make_diagnostic_record(value)

    # ---

    def make_bak_lab_info(self, action):
        bbt_response = action.bbt_response
        if not bbt_response:
            return None

        def make_comment(comment):
            return {
                'id': comment.id,
                'text': comment.valueText
            }

        def make_sens_value(sv):
            return {
                'id': sv.id,
                'mic': sv.MIC,
                'activity': sv.activity,
                'antibiotic': safe_traverse_attrs(sv, 'antibiotic', 'name')
            }

        def make_organism(organism):
            return {
                'id': organism.id,
                'microorganism': safe_traverse_attrs(organism, 'microorganism', 'name'),
                'concentration': organism.concentration,
                'sens_values': [make_sens_value(sv) for sv in organism.sens_values]
            }

        organisms = [make_organism(osm) for osm in bbt_response.values_organism]
        comments = [make_comment(com) for com in bbt_response.values_text]
        pvis = PersonTreeVisualizer()
        result = {
            'doctor': pvis.make_person_ws(bbt_response.doctor),
            'code_lis': bbt_response.codeLIS,
            'defects': bbt_response.defects,
            'final': bool(bbt_response.final),
            'organisms': organisms,
            'comments': comments
        }
        return result
