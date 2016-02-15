# -*- coding: utf-8 -*-
from nemesis.lib.utils import safe_traverse, safe_datetime, safe_date
from nemesis.models.diagnosis import Diagnosis, Diagnostic, Action_Diagnosis, Event_Diagnosis, rbDiagnosisTypeN, \
    rbDiagnosisKind
from nemesis.models.exists import MKB
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


def create_diagnostic(diagnostic_data, action_id):
    """
    создание Diagnositc
    """

    mkb_id = safe_traverse(diagnostic_data, 'mkb', 'id')
    mkb2_id = safe_traverse(diagnostic_data, 'mkb2', 'id')
    diagnostic = Diagnostic()
    diagnostic.mkb = MKB.query.get(mkb_id) if mkb_id else None
    diagnostic.mkb_ex = MKB.query.get(mkb2_id) if mkb2_id else None
    diagnostic.traumaType_id = safe_traverse(diagnostic_data, 'trauma', 'id')
    diagnostic.diagnosis_description = safe_traverse(diagnostic_data, 'diagnosis_description')
    diagnostic.character_id = safe_traverse(diagnostic_data, 'character', 'id')
    diagnostic.stage_id = safe_traverse(diagnostic_data, 'stage', 'id')
    diagnostic.phase_id = safe_traverse(diagnostic_data, 'phase', 'id')
    diagnostic.healthGroup_id = safe_traverse(diagnostic_data, 'healthGroup', 'id')
    diagnostic.action_id = action_id
    diagnostic.rbAcheResult_id = safe_traverse(diagnostic_data, 'ache_result', 'id')
    # diagnostic.sanatorium = 0  # todo
    diagnostic.notes = safe_traverse(diagnostic_data, 'notes')
    return diagnostic


def update_diagnosis_kind_info(action, diagnosis, diagnosis_types_info):
    """
    редактирование связи диагноза (Diagnosis) с Action и Event
    """
    add_to_event = action.person == action.event.execPerson
    diagnosis_id = diagnosis.id
    for diagnosis_type, diagnosis_kind in diagnosis_types_info.iteritems():
        action_diagn = Action_Diagnosis.query.join(rbDiagnosisTypeN).filter(Action_Diagnosis.action_id == action.id,
                                                                            Action_Diagnosis.diagnosis_id == diagnosis_id,
                                                                            rbDiagnosisTypeN.code == diagnosis_type).first() if diagnosis_id else None
        if action_diagn:
            if diagnosis_kind['code'] != 'associated':
                action_diagn.diagnosisKind_id = diagnosis_kind.get('id')
            else:
                action_diagn.deleted = 1
        elif diagnosis_kind['code'] != 'associated':
            action_diagn = Action_Diagnosis()
            action_diagn.action_id = action.id
            action_diagn.diagnosis = diagnosis
            action_diagn.diagnosisKind_id = diagnosis_kind.get('id')
            action_diagn.diagnosisType = rbDiagnosisTypeN.query.filter(rbDiagnosisTypeN.code == diagnosis_type).first()

        if action_diagn:
            db.session.add(action_diagn)

        if add_to_event:  # если лечащий врач, то создать связку и с event
            event_diagn = Event_Diagnosis.query.join(rbDiagnosisTypeN).filter(Event_Diagnosis.event_id == action.event.id,
                                                                              Event_Diagnosis.diagnosis_id == diagnosis_id,
                                                                              rbDiagnosisTypeN.code == diagnosis_type).first() if diagnosis_id else None
            if event_diagn:
                if diagnosis_kind['code'] != 'associated':
                    event_diagn.diagnosisKind_id = diagnosis_kind.get('id')
                else:
                    event_diagn.deleted = 1
            elif diagnosis_kind['code'] != 'associated':
                event_diagn = Event_Diagnosis()
                event_diagn.event_id = action.event.id
                event_diagn.diagnosis = diagnosis
                event_diagn.diagnosisKind_id = diagnosis_kind.get('id')
                event_diagn.diagnosisType = rbDiagnosisTypeN.query.filter(rbDiagnosisTypeN.code == diagnosis_type).first()

            if diagnosis_kind['code'] == 'main':
                prev_main = Event_Diagnosis.query.join(rbDiagnosisTypeN, rbDiagnosisKind).filter(
                    Event_Diagnosis.event_id == action.event.id,
                    Event_Diagnosis.diagnosis_id != diagnosis_id,
                    rbDiagnosisTypeN.code == diagnosis_type,
                    rbDiagnosisKind.code == 'main').first()

                if prev_main:
                    prev_main.diagnosisKind = rbDiagnosisKind.query.filter(rbDiagnosisKind.code == 'complication').first()
                    db.session.add(prev_main)

        if event_diagn:
            db.session.add(event_diagn)


