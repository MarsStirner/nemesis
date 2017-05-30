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
    factory('WMEvent', ['$http', '$q', '$injector', 'WMConfig',
        function($http, $q, $injector, WMConfig) {
            var WMClient;

            var WMEvent = function(event_id, client_id, ticket_id) {
                this.event_id = parseInt(event_id) || null;
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
                this.access = {
                    can_read_diagnoses: false,
                    can_edit_diagnoses: false,
                    can_create_actions: [false, false, false, false],
                    invoice_all: false
                };
                this.request_type_kind = null;
                return this;
            };

            WMEvent.prototype.get_data = function (data) {
                this.info = data.result.event;
                this.allergies = data.result.allergies;
                this.intolerances = data.result.intolerances;
                this.ro = data.result.access.ro;
                this.access.can_read_diagnoses = data.result.access.can_read_diagnoses;
                this.access.can_edit_diagnoses = data.result.access.can_edit_diagnoses;
                this.access.can_create_actions = data.result.access.can_create_actions;
                this.access.invoice_all = data.result.access.invoice_all;
                var client_info = this.info.client;
                if (!WMClient) WMClient = $injector.get('WMClient');
                this.info.client = new WMClient();
                this.info.client.init_from_obj({
                    client_data: client_info
                }, 'for_event');
                var diagnoses_all = (_.isArray(data.result.diagnoses)) ? data.result.diagnoses : [];
                this.diagnoses_all = diagnoses_all;
                this.diagnoses = _.filter(diagnoses_all, function (diag) {return ! diag.end_date});
                this.services = data.result.services;
                this.invoices = data.result.invoices;
                this.is_closed = this.closed();
            };
            WMEvent.prototype.init_from_obj = function (data) {
                this.get_data(data);
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
                    self.get_data(data);
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
            WMEvent.prototype.clone = function () {
                var copy = new this.constructor();
                for (var prop in this) {
                    if (this.hasOwnProperty(prop)) {
                        copy[prop] = _.deepCopy(this[prop]);
                    }
                }
                return copy;
            };

            WMEvent.prototype.is_new = function() {
                return !this.event_id;
            };

            WMEvent.prototype.closed = function() {
                return this.info && this.info.result_id !== null && this.info.exec_date !== null;
            };
            
            WMEvent.prototype.can_create_actions = function(action_type_group) {
               var at_class = {
                'medical_documents': 0,
                'diagnostics': 1,
                'lab': 1,
                'treatments': 2
               };
              return this.access.can_create_actions[at_class[action_type_group]]
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
            WMStationaryEvent.prototype.get_data = function(data) {
                WMEvent.prototype.get_data.call(this, data);
                this.admission_date = data.result.admission_date;
                this.discharge_date = data.result.discharge_date;
                this.hosp_length = data.result.hosp_length;
                this.patient_current_os = data.result.patient_current_os;
                this.hospital_bed = data.result.hospital_bed;
                this.attending_doctor = data.result.attending_doctor;
                this.received = data.result.received;
                this.movings = data.result.movings;
                this.blood_history = data.result.blood_history;
                this.vmp_quoting = data.result.vmp_quoting;
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

            WMStationaryEvent.prototype.can_create_actions = function(action_type_group) {
                if (action_type_group !== 'medical_documents') {
                    var couponEndDate = moment(safe_traverse(this, ['vmp_quoting', 'coupon', 'end_date']));
                    if (couponEndDate.isValid()) {
                        var isVmpCouponExpired = moment(new Date()).startOf('d').isAfter(couponEndDate.clone().startOf('d'));
                        return WMEvent.prototype.can_create_actions.call(this, action_type_group) && !isVmpCouponExpired;
                    }
                }
                return WMEvent.prototype.can_create_actions.call(this, action_type_group)
                
            };
            return WMStationaryEvent;
        }
    ]).
    factory('WMAdmissionEvent', ['$injector', 'WMEvent', 'WebMisApi',
            function($injector, WMEvent, WebMisApi) {
        var WMClient;

        var WMAdmissionEvent = function () {
            WMEvent.call(this);
            this.request_type_kind = "stationary";
        };
        WMAdmissionEvent.inheritsFrom(WMEvent);
        WMAdmissionEvent.prototype.get_data = function(data) {
            if (!WMClient) WMClient = $injector.get('WMClient');
            var wmclient = new WMClient();
            wmclient.init_from_obj({
                client_data: data.event.client
            }, 'for_admission_event');
            this.event_id = data.event.id;
            this.info = data.event;
            this.info.client = wmclient;

            this.received = data.received;
            return this;
        };
        WMAdmissionEvent.prototype.save = function() {
            var self = this;
            return WebMisApi.event.save({
                event: self.info,
                received: self.received,
                request_type_kind: self.request_type_kind
            }).then(function (result) {
                self.event_id = result.id;
                return self.reload();
            });
        };
        return WMAdmissionEvent;
    }]);
