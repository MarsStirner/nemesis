# -*- coding: utf-8 -*-
from nemesis.lib.utils import safe_traverse, safe_datetime, safe_date
from nemesis.models.event import Diagnostic, Diagnosis
from nemesis.systemwide import db
from nemesis.models.exists import rbDiagnosisType, rbDiseaseCharacter, Person, rbSpeciality, rbResult, rbAcheResult, rbHealthGroup, rbTraumaType, rbDiseasePhases, rbDiseaseStage, rbDispanser, MKB

__author__ = 'viruzzz-kun'


def _safe_make_object(obj, factory, *args, **kwargs):
    default = kwargs.get('default', None)
    oid = safe_traverse(obj, *args, default=None)
    if oid is None:
        return default
    return db.session.query(factory).get(oid)


def create_or_update_diagnosis(event, json_data, action=None):
    diagnostic_id = safe_traverse(json_data, 'id')
    deleted = json_data.get('deleted', 0)
    set_date = safe_datetime(safe_traverse(json_data, 'set_date'))
    end_date = safe_datetime(safe_traverse(json_data, 'end_date'))
    notes = safe_traverse(json_data, 'notes')
    diagnosis_description = safe_traverse(json_data, 'diagnosis_description')

    diagnosis_type = _safe_make_object(json_data, rbDiagnosisType, 'diagnosis_type', 'id')
    character = _safe_make_object(json_data, rbDiseaseCharacter, 'character', 'id')
    person = _safe_make_object(json_data, Person, 'person', 'id')
    speciality = _safe_make_object(json_data, rbSpeciality, 'person', 'speciality', 'id')
    result = _safe_make_object(json_data, rbResult, 'result', 'id')
    ache_result = _safe_make_object(json_data, rbAcheResult, 'ache_result', 'id')
    health_group = _safe_make_object(json_data, rbHealthGroup, 'health_group', 'id')
    trauma_type = _safe_make_object(json_data, rbTraumaType, 'trauma_type', 'id')
    phase = _safe_make_object(json_data, rbDiseasePhases, 'phase', 'id')
    stage = _safe_make_object(json_data, rbDiseaseStage, 'stage', 'id')
    dispanser = _safe_make_object(json_data, rbDispanser, 'dispanser', 'id')
    # sanatorium_id = safe_traverse(json_data, 'sanatorium', 'id'),
    # hospital_id = safe_traverse(json_data, 'hospital', 'id'),

    diagnosis = safe_traverse(json_data, 'diagnosis')
    # diagnosis_id = safe_traverse(diagnosis, 'id')
    client = event.client
    _mkb = safe_traverse(diagnosis, 'mkb', 'code')
    _mkbex = safe_traverse(diagnosis, 'mkbex', 'code')
    mkb = MKB.query.filter(MKB.DiagID == _mkb).first() if _mkb else None
    mkbex = MKB.query.filter(MKB.DiagID == _mkbex).first() if _mkbex else None
    if diagnostic_id:
        diag = Diagnostic.query.get(diagnostic_id)
        diag.deleted = deleted
        diag.setDate = set_date
        diag.endDate = end_date
        diag.diagnosisType = diagnosis_type
        diag.character = character
        diag.person = person
        diag.speciality = speciality
        diag.notes = notes
        diag.result = result
        diag.rbAcheResult = ache_result
        diag.healthGroup = health_group
        diag.traumaType = trauma_type
        diag.phase = phase
        diag.stage = stage
        diag.dispanser = dispanser
        diag.diagnosis_description = diagnosis_description

        diagnosis = diag.diagnosis
        if not diagnosis or diagnosis.deleted:
            raise Exception('Diagnosis record can\'t be found')
        diagnosis.mkb = mkb
        diagnosis.mkb_ex = mkbex
    else:
        diag = Diagnostic()
        diag.event = event
        diag.setDate = safe_date(set_date)
        diag.endDate = safe_date(end_date)
        diag.diagnosisType = diagnosis_type
        diag.character = character
        diag.person = person
        diag.speciality = speciality
        diag.notes = notes
        diag.result = result
        diag.rbAcheResult = ache_result
        diag.healthGroup = health_group
        diag.traumaType = trauma_type
        diag.phase = phase
        diag.stage = stage
        diag.dispanser = dispanser
        diag.diagnosis_description = diagnosis_description
        if action:
            diag.action = action
        # etc
        diag.sanatorium = 0
        diag.hospital = 0

        diagnosis = Diagnosis()
        diagnosis.client = client
        diagnosis.mkb = mkb
        diagnosis.mkb_ex = mkbex
        diagnosis.diagnosisType = diagnosis_type
        diagnosis.character = character
        diagnosis.traumaType = trauma_type
        diagnosis.setDate = safe_date(set_date)
        diagnosis.endDate = safe_date(set_date)
        diagnosis.person = person
        # etc
        diagnosis.dispanser_id = None
        diagnosis.mod_id = None

        diag.diagnosis = diagnosis

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
    if diagnostic.diagnosis and not diagnostic.diagnosis.deleted:
        diagnostic.diagnosis.deleted = 1
    db.session.add(diagnostic)
