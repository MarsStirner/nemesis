'use strict';

angular.module('WebMis20.services.models').
    service('WMEventCache', ['WMEvent', '$q', function (WMEvent, $q) {
        var cache = {},
            loading = {};
        this.get = function (event_id) {
            var deferred_from_cache,
                deferred_next_request;
            if (cache.hasOwnProperty(event_id)) {
                deferred_from_cache = $q.defer();
                deferred_from_cache.resolve(cache[event_id]);
                return deferred_from_cache.promise;
            } else if (loading.hasOwnProperty(event_id)) {
                return loading[event_id].promise;
            }
            var event = new WMEvent(event_id);
            deferred_next_request = $q.defer();
            loading[event_id] = deferred_next_request;
            return event.reload().then(function () {
                if (!cache.hasOwnProperty(event_id)) {
                    cache[event_id] = event;
                }
                if (loading.hasOwnProperty(event_id)) {
                    loading[event_id].resolve(event);
                    loading[event_id] = undefined;
                }
                return event;
            });
        };
        return this;
    }]).
    factory('WMEvent', ['$http', '$q', 'WMClient', 'WMConfig',
        function($http, $q, WMClient, WMConfig) {
            var WMEvent = function(event_id, client_id, ticket_id) {
                this.event_id = parseInt(event_id);
                this.client_id = client_id;
                this.ticket_id = ticket_id;
                this.info = null;
                this.diagnoses = [];
                this.diagnoses_all = [];
                this.services = [];
                this.invoices = [];
                this.allergies = [];
                this.intolerances = [];
                this.ro = false;
                this.can_read_diagnoses = false;
                this.can_edit_diagnoses = false;
                this.can_create_actions = [false, false, false, false];
                this.request_type_kind = null;
                return this;
            };

            WMEvent.prototype.get_data = function(self, data){
                self.info = data.result.event;
                self.allergies = data.result.allergies;
                self.intolerances = data.result.intolerances;
                self.ro = data.result.ro;
                self.can_read_diagnoses = data.result.can_read_diagnoses;
                self.can_edit_diagnoses = data.result.can_edit_diagnoses;
                self.can_create_actions = data.result.can_create_actions;
                var client_info = self.info.client;
                self.info.client = new WMClient();
                self.info.client.init_from_obj({
                    client_data: client_info
                }, 'for_event');
                var diagnoses_all = (_.isArray(data.result.diagnoses)) ? data.result.diagnoses : [];
                self.diagnoses_all = diagnoses_all;
                self.diagnoses = _.filter(diagnoses_all, function (diag) {return ! diag.end_date});
                self.services = data.result.services;
                self.invoices = data.result.invoices;
                self.is_closed = self.closed();
            };

            WMEvent.prototype.reload = function() {
                var self = this;
                var url = this.is_new() ? WMConfig.url.event.event_new : WMConfig.url.event.event_get;
                var params = this.is_new() ? {
                    client_id: this.client_id,
                    ticket_id: this.ticket_id,
                    request_type_kind: this.request_type_kind
                } : {
                    event_id: this.event_id
                };
                return $http.get(url, {
                    params: params
                }).success(function (data) {
                    self.get_data(self, data);
                });
            };

            WMEvent.prototype.save = function(close_event) {
                var self = this;
                var deferred = $q.defer();
                $http.post(WMConfig.url.event.event_save, {
                    event: this.info,
                    diagnoses: this.diagnoses,  // TODO: Отдаются только актуальные диагнозы. Надо закрытые?
                    ticket_id: this.ticket_id,
                    close_event: close_event,
                    request_type_kind: this.request_type_kind
                })
                .success(function(response) {
                    var event_id = response.result.id,
                        error_text = response.result.error_text;
                    deferred.resolve({
                        event_id: event_id,
                        error_text: error_text
                    });
                })
                .error(function(response) {
                    deferred.reject(response.meta.name);
                });
                return deferred.promise;
            };

            WMEvent.prototype.is_new = function() {
                return !this.event_id;
            };

            WMEvent.prototype.closed = function() {
                return this.info && this.info.result_id !== null && this.info.exec_date !== null;
            };

            return WMEvent;
        }
    ]).
    factory('WMPoliclinicEvent', ['WMEvent', function(WMEvent) {
            var WMPoliclinicEvent = function (event_id, client_id, ticket_id) {
                WMEvent.call(this, event_id, client_id, ticket_id);
                this.request_type_kind = "policlinic";
            };
            WMPoliclinicEvent.inheritsFrom(WMEvent);
            return WMPoliclinicEvent
        }
    ]).
    factory('WMStationaryEvent', ['WMEvent', '$q', '$http', 'WMConfig', function(WMEvent, $q, $http, WMConfig) {
            var WMStationaryEvent = function (event_id, client_id, ticket_id) {
                WMEvent.call(this, event_id, client_id, ticket_id);
                this.request_type_kind = "stationary";
                this.blood_history = [];
            };
            WMStationaryEvent.inheritsFrom(WMEvent);
            WMStationaryEvent.prototype.get_data = function(self, data) {
                WMEvent.prototype.get_data(self, data);
                self.admission_date = data.result.admission_date;
                self.discharge_date = data.result.discharge_date;
                self.hosp_length = data.result.hosp_length;
                self.patient_current_os = data.result.patient_current_os;
                self.hospital_bed = data.result.hospital_bed;
                self.attending_doctor = data.result.attending_doctor;
                self.received = data.result.received;
                self.movings = data.result.movings;
                self.blood_history = data.result.blood_history;
                self.vmp_quoting = data.result.vmp_quoting;
            };
            WMStationaryEvent.prototype.save = function() {
                var self = this;
                var deferred = $q.defer();
                $http.post(WMConfig.url.event.event_save, {
                    event: this.info,
                    received: this.received,
                    ticket_id: this.ticket_id,
                    request_type_kind: this.request_type_kind,
                    vmp_quoting: this.vmp_quoting
                })
                .success(function(response) {
                    var event_id = response.result.id,
                        error_text = response.result.error_text;
                    deferred.resolve({
                        event_id: event_id,
                        error_text: error_text
                    });
                })
                .error(function(response) {
                    deferred.reject(response.meta.name);
                });
                return deferred.promise;
            };
            return WMStationaryEvent
        }
    ]);