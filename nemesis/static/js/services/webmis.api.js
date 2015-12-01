'use strict';

WebMis20
.service('WebMisApi', [
    '$q', 'WMConfig', 'NotificationService', '$window', 'ApiCalls',
    function ($q, WMConfig, NotificationService, $window, ApiCalls) {
    var self = this;
    var wrapper = ApiCalls.wrapper;
    this.contract = {
        get: function (contract_id) {
            var url = WMConfig.url.api_contract_get;
            if (contract_id) {
                url += contract_id;
            } else {
                url += '?new=true';
            }
            return wrapper('GET', url);
        },
        get_list: function (args) {
            return wrapper('GET', WMConfig.url.api_contract_list, args);
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
            return wrapper('POST', WMConfig.url.api_service_search, {}, args);
        },
        save_service_list: function (args) {
            return wrapper('POST', WMConfig.url.api_service_list_save, {}, args);
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
        }
    };
}]);