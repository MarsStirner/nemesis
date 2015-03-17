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
    factory('WMEvent', ['$http', '$q', 'WMClient', 'WMEventServiceGroup', 'WMEventPaymentList',
        function($http, $q, WMClient, WMEventServiceGroup, WMEventPaymentList) {
            var WMEvent = function(event_id, client_id, ticket_id) {
                this.event_id = parseInt(event_id);
                this.client_id = client_id;
                this.ticket_id = ticket_id;
                this.info = null;
                this.payment = null;
                this.diagnoses = [];
                this.services = [];
                this.ro = false;
                this.has_access_to_payment_info = false;
                this.can_read_diagnoses = false;
                this.can_edit_diagnoses = false;
                this.can_create_actions = [false, false, false, false];
                return this;
            };

            WMEvent.prototype.reload = function() {
                var self = this;
                var url = this.is_new() ? url_event_new : url_event_get;
                var params = this.is_new() ? {
                    client_id: this.client_id,
                    ticket_id: this.ticket_id
                } : {
                    event_id: this.event_id
                };
                return $http.get(url, {
                    params: params
                }).success(function (data) {
                    self.info = data.result.event;
                    self.ro = data.result.ro;
                    self.has_access_to_payment_info = data.result.has_access_to_payment_info;
                    self.can_read_diagnoses = data.result.can_read_diagnoses;
                    self.can_edit_diagnoses = data.result.can_edit_diagnoses;
                    self.can_create_actions = data.result.can_create_actions;
                    var client_info = self.info.client;
                    self.info.client = new WMClient();
                    self.info.client.init_from_obj({
                        client_data: client_info
                    }, 'for_event');
                    self.diagnoses = data.result.diagnoses || [];
                    self.stationary_info = data.result.stationary_info;

                    var p = data.result.payment;
                    self.payment = {
                        local_contract: (p && p.local_contract) ? p.local_contract : null,
                        payments: new WMEventPaymentList(p ? p.payments : [])
                    };
                    self.services = data.result.services && data.result.services.map(function(service) {
                        return new WMEventServiceGroup(service, self.payment.payments);
                    }) || [];
                    self.is_closed = self.closed();
                });
            };

            WMEvent.prototype.save = function(close_event) {
                var self = this;
                var deferred = $q.defer();
                $http.post(url_event_save, {
                    event: this.info,
                    diagnoses: this.diagnoses,
                    payment: this.payment,
                    services: this.services,
                    ticket_id: this.ticket_id,
                    close_event: close_event
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
    factory('WMEventServiceGroup', ['$rootScope', 'WMEventServices', 'PrintingService',
        function($rootScope, WMEventServices, PrintingService) {
            var WMSimpleAction = function (action, service_group) {
                var self = this;
                if (!action) {
                    action = {
                        action_id: null,
                        account: null,
                        amount: 1,
                        beg_date: null,
                        end_date: null,
                        status: null,
                        coord_date: null,
                        coord_person: null,
                        sum: service_group.price,
                        assigned: service_group.all_assigned !== false ?
                            service_group.all_assigned :
                            service_group.assignable.map(function (prop) {
                                return prop[0];
                            }),
                        planned_end_date: null
                    };
                    WMEventServices.get_action_ped(service_group.at_id).then(function (ped) {
                        self.planned_end_date = ped;
                    });
                }
                angular.extend(this, action);
                this.planned_end_date = aux.safe_date(this.planned_end_date);
                this._is_paid_for = undefined;
            };
            WMSimpleAction.prototype.is_paid_for = function () {
                return this._is_paid_for;
            };
            WMSimpleAction.prototype.is_coordinated = function () {
                return Boolean(this.coord_person && this.coord_person.id && this.coord_date);
            };
            WMSimpleAction.prototype.is_closed = function () {
                return this.status === 2;
            };

            var WMEventServiceGroup = function(service_data, payments) {
                if (service_data === undefined) {
                    service_data = {
                        at_id: null,
                        service_id: undefined,
                        code: null,
                        name: null,
                        at_code: null,
                        at_name: null,
                        actions: [],
                        price: undefined,
                        is_lab: null,
                        print_context: null,
                        assignable: [], // info list of assignable properties
                        all_assigned: [], // [] - all have same assignments, False - have different assignments
                        all_planned_end_date: null // date - all have same dates, False - have different dates
                    };
                }
                this.all_actions_closed = undefined;
                this.total_sum = undefined;
                this.account_all = undefined; // false - none, true - all, null - some
                this.coord_all = undefined;
                this.fully_paid = undefined;
                this.partially_paid = undefined;
                this.paid_count = undefined;
                this.coord_count = undefined;
                this.print_services = [];

                this.initialize(service_data, payments);
            };

            WMEventServiceGroup.prototype.initialize = function (service_data, payments) {
                var self = this;
                angular.extend(this, service_data);
                if (this.all_planned_end_date !== false) {
                    this.all_planned_end_date = aux.safe_date(this.all_planned_end_date);
                }
                this.actions = this.actions.map(function (act) {
                    return new WMSimpleAction(act, self);
                });
                this.all_actions_closed = this.actions.every(function (act) {
                    return act.is_closed();
                });
                this.actions.forEach(function (act) {
                    var ps = new PrintingService("action");
                    self.print_services.push(ps);
                });

                // many much watches
                $rootScope.$watch(function () {
                    return self.total_amount;
                }, function (n, o) {
                    self.rearrange_actions();
                    self.recalculate_sum();
                });
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.amount;
                    });
                }, function (n, o) {
                    if (n !== o) {
                        self.recalculate_amount();
                    }
                }, true);
                $rootScope.$watch(function () {
                    return self.account_all;
                }, function (n, o) {
                    if (o === undefined || n === null) {
                        return;
                    }
                    self.actions.forEach(function (act) {
                        if (act.account !== n && !act.is_closed()) {
                            act.account = n;
                            if (n) {
                                self.payments.add_charge(act);
                            } else {
                                self.payments.remove_charge(act);
                            }
                        }
                    });
                });
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.account;
                    });
                }, function (n, o) {
                    var total_count = n.length,
                        account_count = 0;
                    n.forEach(function (acc) {
                        if (acc) {
                            account_count += 1;
                        }
                    });
                    self.account_all = (account_count === total_count) ? true :
                        (account_count === 0) ? false : null;
                }, true);
                $rootScope.$watch(function () {
                    return self.coord_all;
                }, function (n, o) {
                    if (n === undefined || n === null) {
                        return;
                    }
                    self.actions.forEach(function (act) {
                        if (!act.is_coordinated() && !act.is_closed()) {
                            WMEventServices.coordinate(act, !n);
                        }
                    });
                }, true);
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return act.coord_person ? act.coord_person.id : null;
                    });
                }, function (n, o) {
                    var total_count = n.length;
                    self.refresh_coord_info();
                    self.coord_all = (total_count === self.coord_count) ? true :
                        (self.coord_count === 0) ? false : null;
                }, true);
                $rootScope.$watch(function () {
                    return self.actions.map(function (act) {
                        return [act.assigned, act.planned_end_date];
                    });
                }, function (n, o) {
                    var asgn_list = n.map(function (data) {
                            return data[0];
                        }),
                        ref_asgn_list = asgn_list[0],
                        ped = n.map(function (data) {
                            return data[1];
                        }),
                        ref_ped = ped[0],
                        all_same_asgn = asgn_list.every(function (asgn_list) {
                            return angular.equals(asgn_list, ref_asgn_list);
                        }),
                        all_same_ped = ped.every(function (ped) {
                            return moment(ped).isSame(ref_ped);
                        });
                    self.all_assigned = all_same_asgn && ref_asgn_list;
                    self.all_planned_end_date = all_same_ped && ref_ped;
                }, true);

                this.recalculate_amount();

                if (this.price && payments) {
                    this.payments = payments;
                    this.actions.forEach(function (act) {
                        if (act.account) {
                            self.payments.add_charge(act);
                        }
                    });
                    $rootScope.$watch(function () {
                        return self.payments.charges;
                    }, function (n, o) {
                        self.refresh_payments();
                    }, true);
                }
            };

            WMEventServiceGroup.prototype.is_new = function () {
                return this.actions.some(function (a) {
                    return !a.action_id;
                });
            };

            WMEventServiceGroup.prototype.check_payment = function (type) {
                if (!arguments.length) {
                    type = 'full';
                }
                if (type === 'full') {
                    return this.actions.every(function (a) {
                        return a.is_paid_for();
                    });
                } else if (type === 'partial') {
                    return this.actions.some(function (a) {
                        return a.is_paid_for();
                    });
                }
                return false;
            };

            WMEventServiceGroup.prototype.check_coord = function (type) {
                if (!arguments.length) {
                    type = 'full';
                }
                if (type === 'full') {
                    return this.actions.every(function (a) {
                        return a.is_coordinated();
                    });
                } else if (type === 'partial') {
                    return this.actions.some(function (a) {
                        return a.is_coordinated();
                    });
                }
                return false;
            };

            WMEventServiceGroup.prototype.rearrange_actions = function () {
                var self = this,
                    total_amount = this.total_amount,
                    actions_amount = this.actions.reduce(function (sum, cur_act) {
                        return sum + cur_act.amount;
                    }, 0);
                if (actions_amount < total_amount) {
                    for (var i = 0; i < total_amount - actions_amount; i++) {
                        this.actions.push(new WMSimpleAction(null, self));
                    }
                } else if (total_amount < actions_amount) {
                    var i = actions_amount - total_amount,
                        idx = this.actions.length - 1,
                        cur_act;
                    while (i--) {
                        cur_act = this.actions[idx];
                        if (cur_act.action_id || cur_act.account) {
                            break;
                        }
                        if (cur_act.amount > 1) {
                            cur_act.amount -= 1;
                        } else {
                            this.actions.splice(idx, 1);
                            idx--;
                        }
                    }
                }
            };

            WMEventServiceGroup.prototype.recalculate_amount = function () {
                this.total_amount = this.actions.reduce(function (sum, cur_act) {
                    return sum + cur_act.amount;
                }, 0);
            };

            WMEventServiceGroup.prototype.recalculate_sum = function () {
                var self = this;
                this.actions.forEach(function (act) {
                    act.sum = act.amount * self.price;
                });
                this.total_sum = this.actions.reduce(function (sum, cur_act) {
                    return sum + cur_act.sum;
                }, 0);
            };

            WMEventServiceGroup.prototype.refresh_payments = function() {
                var total_count = this.total_amount,
                    paid_actions = this.payments.charges.filter(function (ch) {
                        return ch.suffice;
                    }).map(function (ch) {
                        return ch.action;
                    }),
                    paid_count = 0;

                this.actions.forEach(function (act) {
                    if (paid_actions.has(act)) {
                        act._is_paid_for = true;
                        paid_count += act.amount;
                    } else {
                        act._is_paid_for = false;
                    }
                });

                this.paid_count = paid_count;
                this.fully_paid = total_count === paid_count;
                this.partially_paid = paid_count > 0 && paid_count < total_count;
            };

            WMEventServiceGroup.prototype.refresh_coord_info = function () {
                var total_count = this.total_amount,
                    coordinated_count = this.actions.reduce(function (sum, cur_act) {
                        return sum + (cur_act.is_coordinated() ? cur_act.amount : 0);
                    }, 0);
                this.coord_count = coordinated_count;
                this.fully_coord = total_count === coordinated_count;
                this.partially_coord = coordinated_count > 0 && coordinated_count < total_count;
            };

            return WMEventServiceGroup;
        }
    ]).
    factory('WMEventPaymentList', [
        function() {
            var WMEventPaymentList = function (payment_data) {
                this.payments = payment_data;
                this.charges = [];
                this.total_in = null;
                this.total_out = null;
                this.diff = null;
                this.refresh();
            };
            WMEventPaymentList.prototype.add_charge = function (action) {
                this.charges.push({
                    action: action
                });
                this.refresh();
            };
            WMEventPaymentList.prototype.remove_charge = function (action) {
                var idx = -1,
                    i,
                    cur_action;
                for (i = 0; i < this.charges.length; i++) {
                    cur_action = this.charges[i].action;
                    if (cur_action === action) {
                        idx = i;
                        break;
                    }
                }
                if (idx !== -1) {
                    this.charges.splice(idx, 1);
                    this.refresh();
                }
            };
            WMEventPaymentList.prototype.set_payments = function (payments) {
                this.payments = payments;
                this.refresh();
            };
            WMEventPaymentList.prototype.refresh = function () {
                var bank = this.total_in;
                this.charges.sort(function (a, b) {
                    var a = a.action,
                        b = b.action;
                    if (a.action_id) {
                        if (b.action_id) {
                            return a.beg_date > b.beg_date ?
                                1 :
                                (a.beg_date === b.beg_date ? (a.action_id > b.action_id ? 1 : -1) : -1);
                        }
                    } else {
                        return -1;
                    }
                    return -1;
                }).forEach(function (ch) {
                    ch.suffice = bank >= ch.action.sum;
                    bank -= ch.action.sum;
                });

                this.total_in = this.payments.reduce(function (sum, cur_pay) {
                    return sum + cur_pay.sum;
                }, 0);

                this.total_out = this.charges.reduce(function (sum, cur_ch) {
                    return sum + cur_ch.action.sum;
                }, 0);

                this.diff = this.total_out - this.total_in;
            };
            return WMEventPaymentList;
        }
    ]);