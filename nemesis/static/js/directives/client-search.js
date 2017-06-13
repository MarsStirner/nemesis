'use strict';

angular.module('WebMis20.directives').
    directive('wmSearchClient', ['$q', 'WebMisApi', 'WMConfig', 'TimeoutCallback',
            function ($q, WebMisApi, WMConfig, TimeoutCallback) {
        return {
            restrict: 'E',
            scope: {
                client_id: '=clientId',
                query: '=',
                onSelectCallback: '&onSelect',
                getSearchApi: '&?',
                customRegisterCallback: '&?'
            },
            controller: function ($scope) {
                $scope.pager = {
                    current_page: 1,
                    max_pages: 10,
                    pages: 1,
                    items_per_page: 70,
                    total_items: 1
                };
                $scope.clear_results = function () {
                    $scope.results = null;
                    $scope.client_id = null;
                    $scope.pager.pages = 1;
                    $scope.pager.current_page = 1;
                };
                $scope.query_clear = function () {
                    $scope.query = '';
                    $scope.clear_results();
                };
                $scope.setQuery = function (text) {
                    $scope.clear_results();
                    $scope.query = text;
                };

                $scope.performSearch = function () {
                    $scope.$emit('ClientSearchChanged', {query: $scope.query});

                    if (!$scope.query) {
                        return $q.reject([]);
                    }

                    return WebMisApi.client.search({
                        q: $scope.query,
                        current_page: $scope.pager.current_page,
                        items_per_page: $scope.pager.items_per_page,
                        paginated: true
                    }).then(function (data) {
                        $scope.results = data.client_info;
                        $scope.pager.pages = data.pages;
                        $scope.pager.total_items = data.total_items;
                        return data.client_info;
                    });
                };
                var tc = new TimeoutCallback($scope.performSearch, 600);
                $scope.startSearch = function () {
                    tc.start();
                };

                $scope.registerNewClient = function () {
                    if ($scope.custom_register) {
                        $scope.customRegisterCallback();
                    } else {
                        $scope.open_new_client('new');
                    }
                };
                $scope.open_new_client = function (client_id) {
                    window.open(WMConfig.url.patients.client_html + '?client_id=' + client_id, '_blank');
                };

                $scope.onClientSelect = function (selected_record) {
                    $scope.client_id = selected_record.info.id;
                    ($scope.onSelectCallback || angular.noop)({
                        selected_client: selected_record
                    });
                };
            },
            link: function (scope, element, attrs) {
                scope.results = null;
                scope.allow_register = angular.isDefined(attrs.allowRegister);
                scope.custom_register = angular.isDefined(attrs.customRegister);
                if (angular.isDefined(scope.getSearchApi)) {
                    scope.getSearchApi({
                        api: {
                            performSearch: scope.performSearch,
                            setQuery: scope.setQuery
                        }
                    });
                }
            },
            template: '\
<form class="form-horizontal marginal" role="form">\
    <div class="input-group input-group-lg">\
        <input id="search" class="form-control" type="text" ng-model="query" autocomplete="off"\
               ng-change="clear_results()"\
               placeholder="Поиск пациента по коду, ФИО, дате рождения, полису или документу, удостоверяющему личность"\
               autofocus>\
        <span class="input-group-btn">\
            <button class="btn btn-success" ng-click="startSearch()"><span class="glyphicon glyphicon-search"></span> Найти</button>\
        </span>\
    </div>\
</form>\
<div>\
    <div class="row" ng-class="{\'text-danger\': results.length === 0, \'text-success\': results.length > 0}">\
        <div class="col-sm-8">\
            <span ng-if="results.length > 0" class="lead">Результаты поиска</span>\
            <span ng-if="results.length === 0 && query">Пациент не найден в базе данных</span>\
        </div>\
        <div class="col-sm-4 text-right" ng-if="allow_register">\
            <button ng-click="registerNewClient()" class="btn btn-primary">Зарегистрировать пациента</button>\
        </div>\
    </div>\
    <table id="result_tbl" class="table table-condensed table-clickable table-hover" ng-if="results.length > 0">\
        <thead>\
        <tr>\
            <th width="1%">Код</th>\
            <th width="1%">ФИО</th>\
            <th width="1%">Дата рождения</th>\
            <th width="1%">Пол</th>\
            <th width="10%">Документ</th>\
            <th width="1%">СНИЛС</th>\
            <th width="10%">Полис ОМС</th>\
            <th width="10%">Полис ДМС</th>\
            <th width="1%">Контакты</th>\
        </tr>\
        </thead>\
        <tbody>\
        <tr ng-repeat="result in results" style="cursor: pointer" ng-class="{\'bg-info text-info\': result.info.id === client_id}">\
            <td ng-click="onClientSelect(result)" ng-bind-html="result.info.id | highlight: query"></td>\
            <td ng-click="onClientSelect(result)" ng-bind-html="result.info.full_name | highlight: query" class="nowrap"></td>\
            <td ng-click="onClientSelect(result)">\
                <div ng-bind-html="result.info.birth_date | asDate | highlight: query"></div>\
                <div ng-bind-html="result.info.age"></div>\
            </td>\
            <td ng-click="onClientSelect(result)" ng-bind="result.info.sex.name"></td>\
            <td ng-click="onClientSelect(result)" ng-bind-html="result.id_document.doc_text | highlight: query"></td>\
            <td ng-click="onClientSelect(result)" ng-bind-html="result.info.snils | formatSnils | highlight: query" class="nowrap"></td>\
            <td ng-click="onClientSelect(result)" ng-bind-html="result.compulsory_policy.policy_text | highlight: query"></td>\
            <td ng-click="onClientSelect(result)">\
                <div ng-repeat="policy in result.voluntary_policies" ng-bind-html="policy.policy_text | highlight: query"></div>\
            </td>\
            <td class="cursor-default">\
                <wm-client-contacts contacts="result.contacts"></wm-client-contacts>\
            </td>\
        </tr>\
        </tbody>\
    </table>\
    <pagination ng-model="pager.current_page" total-items="pager.total_items" items-per-page="pager.items_per_page"\
        max-size="pager.max_pages" ng-change="startSearch()" ng-show="pager.pages > 1" boundary-links="true">\
    </pagination>\
</div>'
        };
    }]);
