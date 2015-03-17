'use strict';

angular.module('WebMis20.services.models').
    factory('WMClient', ['$http', '$q', '$rootScope',
        function($http, $q, $rootScope) {
            function initialize(self, data, info_type) {
                // В разных интерфейсах поля модели могут отличаться
                function add_id_doc() {
                    var id_doc = data.client_data.id_document;
                    self.id_docs = id_doc !== null ? [id_doc] : [];
                }
                function add_policies(for_editing) {
                    if (for_editing) {
                        var cpol = data.client_data.compulsory_policy;
                        self.compulsory_policies = cpol !== null ? [cpol] : [];
                    } else {
                        self.compulsory_policy = data.client_data.compulsory_policy;
                    }
                    self.voluntary_policies = data.client_data.voluntary_policies;
                }
                function add_addresses(for_editing) {
                    var reg_addr = data.client_data.reg_address;
                    var live_addr = data.client_data.live_address;
                    if (live_addr !== null && live_addr.synced) {
                        reg_addr.live_id = live_addr.id;
                        reg_addr.synced = true;
                        live_addr = reg_addr;
                    }
                    if (for_editing) {
                        self.reg_addresses = reg_addr !== null ? [reg_addr] : [];
                        self.live_addresses = live_addr !== null ? [live_addr] : [];
                    } else {
                        self.reg_address = reg_addr;
                        self.live_address = live_addr;
                    }
                }
                function add_characteristics() {
                    var blood_types = data.client_data.blood_history;
                    self.blood_types = blood_types !== null ? blood_types : [];
                    var allergies = data.client_data.allergies;
                    self.allergies = allergies !== null ? allergies : [];
                    var intolerances = data.client_data.intolerances;
                    self.intolerances = intolerances !== null ? intolerances : [];
                }
                function add_soc_statuses() {
                    self.soc_statuses = data.client_data.soc_statuses;
                    self.invalidities = self.soc_statuses.filter(function(status) {
                        return status.ss_class.code == 2;
                    });
                    self.works = self.soc_statuses.filter(function(status) {
                        return status.ss_class.code == 3;
                    });
                    self.nationalities = self.soc_statuses.filter(function(status) {
                        return status.ss_class.code == 4;
                    });
                }
                function add_relations() {
                    var relations = data.client_data.relations;
                    self.relations = relations !== null ? relations : [];
                }
                function add_contacts() {
                    var contacts = data.client_data.contacts;
                    self.contacts = contacts !== null ? contacts : [];
                }

                self.info = data.client_data.info;
                if (info_type === 'for_editing') {
                    add_id_doc();
                    add_policies(true);
                    add_addresses(true);
                    add_characteristics();
                    add_soc_statuses();
                    add_relations();
                    add_contacts();
                    self.document_history = data.client_data.document_history;
                    self.deleted_entities = {}; // deleted items to save
                } else if (info_type === 'for_event') {
                    add_id_doc();
                    add_policies();
                    add_addresses();
                    add_relations();
                    add_contacts();
                } else if (info_type === 'for_servicing') {
                    add_id_doc();
                    add_policies();
                    add_addresses();
                    add_contacts();
                    self.appointments = data.appointments;
                    self.events = data.events;
                }
            }

            var WMClient = function(client_id) {
                this.client_id = client_id;
            };

            WMClient.prototype.reload = function(info_type) {
                var self = this;
                var deferred = $q.defer();
                var url_args = { client_id: this.client_id };
                if (info_type !== undefined) {
                    url_args[info_type] = true;
                } else {
                    info_type = 'for_editing';
                }

                $http.get(url_client_get, {
                    params: url_args
                }).success(function(data) {
                    initialize(self, data.result, info_type);
                    deferred.resolve();
                }).error(function(data, status) {
                    var message = status === 404 ? 'Пациент с id ' + self.client_id + ' не найден.' : data.result;
                    deferred.reject(message);
                });
                return deferred.promise;
            };

            WMClient.prototype.init_from_obj = function (client_data, info_type) {
                if (info_type === undefined) {
                    info_type = 'for_editing';
                }
                initialize(this, client_data, info_type);
            };

            WMClient.prototype.save = function() {
                var data = this.get_changed_data();
                var t = this;
                var deferred = $q.defer();
                $http.post(url_client_save, data).
                    success(function(value, headers) {
                        deferred.resolve(value['result']);
                    }).
                    error(function(response) {
                        var rr = response.result;
                        var message = rr.name + ': ' + (rr.data ? rr.data.err_msg : '');
                        deferred.reject(message);
                    });
                return deferred.promise;
            };

            WMClient.prototype.get_changed_data = function() {
                var data = {
                    client_id: this.client_id
                };
                if (this.info.dirty) { data.info = this.info; }
                data.id_docs = this._get_entity_changes('id_docs');
                data.reg_addresses = this._get_entity_changes('reg_addresses');
                data.live_addresses = this._get_entity_changes('live_addresses');
                data.compulsory_policies = this._get_entity_changes('compulsory_policies');
                data.voluntary_policies = this._get_entity_changes('voluntary_policies');
                data.blood_types = this._get_entity_changes('blood_types');
                data.allergies = this._get_entity_changes('allergies');
                data.intolerances = this._get_entity_changes('intolerances');
                var soc_status_changes = [].
                    concat(this._get_entity_changes('invalidities') || []).
                    concat(this._get_entity_changes('works') || []).
                    concat(this._get_entity_changes('nationalities') || []);
                data.soc_statuses = soc_status_changes.length ? soc_status_changes : undefined;
                data.relations = this._get_entity_changes('relations');
                data.contacts = this._get_entity_changes('contacts');

                return data;
            };

            WMClient.prototype._get_entity_changes = function(entity) {
                var dirty_elements = this[entity].filter(function(el) {
                    return el.dirty;
                });
                var deleted_elements = this.deleted_entities[entity] || [];
                var changes = dirty_elements.concat(deleted_elements.filter(function(del_elmnt) {
                    return dirty_elements.indexOf(del_elmnt) === -1;
                }));
                return changes.length ? changes : undefined;
            };

            WMClient.prototype.is_new = function() {
                return this.client_id === 'new';
            };

            return WMClient;
        }
    ]);