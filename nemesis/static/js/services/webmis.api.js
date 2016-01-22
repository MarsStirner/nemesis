'use strict';

WebMis20
.service('WebMisApi', [
    '$q', 'WMConfig', 'NotificationService', '$window', 'ApiCalls',
    function ($q, WMConfig, NotificationService, $window, ApiCalls) {
    var self = this;
    var wrapper = ApiCalls.wrapper;
    this.contract = {
        get: function (contract_id, args) {
            var url = WMConfig.url.api_contract_get;
            if (contract_id) {
                url += contract_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        },
        get_list: function (args) {
            return wrapper('POST', WMConfig.url.api_contract_list, {}, args);
        },
        save: function (contract_id, data) {
            var url = WMConfig.url.api_contract_save,
                method;
            if (contract_id) {
                url += contract_id;
                method = 'POST';
            } else {
                method = 'PUT';
            }
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
            return wrapper('DELETE', WMConfig.url.api_contract_delete + contract_id);
        },
        get_available: function (args) {
            return wrapper('GET', WMConfig.url.api_contract_get_available, args);
        }
    };
    this.contragent = {
        get_list: function (args) {
            return wrapper('POST', WMConfig.url.api_contragent_list, {}, args);
        },
        search_payer: function (args) {
            return wrapper('POST', WMConfig.url.api_contragent_search_payer, {}, args);
        },
        get_payer: function (payer_id) {
            return wrapper('GET', WMConfig.url.api_contragent_payer_get + payer_id);
        }
    };
    this.contingent = {
        get: function (contingent_id, args) {
            var url = WMConfig.url.api_contingent_get;
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
            return wrapper('POST', WMConfig.url.api_pricelist_list, {}, args);
        }
    };
    this.service = {
        search_mis_action_services: function (args) {
            return wrapper('GET', WMConfig.url.api_service_search, args);
        },
        get: function (service_id, args) {
            var url = WMConfig.url.api_service_get;
            if (service_id) {
                url += service_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url, args);
        },
        save_service_list: function (args) {
            return wrapper('POST', WMConfig.url.api_service_list_save, {}, args);
        },
        get_list: function (event_id) {
            return wrapper('GET', WMConfig.url.api_service_list + event_id);
        },
        del: function (service_id) {
            return wrapper('DELETE', WMConfig.url.api_service_delete + service_id);
        },
        calc_sum: function (args) {
            return wrapper('POST', WMConfig.url.api_service_calc_sum, {}, args);
        },
        refreshServiceSubservices: function (service) {
            return wrapper('POST', WMConfig.url.api_service_refresh_subservices, {}, service);
        }
    };
    this.service_discount = {
        get_list: function (args) {
            return wrapper('GET', WMConfig.url.api_service_discount_list, undefined, undefined, {
                cache: true
            });
        }
    };
    this.invoice = {
        get: function (invoice_id, args) {
            var url = WMConfig.url.api_invoice_get;
            if (invoice_id) {
                url += invoice_id;
            } else {
                url += '?new=true';
            }
            if (args) {
                return wrapper('POST', url, undefined, args);
            } else {
                return wrapper('GET', url, args);
            }
        },
        save: function (invoice_id, data) {
            var url = WMConfig.url.api_invoice_save,
                method;
            if (invoice_id) {
                url += invoice_id;
                method = 'POST';
            } else {
                method = 'PUT';
            }
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
            return wrapper('DELETE', WMConfig.url.api_invoice_delete + invoice_id);
        },
        search: function (args) {
            return wrapper('POST', WMConfig.url.api_invoice_search, {}, args);
        },
        calc_sum: function (invoice_id, data) {
            var url = WMConfig.url.api_invoice_calc_sum;
            if (invoice_id) {
                url += invoice_id;
            }
            return wrapper('POST', url, {}, data);
        }
    };
    this.finance_trx = {
        get_new: function (args) {
            var url = WMConfig.url.api_finance_transaction_get;
            url += '?new=true';
            return wrapper('GET', url, args);
        },
        make_trx: function (trx_type_code, data) {
            var url = '{0}{1}/'.format(WMConfig.url.api_finance_transaction_make, trx_type_code);
            return wrapper('PUT', url, {}, data)
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
            var url = WMConfig.url.api_finance_transaction_invoice_get;
            url += '?new=true';
            return wrapper('GET', url, args);
        },
        make_invoice_trx: function (trx_type_code, data) {
            var url = '{0}{1}/'.format(WMConfig.url.api_finance_transaction_invoice_make, trx_type_code);
            return wrapper('PUT', url, {}, data)
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
}]);