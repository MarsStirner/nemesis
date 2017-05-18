'use strict';

angular.module('WebMis20.services').
    service('WMClientServices', ['$timeout', 'MessageBox', 'RefBookService', 'CurrentUser', '$modal', '$http', '$q',
            'WMConfig', 'ApiCalls',
            function ($timeout, MessageBox, RefBookService, CurrentUser, $modal, $http, $q,
                      WMConfig, ApiCalls) {
        function get_actual_address (client, entity) {
            var addrs =  client[entity].filter(function (el) {
                return el.deleted === 0;
            });
            return addrs.length === 1 ? addrs[0] : null;
        }

        function make_address_copy(address, type, copy_into) {
            var copy = copy_into !== undefined ? angular.copy(address, copy_into) : angular.copy(address);
            copy.type = type;
            copy.synced = false;
            copy.dirty = true;
            if (type === 1) {
                copy.id = copy.live_id;
            }
            copy.live_id = undefined;
            return copy;
        }

        function delete_existing_record(client, entity, record, deleted) {
            if (record.id) {
                record.deleted = deleted;
                angular.isArray(client.deleted_entities[entity]) ?
                    client.deleted_entities[entity].push(record) :
                    client.deleted_entities[entity] = [record];
            }
        }

        function get_document_record() {
            return {
                "id": null,
                "deleted": 0,
                "doc_type": null,
                "serial": null,
                "number": null,
                "beg_date": null,
                "end_date": null,
                "origin": null,
                "doc_text": null,
                "file_attach": {}
            };
        }

        return {
            push_id_doc: function(client) {
                var new_doc = get_document_record();
                client.id_docs.push(new_doc);
                return new_doc;
            },
            add_id_doc: function(client) {
                this.push_id_doc(client);
            },
            delete_document: function(client, doc) {
                var self = this;
                MessageBox.question(
                    'Удаление документа',
                    'Документ будет удален. Продолжить?'
                ).then(function () {
                    self.delete_record(client, 'id_docs', doc);
                    self.add_id_doc(client);
                });
            },
            push_policy: function (client, type) {
                var entity = type === 0 ? 'compulsory_policies' : 'voluntary_policies';
                var obj = {
                    "id": null,
                    "deleted": 0,
                    "policy_type": null,
                    "serial": null,
                    "number": null,
                    "beg_date": null,
                    "end_date": null,
                    "insurer": null,
                    "policy_text": null,
                    "file_attach": {}
                };
                client[entity].push(obj);
                return obj;
            },
            add_new_cpolicy: function(client) {
                var self = this;
                var cpols = client.compulsory_policies.filter(function(p) {
                    return p.deleted === 0;
                });
                var cur_cpol = cpols[cpols.length - 1];
                if (cpols.length) {
                    var msg = [
                        'При добавлении нового полиса ОМС старый полис будет удален',
                        cur_cpol.id ? ' и станет доступен для просмотра в истории документов' : '',
                        '. Продолжить?'
                    ].join('');
                    MessageBox.question(
                        'Добавление полиса ОМС',
                        msg
                    ).then(function () {
                        self.delete_record(client, 'compulsory_policies', cur_cpol, 2);
                        self.push_policy(client, 0);
                    });
                } else {
                    self.push_policy(client, 0);
                }
            },
            add_new_vpolicy: function(client) {
                this.push_policy(client, 1);
            },
            delete_cpolicy: function(client, policy) {
                var self = this;
                MessageBox.question(
                    'Удаление полиса ОМС',
                    'Полис будет удален. Продолжить?'
                ).then(function () {
                    self.delete_record(client, 'compulsory_policies', policy);
                });
            },
            delete_vpolicy: function(client, policy) {
                var self = this;
                MessageBox.question(
                    'Удаление полиса ДМС',
                    'Полис будет удален. Продолжить?'
                ).then(function () {
                    self.delete_record(client, 'voluntary_policies', policy);
                });
            },
            push_address: function (client, type) {
                var entity = type === 0 ? 'reg_addresses' : 'live_addresses';
                var obj = {
                    "id": null,
                    "deleted": 0,
                    "type": type,
                    "address": null,
                    "free_input": null,
                    "locality_type": null,
                    "text_summary": null
                };
                client[entity].push(obj);
                return obj;
            },
            add_new_address: function (client, type) {
                var self = this;
                var entity = type === 0 ? 'reg_addresses' : 'live_addresses';
                var cur_addr = get_actual_address(client, entity);
                if (cur_addr) {
                    var msg = [
                        'При добавлении нового адреса старый адрес будет удален',
                        cur_addr.id ? ' и станет доступен для просмотра в истории' : '',
                        '. Продолжить?'
                    ].join('');
                    MessageBox.question(
                        'Добавление адреса',
                        msg
                    ).then(function () {
                        self.delete_address(client, type, cur_addr, 2, true);
                        self.push_address(client, type);
                    });
                } else {
                    self.push_address(client, type);
                }
            },
            delete_address: function (client, type, addr, deleted, silent) {
                var self = this;
                if (deleted === undefined) {
                    deleted = 1;
                }
                if (silent === undefined) {
                    silent = false;
                }
                var entity = type === 0 ? 'reg_addresses' : 'live_addresses';

                function _delete () {
                    if (addr.synced) {
                        var addr_idx_to_delete = client[entity].indexOf(addr),
                            addr_to_delete = make_address_copy(addr, type),
                            live_addr,
                            new_live_addr,
                            reg_addr,
                            la_idx;

                        // delete what should be deleted
                        delete_existing_record(client, entity, addr_to_delete, deleted);
                        self.delete_record(client, entity, null, deleted, addr_idx_to_delete);
                        // and make synced address independent record
                        if (type === 0) {
                            live_addr = get_actual_address(client, 'live_addresses');
                            la_idx = client.live_addresses.indexOf(live_addr);
                            self.delete_record(client, 'live_addresses', null, deleted, la_idx);

                            new_live_addr = self.push_address(client, 1);
                            make_address_copy(live_addr, 1, new_live_addr);
                        } else if (type === 1) {
                            reg_addr = get_actual_address(client, 'reg_addresses');
                            reg_addr.synced = false;
                            reg_addr.live_id = undefined;
                        }
                    } else {
                        self.delete_record(client, entity, addr, deleted);
                    }
                }

                if (silent) {
                    _delete();
                } else {
                    MessageBox.question(
                        'Удаление адреса',
                        'Адрес будет удален. Продолжить?'
                    ).then(function () {
                        _delete();
                    });
                }
            },
            sync_addresses: function (client, live_addr, same) {
                var self = this;
                var reg_addr = get_actual_address(client, 'reg_addresses');
                if (!reg_addr ) {
                    MessageBox.info(
                        'Невозможно скопировать адрес',
                        'Для копирования адреса заполните сначала адрес регистрации'
                    );
                    live_addr.synced = undefined;
                    return;
                }

                function _sync () {
                    if (same) {
                        live_addr.synced = false; // was updated after checkbox toggle
                        self.delete_record(client, 'live_addresses', live_addr, 2);
                        reg_addr.synced = true;
                        reg_addr.live_id = null;
                        client.live_addresses.push(reg_addr);
                        reg_addr.dirty = true;
                    } else {
                        var live_addr_idx = client.live_addresses.indexOf(live_addr),
                            live_addr_to_delete = make_address_copy(live_addr, 1);

                        // current live address record to be deleted
                        // if live address was stored before, place its copy record in list for deletion
                        delete_existing_record(client, 'live_addresses', live_addr_to_delete, 2);
                        // remove former synced live address record. Need to use index and null record
                        // lest reg address record would not be placed in deletion list
                        self.delete_record(client, 'live_addresses', null, 2, live_addr_idx);

                        // detach reg address
                        reg_addr.synced = false;
                        reg_addr.live_id = undefined;

                        // add new live address as copy from reg address
                        var new_live_addr = self.push_address(client, 1);
                        make_address_copy(reg_addr, 1, new_live_addr);
                        new_live_addr.id = null;
                    }
                }

                var to_be_changed = live_addr.synced ? live_addr.live_id : live_addr.id;
                if (to_be_changed) {
                    var msg = (same ? 'При копировании адреса текущая ' : 'Текущая ') +
                        'запись адреса будет удалена и станет доступна для просмотра в истории. Продолжить?';
                    MessageBox.question(
                        'Копирование адреса',
                        msg
                    ).then(function () {
                        _sync();
                    }, function () {
                        live_addr.synced = !live_addr.synced;
                    });
                } else {
                    _sync();
                }
            },
            add_new_blood_type: function(client) {
                var bt = client.blood_types;
                if (bt.length && !bt[0].id) {
                    bt.splice(0, 1);
                }
                client.blood_types.unshift({
                    'id': null,
                    'blood_type': null,
                    'date': null,
                    'person': null
                });
                bt[0].person = CurrentUser.info;
            },
            delete_blood_type: function(client, bt) {
                var self = this;
                MessageBox.question(
                    'Удаление группы крови',
                    'Вы действительно хотите удалить эту запись о группе крови?'
                ).then(function () {
                    self.delete_record(client, 'blood_types', bt);
                });
            },
            add_allergy: function(client) {
                client.allergies.push({
                    'id': null,
                    'deleted': 0,
                    'name': null,
                    'power': null,
                    'date': null,
                    'notes': null
                });
            },
            delete_allergy: function(client, allergy) {
                var self = this;
                MessageBox.question(
                    'Удаление аллергии',
                    'Вы действительно хотите удалить эту запись об аллергии?'
                ).then(function () {
                    self.delete_record(client, 'allergies', allergy);
                });
            },
            add_med_intolerance: function(client) {
                client.intolerances.push({
                    'id': null,
                    'deleted': 0,
                    'name': null,
                    'power': null,
                    'date': null,
                    'notes': null
                });
            },
            delete_med_intolerance: function(client, mi) {
                var self = this;
                MessageBox.question(
                    'Удаление медикаментозной непереносимости',
                    'Вы действительно хотите удалить эту запись о медикаментозной непереносимости?'
                ).then(function () {
                    self.delete_record(client, 'intolerances', mi);
                });
            },
            push_soc_status: function (client, class_name, class_code) {
                var document = null;
                if (class_code === '2') {
                    document = get_document_record();
                } else if (class_code === '3') {
                    document = {};
                }
                var new_ss = {
                    'deleted': 0,
                    'ss_class': {'code': class_code},
                    'ss_type': null,
                    'beg_date': null,
                    'end_date': null,
                    'self_document': document
                };
                client[class_name].push(new_ss);
                return new_ss;
            },
            add_soc_status_doc: function (ss) {
                ss.self_document = get_document_record();
            },
            clear_soc_status_doc: function (ss, formCtrl) {
                ss.self_document = {};
                if (formCtrl) {
                    $timeout(formCtrl.$setPristine);
                }
            },
            add_new_invalidity: function(client) {
                var self = this;
                var invld = client.invalidities.filter(function(i) {
                    return i.deleted === 0;
                });
                var cur_invld = invld[invld.length - 1];
                if (invld.length) {
                    var msg = [
                        'При добавлении новой инвалидности старая запись будет удалена',
                        cur_invld.id ? ' и станет доступна для просмотра в истории' : '',
                        '. Продолжить?'
                    ].join('');
                    MessageBox.question(
                        'Добавление инвалидности',
                        msg
                    ).then(function () {
                        self.delete_record(client, 'invalidities', cur_invld, 2);
                        self.push_soc_status(client, 'invalidities', '2');
                    });
                } else {
                    self.push_soc_status(client, 'invalidities', '2');
                }
            },
            delete_invalidity: function(client, invalidity) {
                var self = this;
                MessageBox.question(
                    'Удаление инвалидности',
                    'Вы действительно хотите удалить эту запись об инвалидности?'
                ).then(function () {
                    self.delete_record(client, 'invalidities', invalidity);
                });
            },
            add_new_work: function(client) {
                this.push_soc_status(client, 'works', '3')
            },
            delete_work: function(client, work) {
                var self = this;
                MessageBox.question(
                    'Удаление занятости',
                    'Вы действительно хотите удалить эту запись о занятости?'
                ).then(function () {
                    self.delete_record(client, 'works', work);
                });
            },
            add_new_nationality: function(client) {
                this.push_soc_status(client, 'nationalities', '4')
            },
            delete_nationality: function(client, nationality) {
                var self = this;
                MessageBox.question(
                    'Удаление гражданства',
                    'Вы действительно хотите удалить эту запись о гражданстве?'
                ).then(function () {
                    self.delete_record(client, 'nationalities', nationality);
                });
            },
            add_relation: function (client) {
                client.relations.push({
                    id: null,
                    deleted: 0,
                    rel_type: null,
                    direct: true,
                    relative: null
                });
            },
            delete_relation: function(client, relation) {
                var self = this;
                MessageBox.question(
                    'Удаление связи с другим пациентом',
                    'Вы действительно хотите удалить эту связь с другим пациентом?'
                ).then(function () {
                    self.delete_record(client, 'relations', relation);
                });
            },
            add_contact: function(client) {
                client.contacts.push({
                    'id': null,
                    deleted: 0,
                    contact_type: null,
                    contact_text: null,
                    notes: null
                });
            },
            delete_contact: function(client, contact) {
                var self = this;
                MessageBox.question(
                    'Удаление контакта',
                    'Вы действительно хотите удалить этот контакт?'
                ).then(function () {
                    self.delete_record(client, 'contacts', contact);
                });
            },
            delete_record: function(client, entity, record, deleted, idx) {
                if (arguments.length < 4) {
                    deleted = 1;
                }
                if (record && record.id) {
                    delete_existing_record(client, entity, record, deleted);
                } else {
                    var idx = idx !== undefined ? idx : client[entity].indexOf(record);
                    client[entity].splice(idx, 1);
                }
            },
            // addVmpCoupon: function (client) {
            //     var coupon = {
            //         id: null,
            //         number: 0,
            //         mkb: null,
            //         code: '',
            //         date: null,
            //         event: null,
            //         name: '',
            //         deleted: 0
            //     };
            //     this.editVmpCoupon(client, coupon).then(function (coupon) {
            //         client.vmp_coupons.push(coupon);
            //     });
            // },
            // removeVmpCoupon: function(client, coupon) {
            //     var self = this;
            //     MessageBox.question(
            //         'Удаление талона ВМП',
            //         'Вы действительно хотите удалить талон ВМП?'
            //     ).then(function () {
            //         $http.post(
            //             WMConfig.url.patients.coupon_delete, {
            //                 coupon: coupon
            //             }
            //         ).success(function(){
            //             self.delete_record(client, 'vmp_coupons', coupon)
            //         });
            //
            //     })
            // },
            // editVmpCoupon: function(client, coupon) {
            //     var self = this;
            //     var deferred = $q.defer();
            //     $modal.open({
            //         size: 'lg',
            //         templateUrl: '/nemesis/client/services/modal/edit_vmp_coupon.html',
            //         backdrop : 'static',
            //         resolve: {
            //             coupon: function () {
            //                 return coupon;
            //             }
            //         },
            //         controller: function ($scope, $modalInstance, coupon) {
            //             $scope.coupon_file = {};
            //             $scope.coupon = coupon;
            //             function reloadCoupon (coupon) {
            //                 $scope.coupon = coupon;
            //                 $scope.wrong_client = client.client_id != $scope.coupon.client.id;
            //                 $scope.nonunique = client.vmp_coupons.filter(function (coupon){
            //                     return coupon.number == $scope.coupon.number
            //                 }).length > 0;
            //             };
            //             $scope.parse_xlsx = function() {
            //                 ApiCalls.wrapper('POST', WMConfig.url.patients.coupon_parse, {}, {
            //                     coupon: $scope.coupon_file
            //                 }).then(reloadCoupon);
            //             }
            //         }
            //     }).result.then(function (result) {
            //         $http.post(
            //             WMConfig.url.patients.coupon_save, {
            //                 client_id: client.client_id,
            //                 coupon: result[0],
            //                 coupon_file: result[1]
            //             }
            //         ).success(function(data){
            //             deferred.resolve(data.result);
            //         }).error(function (data) {
            //             return MessageBox.error(
            //                 'Ошибка',
            //                 'Произошла ошибка добавления талона'
            //             );
            //         });
            //     });
            //     return deferred.promise;
            // }
        };
    }])
    .run(['$templateCache', function ($templateCache) {
        $templateCache.put(
            '/nemesis/client/services/modal/edit_vmp_coupon.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
                <h4 class="modal-title" id="myModalLabel">Загрузка талона ВМП</h4>\
            </div>\
            <div class="modal-body">\
                <div class="row marginal">\
                    <div class="col-md-8">\
                        <input type="file" wm-input-file file="coupon_file"\
                               accept="image/*,.pdf,.txt,.odt,.doc,.docx,.ods,.xls,.xlsx">\
                    </div>\
                    <div class="col-md-4">\
                        <button type="button" ng-disabled="!coupon_file.name" class="btn btn-default btn-sm" ng-click="parse_xlsx()">Загрузить</button>\
                    </div>\
                </div>\
                <div class="row" ng-if="coupon.number">\
                    <div class="col-md-12">\
                        <b>После загрузки файла проверьте правильность данных:</b>\
                    </div>\
                </div>\
                <div class="row" ng-if="wrong_client">\
                    <div class="col-md-12 text-danger">\
                        <b>Внимание! Убедитесь, что талон пренадлежит текущему пациенту!</b>\
                    </div>\
                </div>\
                <div class="row">\
                    <div class="col-md-12" ng-if="coupon.number">\
                        <table class="table table-condensed">\
                            <tbody>\
                                <tr>\
                                    <th>Пациент</th>\
                                    <th>[[coupon.client.name]]</th>\
                                </tr>\
                                <tr>\
                                    <th>№ талона</th>\
                                    <td>[[coupon.number]]</td>\
                                </tr>\
                                <tr>\
                                    <th>Диагноз</th>\
                                    <td>[[coupon.mkb.code]] [[coupon.mkb.name]]</td>\
                                </tr>\
                                <tr>\
                                    <th>Код ВМП</th>\
                                    <td>[[coupon.quota_type.code]]</td>\
                                </tr>\
                                <tr>\
                                    <th>дата планируемой госпитализации</th>\
                                    <td>[[coupon.date | asDate]]</td>\
                                </tr>\
                            </tbody>\
                        </table>\
                    </div>\
                </div>\
                <div class="row" ng-if="coupon.number">\
                    <div class="col-md-12">\
                        <b>Если данные верные - сохраните талон</b>\
                    </div>\
                </div>\
            </div>\
            <div class="modal-footer">\
                <div class="pull-right">\
                    <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
                    <button ng-disabled="nonunique" class="btn btn-success" ng-click="$close([coupon, coupon_file])">Сохранить</button>\
                </div>\
            </div>\
')
    }])
;