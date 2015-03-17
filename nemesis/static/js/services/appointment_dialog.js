/**
 * Created by mmalkov on 11.07.14.
 */
angular.module('WebMis20.services.dialogs', ['WebMis20.services', 'ui.bootstrap'])
.service('WMAppointmentDialog', ['$modal', 'WMAppointment', 'RefBookService', function ($modal, WMAppointment, RefBookService) {
    return {
        cancel: function (ticket, person, client_id) {
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Отменить запись на приём?</h4>\
                    </div>\
                    <div class="modal-body" ng-if="!error">\
                        Отменить <span ng-if="ticket.attendance_type.code == \'CITO\'">экстренную</span>\
                        <span ng-if="ticket.attendance_type.code == \'extra\'">сверхплановую</span>\
                            запись на приём к <strong>[[ person.name ]]</strong> ([[ person.speciality.name ]])\
                        <span ng-if="ticket.attendance_type.code == \'planned\'">на <strong>[[ ticket.begDateTime | asMomentFormat:\'HH:mm DD.MM.YY\' ]]</strong></span>?\
                    </div>\
                    <div class="modal-body" ng-if="error">\
                        [[ error.text ]]\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-success" ng-click="accept()" ng-disabled="error">Отменить запись</button>\
                        <button type="button" class="btn btn-danger" ng-click="cancel()">Не отменять запись</button>\
                    </div>',
                controller: function ($scope, $http, $modalInstance) {
                    $scope.ticket = ticket;
                    $scope.person = person;
                    $scope.error = null;
                    $scope.accept = function () {
                        WMAppointment.cancel(ticket, client_id).success(function (data) {
                            $modalInstance.close(data);
                        }).error(function () {
                            $scope.error = {
                                text: 'Ошибка при отмене записи на приём'
                            }
                        });
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                }
            });
        },
        make: function (ticket, person, client_id, client_name) {
            var size = client_id ? '' : 'lg';
            return $modal.open({
                template:
                    '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
                        <button type="button" class="close" ng-click="cancel()">&times;</button>\
                        <h4 class="modal-title" id="myModalLabel">Записать на приём?</h4>\
                    </div>\
                    <div class="modal-body modal-scrollable">\
                        <div id="page1" ng-show="page === 0">\
                            <wm-search-client client-id="model.client.client_id" query="client_query"\
                                on-select="select_client(selected_client)"></wm-search-client>\
                        </div>\
                        <div id="page2" ng-show="page === 1">\
                            <dl class="dl-horizontal novmargin">\
                              <dt>Врач:</dt><dd>[[ person.name ]] ([[ person.speciality.name ]])</dd>\
                              <dt>Время приёма:</dt>\
                              <dd>\
                                <span ng-if="ticket.attendance_type.code == \'planned\'">[[ ticket.begDateTime | asMomentFormat:\'HH:mm DD.MM.YY\' ]]</span>\
                                <span ng-if="ticket.attendance_type.code == \'CITO\'"><strong>экстренно</strong></span>\
                                <span ng-if="ticket.attendance_type.code == \'extra\'"><strong>сверх плана</strong></span>\
                              </dd>\
                              <dt>Тип записи:</dt>\
                              <dd class="marginal"><select class="form-control" ng-model="model.appointment_type"\
                                      ng-options="at as at.name for at in rbAppointmentType.objects \
                                        | filter:flt_appointment_type() track by at.id"\
                                      ng-change="on_at_change()"></select></dd>\
                              <dt ng-if="show_assoc_events()">Приём в рамках ИБ:</dt>\
                              <dd ng-if="show_assoc_events()">\
                                  <span ng-if="!event_list.length">Нет открытой истории болезни</span>\
                                  <ul class="list-group">\
                                    <li class="list-group-item" ng-repeat="event in event_list">\
                                        <label for="event[[$index]]" class="label-no-bold">\
                                            <input type="radio" id="event[[$index]]" ng-model="model.associated_event_id" ng-value="event.id">\
                                            [[event.text_description]]\
                                        </label>\
                                    </li>\
                                  </ul>\
                              </dd>\
                              <dt ng-show="client_name">Пациент:</dt><dd ng-show="client_name">[[ client_name ]]</dd>\
                            </dl>\
                        </div>\
                    </div>\
                    <div class="modal-footer">\
                        <button type="button" class="btn btn-primary" ng-click="next_page()" ng-show="chose_client_mode && page === 0" ng-disabled="!model.client.client_id">Далее</button>\
                        <button type="button" class="btn btn-default" ng-click="prev_page()" ng-show="chose_client_mode && page === 1">Назад</button>\
                        <button type="button" class="btn btn-success" ng-click="accept()" ng-show="page === 1">Записать</button>\
                        <button type="button" class="btn btn-danger" ng-click="cancel()">Не записывать</button>\
                    </div>',
                controller: function ($scope, $http, $modalInstance) {
                    $scope.rbAppointmentType = new RefBookService.get('rbAppointmentType');
                    $scope.ticket = ticket;
                    $scope.person = person;
                    $scope.model = {
                        client: {
                            client_id: client_id
                        },
                        appointment_type: null,
                        associated_event_id: null
                    };
                    $scope.client_name = client_name;
                    $scope.client_query = '';
                    $scope.rbAppointmentType.get_by_code_async('amb').then(function (at) {
                        $scope.model.appointment_type = at;
                    });
                    $scope.event_list = [];
                    $scope.chose_client_mode = !client_id;
                    $scope.page = client_id ? 1 : 0;
                    var assoc_event_required_codes = ['hospital', 'polyclinic'];

                    $scope.load_event_info = function (client_id) {
                        if (!client_id) {
                            return;
                        }
                        $http.get(url_api_event_stationary_open_get, {
                            params: {
                                client_id: client_id
                            }
                        }).success(function (data) {
                            $scope.event_list = data.result;
                        });
                    };
                    $scope.load_event_info($scope.model.client.client_id);

                    $scope.show_assoc_events = function () {
                        return $scope.model.appointment_type && assoc_event_required_codes.has($scope.model.appointment_type.code);
                    };
                    $scope.flt_appointment_type = function () {
                        return function (appointment_type) {
                            return $scope.event_list.length ? true : !assoc_event_required_codes.has(appointment_type.code);
                        }
                    };
                    $scope.on_at_change = function () {
                        if (!assoc_event_required_codes.has($scope.model.appointment_type.code)) {
                            $scope.model.associated_event_id = null;
                        }
                    };
                    $scope.select_client = function (selected_client) {
                        $scope.client_name = selected_client.info.full_name;
                        $scope.load_event_info(selected_client.info.id);
                    };
                    $scope.next_page = function () {
                        $scope.page++;
                    };
                    $scope.prev_page = function () {
                        $scope.page--;
                    };
                    $scope.accept = function () {
                        WMAppointment.make(ticket,
                            $scope.model.client.client_id,
                            $scope.model.appointment_type.id,
                            $scope.model.associated_event_id
                        ).success(function (data) {
                            $modalInstance.close(data);
                        }).error(function () {
                            $scope.error = {
                                text: 'Ошибка при записи на приём'
                            };
                        });
                    };
                    $scope.cancel = function () {
                        $modalInstance.dismiss('cancel');
                    };
                },
                size: size
            });
        }
    }
}]);
