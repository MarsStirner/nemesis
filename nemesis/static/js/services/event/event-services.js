'use strict';

angular.module('WebMis20.services').
    service('WMEventServices', [
            '$http', '$injector', '$q', 'MessageBox', 'Settings', 'WMEventFormState', 'CurrentUser', 'PaymentKind', 'RefBookService', 'WMConfig',
            function ($http, $injector, $q, MessageBox, Settings, WMEventFormState, CurrentUser, PaymentKind, RefBookService, WMConfig) {
        var rbDiagnosisType = RefBookService.get('rbDiagnosisTypeN');
        function contains_sg (event, at_id, service_id) {
            return event.services.some(function (sg) {
                return sg.at_id === at_id && (sg.service_id !== undefined ? sg.service_id === service_id : true);
            });
        }
        function check_event_ache_result_required() {
            return Settings.get_string('Event.mandatoryResult') == '1';
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

        function check_event_diagnoses_results(event){
            var deferred = $q.defer();
            var diags_without_result = event.diagnoses.filter(function(diag){
                for (var diag_type_code in diag.diagnosis_types){
                    var diag_type = rbDiagnosisType.get_by_code(diag_type_code);
                    if (diag.diagnosis_types[diag_type_code].code != 'associated' && diag_type.require_result && !diag.diagnostic.ache_result){
                        return true
                    }
                }
                return false
            })

            if(diags_without_result.length) {
                var msg = ('Необходимо указать результат для диагнозов:{0} <br><br>').format(
                    diags_without_result.reduce(function(a, b){return a + '<br>' + b.diagnostic.mkb.code}, ""));
                return MessageBox.error('Невозможно закрыть обращение', msg);
            }

            deferred.resolve();
            return deferred.promise;
        }

        function check_event_main_diagnoses(event){
            var types_with_main = [];
            _.each(event.diagnoses, function(diagnosis) {
                _.each(diagnosis.diagnosis_types, function (diagnosis_kind, diagnosis_type_code) {
                    if (diagnosis_kind.code == 'main') {
                        types_with_main.push(diagnosis_type_code)
                    }
                });
            });

            var types_without_main = _.filter(event.info.diagnosis_types, function(diagnosis_type) {
                return !types_with_main.has(diagnosis_type.code)
            });

            if (types_without_main.length) {
                return MessageBox.error(
                    'Невозможно закрыть обращение',
                    'Необходимо указать основной диагноз на вкладках:<br> * {0}<br><br>'.format(
                        '<br/> * '.join(_.pluck(types_without_main, 'name'))
                    )
                );
            }
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        }

        function check_event_oparin_diagnoses (event) {
            // Сделано для удовлетворения тикета TMIS-1085.
            var may_close = false;
            _.each(event.diagnoses, function(diagnosis) {
                _.each(diagnosis.diagnosis_types, function (diagnosis_kind, diagnosis_type_code) {
                    may_close = may_close || diagnosis_type_code == 'final' || diagnosis_kind.code == 'main';
                });
            });
            if (!may_close) {
                return MessageBox.error('Невозможно закрыть обращение', 'Необходимо указать основной или заключительный диагноз')
            }
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        }

        function check_event_unclosed_actions(event) {
            var deferred = $q.defer();
            var unclosed_actions = event.info.actions.filter(function (action) {
                return action.status.code !== 'finished';
            }).map(function (action) {
                return action.at_name;
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
            coordinate: function (action, off) {
                var user = off ? null : {id: CurrentUser.id},
                    date = off ? null : new Date();
                if ((action.is_coordinated() && off) || (!action.is_coordinated() && !off)) {
                    action.coord_person = user;
                    action.coord_date = date;
                }
            },
            get_action_ped: function (action_type_id) {
                var deferred = $q.defer();
                $http.get(WMConfig.url.actions.get_action_ped, {
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
                    check_event_diagnoses_results(event).then(function () {
                        // Сделано для удовлетворения тикета TMIS-1085.
                        var dfrd = (event.info.event_type.request_type.code == 'policlinic' && event.info.event_type.finance.code == '2')
                            ? check_event_oparin_diagnoses(event)
                            : check_event_main_diagnoses(event);
                        dfrd.then(function () {
                            check_event_unclosed_actions(event).then(function () {
                                deferred.resolve();
                            });
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
                return $http.delete(WMConfig.url.actions.delete_action.format(action.id));
            },
            isPaymentPerService: function(event) {
                return safe_traverse(event, ['payment', 'paymentKind']) === PaymentKind.perService;
            }
        };
    }]).
    service('WMEventFormState', [function () {
        var rt = {},
            fin = {},
            is_new = null;
        var stat_codes = ['clinic', 'hospital', 'stationary'];
        return {
            set_state: function (request_type, finance, is_new) {
                rt = request_type || {};
                fin = finance || {};
            },
            is_new: function () {
                return is_new;
            },
            is_policlinic: function () {
                return rt.code === 'policlinic';
            },
            is_stationary: function () {
                return stat_codes.has(rt.code);
            },
            is_diagnostic: function () {
                return rt.code === '4' || rt.code === 'diagnosis' || rt.code === 'diagnostic';
            },
            is_paid: function () {
                return fin.code === '4';
            },
            is_oms: function (client, type) {
                return fin.code === '2';
            },
            is_dms: function (client, type) {
                return fin.code === '3';
            },
            has_commitment_letter: function () {
                return ['3', '5'].has(fin.code);
            }
        };
    }]);