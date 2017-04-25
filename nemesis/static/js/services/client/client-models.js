'use strict';

angular.module('WebMis20.services.models').
    factory('WMClient', ['ApiCalls', 'WMConfig', 'WMAdmissionEvent',
        function(ApiCalls, WMConfig, WMAdmissionEvent) {
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
//                    self.soc_statuses = data.client_data.soc_statuses;
                    self.invalidities = data.client_data.invalidities;
                    self.works = data.client_data.works;
                    self.nationalities = data.client_data.nationalities;
                }
                function add_relations() {
                    var relations = data.client_data.relations;
                    self.relations = relations !== null ? relations : [];
                }
                function add_contacts() {
                    var contacts = data.client_data.contacts;
                    self.contacts = contacts !== null ? contacts : [];
                }
                function add_file_attaches() {
                    self.file_attaches = data.client_data.file_attaches;
                    var map = {};
                    self.file_attaches.forEach(function (fa, idx) {
                        map[fa.id] = idx;
                    });
                    self.id_docs.forEach(function (id_doc) {
                        if (id_doc.file_attach.id) {
                            id_doc.file_attach = self.file_attaches[map[id_doc.file_attach.id]];
                        }
                    });
                    self.compulsory_policies.forEach(function (cpol) {
                        if (cpol.file_attach.id) {
                            cpol.file_attach = self.file_attaches[map[cpol.file_attach.id]];
                        }
                    });
                    self.voluntary_policies.forEach(function (vpol) {
                        if (vpol.file_attach.id) {
                            vpol.file_attach = self.file_attaches[map[vpol.file_attach.id]];
                        }
                    });
                    self.invalidities.forEach(function (invld) {
                        if (safe_traverse(invld, ['self_document', 'file_attach', 'id'])) {
                            invld.self_document.file_attach = self.file_attaches[map[invld.self_document.file_attach.id]];
                        }
                    });
                    self.works.forEach(function (work) {
                        if (safe_traverse(work, ['self_document', 'file_attach', 'id'])) {
                            work.self_document.file_attach = self.file_attaches[map[work.self_document.file_attach.id]];
                        }
                    });
                }
                function add_vmp_coupons() {
                    var vmp_coupons = data.client_data.vmp_coupons;
                    self.vmp_coupons = vmp_coupons !== null ? vmp_coupons : [];
                }

                self.info = data.client_data.info;
                self.client_id = self.info.id;
                if (info_type === 'for_editing') {
                    add_id_doc();
                    add_policies(true);
                    add_addresses(true);
                    add_characteristics();
                    add_soc_statuses();
                    add_relations();
                    add_contacts();
                    add_file_attaches();
                    add_vmp_coupons();
                    self.document_history = data.client_data.document_history;
                    self.deleted_entities = {}; // deleted items to save
                } else if (info_type === 'for_event') {
                    add_id_doc();
                    add_policies();
                    add_addresses();
                    add_relations();
                    add_contacts();
                    // Do we need? add_vmp_coupons();
                } else if (info_type === 'for_servicing') {
                    add_id_doc();
                    add_policies();
                    add_addresses();
                    add_contacts();
                    // Do we need? add_vmp_coupons();
                    self.appointments = data.appointments;
                    self.events = data.events;
                    if (data.current_hosp) {
                        if (!self.current_hosp) {
                            self.current_hosp = new WMAdmissionEvent();
                        }
                        self.current_hosp.init_from_obj(data.current_hosp);
                    }
                }
            }

            var WMClient = function(client_id) {
                this.client_id = client_id;
            };

            WMClient.prototype.reload = function(info_type) {
                var self = this;
                var url_args = { client_id: this.client_id };
                if (_.isUndefined(info_type)) {
                    info_type = 'for_editing';
                } else {
                    url_args[info_type] = true;
                }

                return ApiCalls.wrapper('GET', WMConfig.url.patients.client_get, url_args)
                    .then(function(result) {
                        initialize(self, result, info_type);
                    });
            };

            WMClient.prototype.init_from_obj = function (client_data, info_type) {
                initialize(this, client_data, info_type);
            };

            WMClient.prototype.save = function() {
                var data = this.get_changed_data();
                return ApiCalls.wrapper('POST', WMConfig.url.patients.client_save, undefined, data);
            };

            WMClient.prototype.clone = function () {
                var copy = new this.constructor();
                for (var prop in this) {
                    if (this.hasOwnProperty(prop)) {
                        copy[prop] = _.deepCopy(this[prop]);
                    }
                }
                return copy;
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
                data.invalidities = this._get_entity_changes('invalidities');
                data.works = this._get_entity_changes('works');
                data.nationalities = this._get_entity_changes('nationalities');
                data.relations = this._get_entity_changes('relations');
                data.contacts = this._get_entity_changes('contacts');
                data.vmp_coupons = this._get_entity_changes('vmp_coupons');

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
