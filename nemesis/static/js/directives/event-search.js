'use strict';

angular.module('WebMis20.directives').
    directive('wmSearchEvent', ['$q', '$http', 'PrintingService', function ($q, $http, PrintingService) {
        return {
            restrict: 'E',
            scope: {
                event_id: '=eventId',
                query: '=',
                onSelectCallback: '&onSelect'
            },
            controller: function ($scope) {
                $scope.clear_results = function () {
                    $scope.results = null;
                    $scope.event_id = null;
                    $scope.prints = {};
                };
                $scope.query_clear = function () {
                    $scope.query = '';
                    $scope.clear_results();
                };
                var canceler = $q.defer();
                $scope.perform_search = function () {
                    canceler.resolve();
                    canceler = $q.defer();
                    if ($scope.query) {
                        $http.get(
                            url_event_search, {
                                params: {
                                    q: $scope.query
                                },
                                timeout: canceler.promise
                            }
                        ).success(function (data) {
                            $scope.results = data.result;
                            $scope.prints = {};
                            angular.forEach($scope.results, function (event) {
                                $scope.prints[event.id] = new PrintingService('event');
                            });
                        });
                    }
                };
                $scope.get_client_url = function (client_id) {
                    return url_for_patien_info_full + '?client_id=' + client_id;
                };
                $scope.get_event_url = function (event_id) {
                    return url_for_event_html_event_info + '?event_id=' + event_id;
                };
                $scope.onEventSelect = function (selected_record) {
                    $scope.event_id = selected_record.id;
                    ($scope.onSelectCallback || angular.noop)({
                        selected_event: selected_record
                    });
                };
                $scope.ps_resolve = function (event_id) {
                    return {
                        event_id: event_id
                    }
                };
            },
            link: function (scope, element, attrs) {
                scope.results = null;
            },
            template: '\
<form class="form-horizontal marginal" role="form">\
    <div class="input-group">\
        <input id="search" class="form-control" type="text" ng-model="query" autocomplete="off"\
               ng-change="clear_results()"\
               placeholder="Поиск по коду пациента, ФИО, дате рождения или номеру обращения">\
        <span class="input-group-btn">\
            <button class="btn btn-success" ng-click="perform_search()"><span class="glyphicon glyphicon-search"></span> Найти</button>\
        </span>\
    </div>\
</form>\
<div class="panel panel-default" ng-class="{\'panel-danger\': results.length === 0, \'panel-success\': results.length > 0}">\
    <div class="panel-heading">\
        <div class="row">\
            <div class="col-sm-8">\
                <span ng-if="results.length > 0" class="lead">Результаты поиска</span>\
                <span ng-if="results.length === 0 && query">Обращений не найдено</span>\
            </div>\
        </div>\
    </div>\
    <table id="result_tbl" class="table table-condensed table-clickable table-hover table-striped" ng-if="results.length > 0">\
        <thead>\
        <tr>\
            <th width="1%">№ обращения</th>\
            <th width="1%">Договор</th>\
            <th width="10%">Пациент</th>\
            <th width="1%">Дата рождения</th>\
            <th width="1%">Пол</th>\
            <th width="10%">Врач</th>\
            <th width="1%">Назначен</th>\
            <th width="1%">Выполнен</th>\
            <th width="10%">Тип обащения</th>\
            <th width="1%">Акт</th>\
            <th width="1%"></th>\
        </tr>\
        </thead>\
        <tbody>\
        <tr ng-repeat="event in results" style="cursor: pointer"\
            ng-class="{\'bg-info text-info\': event.id === event_id}">\
            <td ng-bind-html="event.external_id | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.contract.number_contract | highlight: query" class="nowrap" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.client.full_name | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.client.birth_date | asDate | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.client.sex.name" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.exec_person.full_name | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.beg_date_date | asDate | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.end_date_date | asDate | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.event_type.name | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-bind-html="event.contract.coord_text | highlight: query" ng-click="onEventSelect(event)"></td>\
            <td ng-class="{\'bg-muted\': event.id !== event_id}" class="cursor-default nowrap">\
                <a ng-href="[[get_client_url(event.client.id)]]" target="_blank" class="btn btn-default"\
                    title="Открыть карту пациента"><span class="fa fa-user"></span>\
                </a>\
                <a ng-href="[[get_event_url(event.id)]]" target="_blank" class="btn btn-default"\
                    title="Открыть обращение пациента"><span class="fa fa-list-alt"></span>\
                </a>\
                <ui-print-button ps="prints[event.id]" resolve="ps_resolve(event.id)"\
                    lazy-load-context="[[event.event_type.print_context]]"></ui-print-button>\
            </td>\
        </tr>\
        </tbody>\
    </table>\
</div>'
        };
    }]);