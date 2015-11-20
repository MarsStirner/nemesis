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
                .then(function (action) {
                    NotificationService.notify(
                        200,
                        'Успешно сохранено',
                        'success',
                        5000
                    );
                    return action;
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
    this.contragent = {
        get_list: function (args) {
            return wrapper('POST', WMConfig.url.api_contragent_list, {}, args);
        }
    };
    //this.measure = {
    //    get_chart: function (event_id) {
    //        return wrapper('GET', Config.url.api_chart_measure_list + event_id)
    //    },
    //    get_by_event: function (event_id, query) {
    //        return wrapper('POST', Config.url.api_measure_list + event_id, undefined, query)
    //    },
    //    regenerate: function (action_id) {
    //        return wrapper('GET', Config.url.api_event_measure_generate + action_id)
    //    },
    //    get: function (event_measure_id) {
    //        return wrapper('GET', Config.url.api_event_measure_get + event_measure_id);
    //    },
    //    remove: function (action_id) {
    //        return wrapper('POST', Config.url.api_event_measure_remove + action_id)
    //    },
    //    cancel: function (event_measure_id) {
    //        return wrapper('POST', Config.url.api_event_measure_cancel + event_measure_id);
    //    },
    //    get_appointment: function (event_measure_id, appointment_id) {
    //        var url = Config.url.api_event_measure_appointment_get.format(event_measure_id);
    //        if (appointment_id) {
    //            url += appointment_id;
    //        } else {
    //            url += '?new=true';
    //        }
    //        return wrapper('GET', url);
    //    },
    //    save_appointment: function (event_measure_id, appointment_id, data) {
    //        var url = Config.url.api_event_measure_appointment_save.format(event_measure_id),
    //            method;
    //        if (appointment_id) {
    //            url += appointment_id;
    //            method = 'POST';
    //        } else {
    //            method = 'PUT';
    //        }
    //        return wrapper(method, url, {}, data)
    //            .then(function (action) {
    //                NotificationService.notify(
    //                    200,
    //                    'Успешно сохранено',
    //                    'success',
    //                    5000
    //                );
    //                return action;
    //            }, function (result) {
    //                NotificationService.notify(
    //                    500,
    //                    'Ошибка сохранения, свяжитесь с администратором',
    //                    'danger'
    //                );
    //                return result;
    //            });
    //    },
    //    get_em_result: function (event_measure_id, em_result_id) {
    //        var url = Config.url.api_event_measure_result_get.format(event_measure_id);
    //        if (em_result_id) {
    //            url += em_result_id;
    //        } else {
    //            url += '?new=true';
    //        }
    //        return wrapper('GET', url);
    //    },
    //    save_em_result: function (event_measure_id, em_result_id, data) {
    //        var url = Config.url.api_event_measure_result_save.format(event_measure_id),
    //            method;
    //        if (em_result_id) {
    //            url += em_result_id;
    //            method = 'POST';
    //        } else {
    //            method = 'PUT';
    //        }
    //        return wrapper(method, url, {}, data)
    //            .then(function (action) {
    //                NotificationService.notify(
    //                    200,
    //                    'Успешно сохранено',
    //                    'success',
    //                    5000
    //                );
    //                return action;
    //            }, function (result) {
    //                NotificationService.notify(
    //                    500,
    //                    'Ошибка сохранения, свяжитесь с администратором',
    //                    'danger'
    //                );
    //                return result;
    //            });
    //    }
    //};
}]);