def create_or_update_diagnoses(action, diagnoses_data):

    for diagnosis_data in diagnoses_data:
        diagnosis = None
        diagnosis_id = diagnosis_data.get('id')
        kind_changed = diagnosis_data.get('kind_changed')
        diagnostic_changed = diagnosis_data.get('diagnostic_changed')
        diagnostic_data = diagnosis_data.get('diagnostic')
        diagnosis_types = diagnosis_data.get('diagnosis_types')
        if diagnosis_id and diagnostic_changed:
            diagnosis = Diagnosis.query.get(diagnosis_id)
            diagnosis.setDate = safe_datetime(diagnosis_data.get('set_date'))
            diagnosis.endDate = safe_datetime(diagnosis_data.get('end_date'))

            diagnostic = create_diagnostic(diagnostic_data, action.id)
            diagnostic.diagnosis = diagnosis

            db.session.add(diagnostic)
        elif not diagnosis_id:
            diagnosis = Diagnosis()
            diagnosis.setDate = safe_datetime(diagnosis_data.get('set_date'))
            diagnosis.endDate = safe_datetime(diagnosis_data.get('end_date'))
            diagnosis.client_id = action.event.client_id
            diagnosis.person_id = safe_traverse(diagnosis_data, 'person', 'id')

            diagnostic = create_diagnostic(diagnostic_data, action.id)
            diagnostic.diagnosis = diagnosis

            db.session.add_all([diagnosis, diagnostic])

        if kind_changed:  # если был изменен вид диагноза (основной, осложнение, сопутствующий)
            diagnosis = Diagnosis.query.get(diagnosis_id) if not diagnosis else diagnosis
            update_diagnosis_kind_info(action, diagnosis, diagnosis_types)
        db.session.commit()


# не используется
def create_or_update_diagnosis(event, json_data, action=None):
    diagnostic_id = safe_traverse(json_data, 'id')
    deleted = json_data.get('deleted', 0)
    set_date = safe_datetime(safe_traverse(json_data, 'set_date'))
    end_date = safe_datetime(safe_traverse(json_data, 'end_date'))
    diagnosis_type_id = safe_traverse(json_data, 'diagnosis_type', 'id')
    character_id = safe_traverse(json_data, 'character', 'id')
    person_id = safe_traverse(json_data, 'person', 'id')
    speciality_id = safe_traverse(json_data, 'person', 'speciality', 'id')
    notes = safe_traverse(json_data, 'notes')
    result_id = safe_traverse(json_data, 'result', 'id')
    ache_result_id = safe_traverse(json_data, 'ache_result', 'id')
    health_group_id = safe_traverse(json_data, 'health_group', 'id')
    trauma_type_id = safe_traverse(json_data, 'trauma_type', 'id')
    phase_id = safe_traverse(json_data, 'phase', 'id')
    diagnosis_description = safe_traverse(json_data, 'diagnosis_description')
    stage_id = safe_traverse(json_data, 'stage', 'id')
    dispanser_id = safe_traverse(json_data, 'dispanser', 'id')
    # sanatorium_id = safe_traverse(json_data, 'sanatorium', 'id'),
    # hospital_id = safe_traverse(json_data, 'hospital', 'id'),

    diagnosis = safe_traverse(json_data, 'diagnosis')
    diagnosis_id = safe_traverse(diagnosis, 'id')
    client_id = event.client_id
    mkb = safe_traverse(diagnosis, 'mkb', 'code')
    mkbex = safe_traverse(diagnosis, 'mkbex', 'code')
    if diagnostic_id:
        diag = Diagnostic.query.get(diagnostic_id)
        diag.deleted = deleted
        diag.setDate = set_date
        diag.endDate = end_date
        diag.diagnosisType_id = diagnosis_type_id
        diag.character_id = character_id
        diag.person_id = person_id
        diag.speciality_id = speciality_id
        diag.notes = notes
        diag.result_id = result_id
        diag.rbAcheResult_id = ache_result_id
        diag.healthGroup_id = health_group_id
        diag.traumaType_id = trauma_type_id
        diag.phase_id = phase_id
        diag.stage_id = stage_id
        diag.dispanser_id = dispanser_id
        diag.diagnosis_description = diagnosis_description

        diagnosis = filter(lambda ds: ds.id == diagnosis_id, diag.diagnoses)
        if not diagnosis:
            raise Exception('Diagnosis record can\'t be found')
        else:
            diagnosis = diagnosis[0]
        diagnosis.MKB = mkb
        diagnosis.MKBEx = mkbex or ''
    else:
        diag = Diagnostic()
        diag.event = event
        diag.setDate = safe_date(set_date)
        diag.endDate = safe_date(end_date)
        diag.diagnosisType_id = diagnosis_type_id
        diag.character_id = character_id
        diag.person_id = person_id
        diag.speciality_id = speciality_id
        diag.notes = notes
        diag.result_id = result_id
        diag.rbAcheResult_id = ache_result_id
        diag.healthGroup_id = health_group_id
        diag.traumaType_id = trauma_type_id
        diag.phase_id = phase_id
        diag.stage_id = stage_id
        diag.dispanser_id = dispanser_id
        diag.diagnosis_description = diagnosis_description
        if action:
            diag.action = action
        # etc
        diag.sanatorium = 0
        diag.hospital = 0

        diagnosis = Diagnosis()
        diagnosis.client_id = client_id
        diagnosis.MKB = mkb
        diagnosis.MKBEx = mkbex or ''
        diagnosis.diagnosisType_id = diagnosis_type_id
        diagnosis.character_id = character_id
        diagnosis.traumaType_id = trauma_type_id
        diagnosis.setDate = safe_date(set_date)
        diagnosis.endDate = safe_date(set_date)
        diagnosis.person_id = person_id
        # etc
        diagnosis.dispanser_id = None
        diagnosis.mod_id = None

        diag.diagnoses.append(diagnosis)

    return diag


# не используется
def delete_diagnosis(diagnostic, diagnostic_id=None):
    """
    :type diagnostic: application.models.event.Diagnostic
    :param diagnostic:
    :return:
    """
    if diagnostic is None and diagnostic_id:
        diagnostic = Diagnostic.query.get(diagnostic_id)
    diagnostic.deleted = 1
    for ds in diagnostic.diagnoses:
        ds.deleted = 1
    db.session.add(diagnostic)