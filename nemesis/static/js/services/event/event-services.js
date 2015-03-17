'use strict';

angular.module('WebMis20.services').
    service('WMEventServices', ['$http', '$injector', '$q', 'MessageBox', 'Settings', 'WMEventFormState', 'CurrentUser',
            function ($http, $injector, $q, MessageBox, Settings, WMEventFormState, CurrentUser) {
        function contains_sg (event, at_id, service_id) {
            return event.services.some(function (sg) {
                return sg.at_id === at_id && (sg.service_id !== undefined ? sg.service_id === service_id : true);
            });
        }
        function check_event_ache_result_required() {
            return new Settings().get_string('Event.mandatoryResult') == '1'; // FIXME: change factory to service
        }

        function check_event_results(event) {
            var deferred = $q.defer();
            if (!event.info.result) {
                return MessageBox.error('Невозможно закрыть обращение', 'Необходимо задать результат');
            }
            if (check_event_ache_result_required() && !WMEventFormState.is_diagnostic() && !event.info.ache_result){
                return MessageBox.error('Невозможно закрыть обращение', 'Необходимо задать исход заболевания/госпитализации');
            }
            deferred.resolve();
            return deferred.promise;
        }
        function check_event_final_diagnosis(event) {
            var deferred = $q.defer();
            if (!WMEventFormState.is_diagnostic()) {
                var final_diagnosis = event.diagnoses.filter(function (diag) {
                    return diag.diagnosis_type.code == 1;
                });
                if (!final_diagnosis.length) {
                    return MessageBox.error('Невозможно закрыть обращение', 'Необходимо указать заключительный диагноз');
                } else if (final_diagnosis.length > 1) {
                    return MessageBox.error('Невозможно закрыть обращение', 'В обращении не может быть больше одного заключительного диагноза');
                }
                if (!final_diagnosis[0].result) {
                    return MessageBox.error('Невозможно закрыть обращение', 'Необходимо указать результат заключительного диагноза');
                }
            }
            deferred.resolve();
            return deferred.promise;
        }
        function check_event_unclosed_actions(event) {
            var deferred = $q.defer();
            var unclosed_actions = event.info.actions.filter(function (action) {
                return action.status.code !== 'finished';
            }).map(function (action) {
                return action.name;
            });
            if (unclosed_actions.length) {
                var msg = ('Следующие действия не завершены:<br> * {0}<br><br>' +
                    'Продолжить процесс закрытия обращения?').format(unclosed_actions.join('<br> * '));
                return MessageBox.question('Имеются незакрытые действия', msg);
            } else {
                deferred.resolve();
            }
            return deferred.promise;
        }

        return {
            add_service: function(event, service_group) {
                if (!contains_sg(event, service_group.at_id, service_group.service_id)) {
                    var service_data = angular.extend(
                            service_group,
                            {
                                amount: 1,
                                sum: service_group.price,
                                actions: [undefined]
                            }
                        ),
                        SgModel = $injector.get('WMEventServiceGroup');
                    event.services.push(new SgModel(service_data, event.payment.payments));
                }
            },
            remove_service: function(event, sg_idx) {
                if (!confirm('Вы действительно хотите удалить выбранную группу услуг?')) {
                    return;
                }
                var sg = event.services[sg_idx];
                var action_id_list = sg.actions.map(function (a) {
                    return a.action_id;
                });
                var group_saved = action_id_list.length && action_id_list.every(function (a_id) {
                    return a_id !== undefined && a_id !== null;
                });
                if (group_saved) {
                    $http.post(
                        url_for_event_api_service_delete_service, {
                            event_id: event.info.id,
                            action_id_list: action_id_list
                        }
                    ).success(function() {
                        event.services.splice(sg_idx, 1);
                    }).error(function() {
                        alert('error');
                    });
                } else {
                    event.services.splice(sg_idx, 1);
                }
            },
            remove_action: function (event, action, sg) {
                if (action.action_id && !confirm('Вы действительно хотите удалить выбранную услугу?')) {
                    return;
                }
                var sg_idx = event.services.indexOf(sg),
                    action_idx = event.services[sg_idx].actions.indexOf(action),
                    self = this;
                if (action.action_id) {
                    $http.post(
                        url_for_event_api_service_delete_service, {
                            action_id_list: [action.action_id]
                        }
                    ).success(function () {
                        sg.actions.splice(action_idx, 1);
                        if (!sg.actions.length) {
                            self.remove_service(event, sg_idx)
                        }
                    }).error(function () {
                        alert('error');
                    });
                } else {
                    sg.actions.splice(action_idx, 1);
                    if (!sg.actions.length) {
                        self.remove_service(event, sg_idx)
                    }
                }
            },
            coordinate: function (action, off) {
                var user = off ? null : {id: CurrentUser.id},
                    date = off ? null : new Date();
                if ((action.is_coordinated() && off) || (!action.is_coordinated() && !off)) {
                    action.coord_person = user;
                    action.coord_date = date;
                }
            },
            update_payment: function (event, payment) {
                var cur_lc = event.payment.local_contract;
                if (cur_lc.date_contract && !payment.local_contract.date_contract) {
                    payment.local_contract.date_contract = cur_lc.date_contract;
                }
                if ((cur_lc.number_contract !== null || cur_lc.number_contract !== undefined) &&
                    !payment.local_contract.number_contract) {
                    payment.local_contract.number_contract = cur_lc.number_contract;
                }
                event.payment.local_contract = payment.local_contract;
                event.payment.payments.set_payments(payment.payments);
            },
            get_action_ped: function (action_type_id) {
                var deferred = $q.defer();
                $http.get(url_api_get_action_ped, {
                    params: {
                        action_type_id: action_type_id
                    }
                }).success(function (data) {
                    deferred.resolve(new Date(data.result.ped));
                }).error(function (response) {
                    deferred.reject();
                });
                return deferred.promise;
            },
            get_prev_events_contracts: function (client_id, finance_id, set_date) {
                var deferred = $q.defer();
                $http.get(url_api_prev_event_payment_info_get, {
                    params: {
                        client_id: client_id,
                        finance_id: finance_id,
                        set_date: set_date
                    }
                }).success(function (data) {
                    deferred.resolve(data.result)
                }).error(function() {
                    deferred.reject('Произошла ошибка получения данных предыдущих обращений');
                });
                return deferred.promise;
            },
            clear_local_contract: function (event) {
                var lc = event.payment && event.payment.local_contract;
                if (lc) {
                    lc.id = null;
                    lc.first_name = null;
                    lc.last_name = null;
                    lc.patr_name = null;
                    lc.birth_date = null;
                    lc.doc_type = null;
                    lc.serial_left = null;
                    lc.serial_right = null;
                    lc.number = null;
                    lc.reg_address = null;
                    lc.payer_org = null;
                    lc.payer_org_id = null;
                    lc.shared_in_events = null;
                }
            },
            get_new_diagnosis: function (action_info) {
                return {
                    'id': null,
                    'set_date': null,
                    'end_date': null,
                    'diagnosis_type': null,
                    'deleted': 0,
                    'diagnosis': {
                        'id': null,
                        'mkb': null,
                        'mkbex': null,
                        'client_id': null
                    },
                    'character': null,
                    'person': CurrentUser.get_main_user().info,
                    'notes': null,
                    'action_id': null,
                    'action': action_info ? action_info : null,
                    'result': null,
                    'ache_result': null,
                    'health_group': null,
                    'trauma_type': null,
                    'phase': null
                };
            },
            add_diagnosis: function (event, diagnosis) {
                event.diagnoses.push(diagnosis);
            },
            delete_diagnosis: function (diag_list, diagnosis, deleted) {
                if (arguments.length < 3) {
                    deleted = 1;
                }
                if (diagnosis && diagnosis.id) {
                    diagnosis.deleted = deleted;
                } else {
                    var idx = diag_list.indexOf(diagnosis);
                    diag_list.splice(idx, 1);
                }
            },
            reload_diagnoses: function (event) {
                return $http.get(url_api_diagnosis_get, {
                    params: {
                        event_id: event.event_id
                    }
                }).success(function (data) {
                    event.diagnoses = data.result;
                });
            },
            delete_event: function (event) {
                return $http.post(
                    url_for_delete_event, {
                        event_id: event.event_id
                    }
                );
            },
            check_can_close_event: function (event) {
                var deferred = $q.defer();
                check_event_results(event).then(function () {
                    check_event_final_diagnosis(event).then(function () {
                        check_event_unclosed_actions(event).then(function () {
                            deferred.resolve();
                        });
                    });
                });
                return deferred.promise;
            },
            close_event: function (event) {
                return $http.post(url_event_close, {
                    event: event.info
                });
            },
            delete_action: function (event, action) {
                var self = this;
                return $http.post(
                    url_for_event_api_delete_action, {
                        action_id: action.id
                    }
                ).success(function() {
                    event.info.actions.remove(action);
                    return self.reload_diagnoses(event);
                });
            }
        };
    }]).
    service('WMEventFormState', [function () {
        var rt = {},
            fin = {},
            is_new = null;
        return {
            set_state: function (request_type, finance, is_new) {
                rt = request_type || {};
                fin = finance || {};
                is_new = is_new;
            },
            is_new: function () {
                return is_new;
            },
            is_policlinic: function () {
                return rt.code === 'policlinic';
            },
            is_diagnostic: function () {
                return rt.code === '4';
            },
            is_paid: function () {
                return fin.code === '4';
            },
            is_oms: function (client, type) {
                return fin.code === '2';
            },
            is_dms: function (client, type) {
                return fin.code === '3';
            }
        };
    }]);