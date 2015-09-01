# -*- coding: utf-8 -*-
from flask import render_template, request, redirect, current_app
from flask.ext.principal import Identity, identity_changed
from flask.ext.login import current_user
from sqlalchemy.orm import lazyload, joinedload

from nemesis.lib.utils import jsonify
from nemesis.lib.user import UserAuth, UserProfileManager
from nemesis.lib.jsonify import PersonTreeVisualizer
from nemesis.models.exists import rbUserProfile, Person
from nemesis.app import app
from nemesis.systemwide import db

__author__ = 'viruzzz-kun'


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


@app.route('/api/doctors_to_assist')
def api_doctors_to_assist():
    viz = PersonTreeVisualizer()
    persons = db.session.query(Person).add_entity(rbUserProfile).join(Person.user_profiles).filter(
        rbUserProfile.code.in_([UserProfileManager.doctor_clinic, UserProfileManager.doctor_diag])
    ).options(
        lazyload('*'),
        joinedload(Person.speciality),
        joinedload(Person.org_structure),
    ).order_by(
        Person.lastName,
        Person.firstName
    )
    res = [viz.make_person_for_assist(person, profile) for person, profile in persons]
    return jsonify(res)


