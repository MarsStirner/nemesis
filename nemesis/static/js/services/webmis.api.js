'use strict';

WebMis20
.service('WebMisApi', [
    '$q', 'WMConfig', 'NotificationService', '$window', 'ApiCalls',
    function ($q, WMConfig, NotificationService, $window, ApiCalls) {
    var self = this;
    var wrapper = ApiCalls.wrapper;
    this.contract = {
        get: function (contract_id, args) {
            var url = WMConfig.url.accounting.api_contract_get;
            if (contract_id) {
                url += contract_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        },
        get_list: function (args) {
            return wrapper('POST', WMConfig.url.accounting.api_contract_list, {}, args);
        },
        save: function (contract_id, data) {
            var url = WMConfig.url.accounting.api_contract_save,
                method;
            if (contract_id) {
                url += contract_id;
            }
            method = 'POST';
            return wrapper(method, url, {}, data)
                .then(function (contract) {
                    NotificationService.notify(
                        200,
                        'Успешно сохранено',
                        'success',
                        5000
                    );
                    return contract;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return $q.reject(result);
                });
        },
        del: function (contract_id) {
            return wrapper('DELETE', WMConfig.url.accounting.api_contract_delete + contract_id);
        },
        get_available: function (args) {
            return wrapper('GET', WMConfig.url.accounting.api_contract_get_available, args);
        }
    };
    this.contragent = {
        get_list: function (args) {
            return wrapper('POST', WMConfig.url.accounting.api_contragent_list, {}, args);
        },
        search_payer: function (args) {
            return wrapper('POST', WMConfig.url.accounting.api_contragent_search_payer, {}, args);
        },
        get_payer: function (payer_id) {
            return wrapper('GET', WMConfig.url.accounting.api_contragent_payer_get + payer_id);
        },
        get_client: function (client_id) {
            return wrapper('GET', WMConfig.url.accounting.api_contragent_client_get + client_id);
        },
        check_duplicate: function (data) {
            return wrapper('POST', WMConfig.url.accounting.api_contragent_check_duplicate, {}, data);
        }
    };
    this.contingent = {
        get: function (contingent_id, args) {
            var url = WMConfig.url.accounting.api_contingent_get;
            if (contingent_id) {
                url += contingent_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        }
    };
    this.pricelist = {
        get_list: function (args) {
            return wrapper('POST', WMConfig.url.accounting.api_pricelist_list, {}, args);
        }
    };
    this.service = {
        search_mis_action_services: function (args) {
            return wrapper('GET', WMConfig.url.accounting.api_service_search, args);
        },
        get: function (service_id, args) {
            var url = WMConfig.url.accounting.api_service_get;
            if (service_id) {
                url += service_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        },
        save_service_list: function (data, args) {
            return wrapper('POST', WMConfig.url.accounting.api_service_list_save, args, data);
        },
        get_list: function (event_id, args) {
            return wrapper('GET', WMConfig.url.accounting.api_service_list + event_id, args);
        },
        del: function (service_id) {
            return wrapper('DELETE', WMConfig.url.accounting.api_service_delete + service_id);
        },
        calc_sum: function (args) {
            return wrapper('POST', WMConfig.url.accounting.api_service_calc_sum, {}, args);
        },
        refreshServiceSubservices: function (service) {
            return wrapper('POST', WMConfig.url.accounting.api_service_refresh_subservices, {}, service);
        },
        get_service_at_price: function (contract_id) {
            return wrapper('GET', WMConfig.url.accounting.api_service_at_price_get + contract_id);
        }
    };
    this.service_discount = {
        get_list: function (args) {
            return wrapper('GET', WMConfig.url.accounting.api_service_discount_list, undefined, undefined, {
                cache: true
            });
        }
    };
    this.invoice = {
        get: function (invoice_id, args) {
            var url = WMConfig.url.accounting.api_invoice_get;
            if (invoice_id) {
                url += invoice_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        },
        save: function (invoice_id, data) {
            var url = WMConfig.url.accounting.api_invoice_save,
                method;
            if (invoice_id) {
                url += invoice_id;
            }
            method = 'POST';
            return wrapper(method, url, {}, data)
                .then(function (invoice) {
                    NotificationService.notify(
                        200,
                        'Успешно сохранено',
                        'success',
                        5000
                    );
                    return invoice;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return $q.reject(result);
                });
        },
        del: function (invoice_id) {
            return wrapper('DELETE', WMConfig.url.accounting.api_invoice_delete + invoice_id);
        },
        search: function (args) {
            return wrapper('POST', WMConfig.url.accounting.api_invoice_search, {}, args);
        },
        calc_sum: function (invoice_id, data) {
            var url = WMConfig.url.accounting.api_invoice_calc_sum;
            if (invoice_id) {
                url += invoice_id;
            }
            return wrapper('POST', url, {}, data);
        }
    };
    this.refund = {
        get: function (invoice_id) {
            return wrapper('GET', WMConfig.url.accounting.api_invoice_refund_get.format(invoice_id));
        },
        save: function (invoice_id, data) {
            return wrapper('POST', WMConfig.url.accounting.api_invoice_refund_save.format(invoice_id), {}, data);
        },
        del: function (invoice_id) {
            return wrapper('DELETE', WMConfig.url.accounting.api_invoice_refund_delete.format(invoice_id));
        },
        process: function (invoice_id, data) {
            return wrapper('POST', WMConfig.url.accounting.api_invoice_refund_process.format(invoice_id), {}, data)
                .then(function (payer) {
                    NotificationService.notify(
                        200,
                        'Возврат проведён',
                        'success',
                        5000
                    );
                    return payer;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return $q.reject(result);
                });
        }
    };
    this.finance_trx = {
        get_new: function (args) {
            var url = WMConfig.url.accounting.api_finance_transaction_get;
            url += '?new=true';
            return wrapper('GET', url, args);
        },
        make_trx: function (trx_type_code, data) {
            var url = '{0}{1}/'.format(WMConfig.url.accounting.api_finance_transaction_make, trx_type_code);
            return wrapper('POST', url, {}, data)
                .then(function (payer) {
                    NotificationService.notify(
                        200,
                        'Транзакция сохранена',
                        'success',
                        5000
                    );
                    return payer;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return $q.reject(result);
                });
        },
        get_new_invoice_trxes: function (args) {
            var url = WMConfig.url.accounting.api_finance_transaction_invoice_get;
            url += '?new=true';
            return wrapper('GET', url, args);
        },
        make_invoice_trx: function (trx_type_code, data) {
            var url = '{0}{1}/'.format(WMConfig.url.accounting.api_finance_transaction_invoice_make, trx_type_code);
            return wrapper('POST', url, {}, data)
                .then(function (invoice) {
                    NotificationService.notify(
                        200,
                        'Транзакция сохранена',
                        'success',
                        5000
                    );
                    return invoice;
                }, function (result) {
                    NotificationService.notify(
                        500,
                        'Ошибка сохранения, свяжитесь с администратором',
                        'danger'
                    );
                    return $q.reject(result);
                });
        }
    };
    this.action = {
        search: function (data) {
            return wrapper('POST', WMConfig.url.actions.search_actions, {}, data);
        }
    }
}]);