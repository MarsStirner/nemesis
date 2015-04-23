# -*- coding: utf-8 -*-
from nemesis.lib.utils import safe_traverse, safe_datetime, safe_date
from nemesis.models.event import Diagnostic, Diagnosis
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


def create_or_update_diagnosis(event, json_data, action=None):
    diagnostic_id = safe_traverse(json_data, 'id')
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