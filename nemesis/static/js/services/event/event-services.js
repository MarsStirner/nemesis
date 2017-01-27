'use strict';

angular.module('WebMis20.services').
    service('WMEventServices', [
            '$http', '$injector', '$q', 'MessageBox', 'Settings', 'WMEventFormState', 'CurrentUser', 'RefBookService', 'WMConfig',
            function ($http, $injector, $q, MessageBox, Settings, WMEventFormState, CurrentUser, RefBookService, WMConfig) {
        var rbDiagnosisType = RefBookService.get('rbDiagnosisTypeN');
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

        function check_event_diagnoses_results(event){
            var deferred = $q.defer();
            var diags_without_result = event.diagnoses_all.filter(function(diag){
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
            _.each(event.diagnoses_all, function(diagnosis) {
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
                    'В обращении отсутствует основной диагноз'
                );
            }
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        }

        function check_event_oparin_diagnoses (event) {
            // Сделано для удовлетворения тикета TMIS-1085.
            var may_close = false;
            _.each(event.diagnoses_all, function(diagnosis) {
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
            get_action_ped: function (action_type_id, event_id) {
                var deferred = $q.defer();
                $http.get(WMConfig.url.actions.get_action_ped, {
                    params: {
                        action_type_id: action_type_id,
                        event_id: event_id
                    }
                }).success(function (data) {
                    deferred.resolve(new Date(data.result.ped));
                }).error(function (response) {
                    deferred.reject();
                });
                return deferred.promise;
            },
            delete_event: function (event) {
                return $http.post(
                    WMConfig.url.event.delete_event, {
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
                return $http.post(WMConfig.url.event.event_close, {
                    event: event.info
                });
            },
            delete_action: function (event, action) {
                var self = this;
                return $http.delete(WMConfig.url.actions.action_delete.format(action.id));
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