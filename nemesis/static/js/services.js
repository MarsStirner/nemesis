'use strict';

angular.module('WebMis20.services', []).
    service('WMAppointment', ['$http', function ($http) {
        return {
            make: function (ticket, client_id, appointment_type_id, associated_event_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    appointment_type_id: appointment_type_id,
                    event_id: associated_event_id
                });
            },
            cancel: function (ticket, client_id) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    delete: true
                });
            },
            change_notes: function (ticket_client_id, notes) {
                return $http.post(url_schedule_api_appointment, {
                    client_id: client_id,
                    ticket_id: ticket.id,
                    note: notes
                });
            }
        }
    }]).
    service('AgeSex', [function() {
        return {
            sex_acceptable: function (client, sex) {
                return ! (sex && sex !== client.sex_raw);
            },
            age_acceptable: function (client, selector) {
                return ! (
                    selector[0] != 0 && client.age_tuple[selector[0] - 1] < selector[1] ||
                    selector[2] != 0 && client.age_tuple[selector[2] - 1] > selector[3]
                );
            }
        }
    }]).
    service('WMWindowSync', ['$window', '$rootScope', '$interval', function ($window, $rootScope, $interval) {
        return {
            openTab: function (url, onCloseCallback) {
                var interval,
                    clearInterval = function() {
                        $interval.cancel(interval);
                        interval = undefined;
                    };
                var w = $window.open(url);
                interval = $interval(function () {
                    if (w.closed) {
                        (onCloseCallback || angular.noop)();
                        clearInterval();
                        w = undefined;
                    }
                }, 500);
            }
        }
    }]);