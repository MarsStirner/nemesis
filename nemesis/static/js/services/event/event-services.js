'use strict';

angular.module('WebMis20.services').
    service('WMEventServices', [
            '$http', '$injector', '$q', 'MessageBox', 'Settings', 'WMEventFormState', 'CurrentUser', 'RefBookService', 'WMConfig',
            function ($http, $injector, $q, MessageBox, Settings, WMEventFormState, CurrentUser, RefBookService, WMConfig) {
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
            is_hospital: function () {
                return rt.code === 'hospital';
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
                return ['2', '3', '5'].has(fin.code);
            }
        };
    }]);
