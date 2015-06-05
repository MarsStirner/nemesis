'use strict';

angular.module('WebMis20.directives').
    directive('wmKladrAddress', ['$rootScope', function ($rootScope) {
        return {
            restrict: 'E',
            require: '^form',
            transclude: true,
            scope: {
                prefix: '@',
                addressModel: '=',
                editMode: '&'
            },
            controller: function ($scope) {
                var widgets = $scope.widgets = {};
                var modes = $scope.modes = {
                    full_free_input: false,
                    street_free_input: false
                };

                this.registerWidget = function(name, w) {
                    widgets[name] = w;
                };
                $scope.fullFreeInputEnabled = function() {
                    return modes.full_free_input;
                };
                $scope.streetFreeInputEnabled = function () {
                    return modes.street_free_input;
                };
                $scope.setFullFreeInput = function (on, broadcast, changeModels) {
                    modes.full_free_input = on;
                    if (changeModels) {
                        $scope.setFreeInputText(on);
                        if ($scope.addressModel.address) {
                            $scope.addressModel.address.locality = on ?
                                null :
                                ($scope.addressModel.address.locality || {});
                        }
                        $scope.addressModel.dirty = true;
                    }
                    if ($scope.addressModel.synced && broadcast) {
                        $rootScope.$broadcast('addressWidgetFreeInputChanged', {
                            enabled: on
                        });
                    }
                };
                $scope.setStreetInputFree = function (on, broadcast) {
                    modes.street_free_input = on;
                    if ($scope.addressModel.address) {
                        $scope.addressModel.address.street = on ?
                            null :
                            ($scope.addressModel.address.street || {});
                        $scope.addressModel.address.street_free = on ?
                            ($scope.addressModel.address.street_free || '') :
                            null;
                        $scope.addressModel.dirty = true;
                    }
                    if ($scope.addressModel.synced && broadcast) {
                        $rootScope.$broadcast('addressWidgetInputStreetChanged', {
                            enabled: on
                        });
                    }
                };
                $scope.setFreeInputText = function(enabled) {
                    var text = null;
                    if (enabled) {
                        text = '{0}{, |1}{, д. |2}{, к. |3}{, кв. |4}'.formatNonEmpty(
                            widgets.locality.getText(),
                            $scope.streetFreeInputEnabled() ?
                                safe_traverse($scope.addressModel, ['address', 'street_free']):
                                widgets.street.getText(),
                            safe_traverse($scope.addressModel, ['address', 'house_number']),
                            safe_traverse($scope.addressModel, ['address', 'corpus_number']),
                            safe_traverse($scope.addressModel, ['address', 'flat_number'])
                        );
                    }
                    $scope.addressModel.free_input = text;
                };

                this.getLocation = function() {
                    return safe_traverse($scope.addressModel, ['address', 'locality']);
                };

                $scope.clearStreet = function() {
                    $scope.addressModel.address.street = null;
                    widgets.street.clearSearchInput();
                    $scope.addressModel.address.street_free = null;
                };
            },
            link: function(scope, elm, attrs, formCtrl) {
                scope.addressForm = formCtrl;
                var extractState = function (obj) {
                    return {
                        locality_code: safe_traverse(obj, ['address', 'locality', 'code']),
                        free_input: obj.free_input,
                        street_code: safe_traverse(obj, ['address', 'street', 'code']),
                        street_free: safe_traverse(obj, ['address', 'street_free'])
                    };
                };
                var unregisterModesSet = scope.$watch('addressModel', function(newVal, oldVal) {
                    var newState = extractState(newVal),
                        newFullFreeInput = newState.free_input !== null && newState.free_input !== undefined,
                        newStreeFreeInput = newState.street_free !== null && newState.street_free !== undefined;
                    if (newFullFreeInput !== scope.fullFreeInputEnabled()) {
                        scope.setFullFreeInput(newFullFreeInput);
                    }
                    if (newStreeFreeInput !== scope.streetFreeInputEnabled()) {
                        scope.setStreetInputFree(newStreeFreeInput);
                    }
                }, true);
                scope.$watch('addressForm.$dirty', function(n, o) {
                    if (n !== o) {
                        scope.addressModel.dirty = n;
                    }
                });
                scope.$watch('addressModel.dirty', function(n, o) {
                    if (n && !scope.addressForm.$dirty) {
                        scope.addressForm.$setDirty(n);
                    }
                });
                scope.$watch('addressModel.address.locality', function(n, o) {
                    if (n !== o) {
                        scope.clearStreet();
                    }
                });
                scope.$on('addressWidgetFreeInputChanged', function (event, params) {
                    if (scope.fullFreeInputEnabled() !== params.enabled) {
                        scope.setFullFreeInput(params.enabled);
                    }
                });
                scope.$on('addressWidgetInputStreetChanged', function (event, params) {
                    if (scope.streetFreeInputEnabled() !== params.enabled) {
                        scope.setStreetInputFree(params.enabled);
                    }
                });
            },
            template:
'<div class="panel panel-default">\
<div class="panel-body">\
    <div ng-transclude></div>\
    <div class="row">\
    <div class="col-md-9">\
        <div class="row">\
            <div class="form-group col-md-12" ng-show="!fullFreeInputEnabled()"\
                 ng-class="{\'has-error\': addressForm.$dirty &&\
                    (addressForm.locality.$error.required || (!fullFreeInputEnabled() && addressForm.locality.$invalid))}">\
                <label for="[[prefix]]_locality">Населенный пункт</label>\
                <a class="btn btn-link nomarpad pull-right" ng-click="setFullFreeInput(true, true, true)" ng-disabled="!editMode()"\
                    tooltip-popup-delay="1000" tooltip="Если населенный пункт не найден в справочнике адресов Кладр, то адрес можно заполнить полностью в свободном виде">Ввести вручную</a>\
                <wm-kladr-locality id="[[prefix]]_locality" name="locality"\
                    ng-model="addressModel.address.locality" ng-required="!fullFreeInputEnabled() && addressForm.$dirty"\
                    disabled="!editMode()">\
                </wm-kladr-locality>\
            </div>\
            <div class="form-group col-md-12" ng-show="!fullFreeInputEnabled()"\
                 ng-class="{\'has-error\': addressForm.$dirty &&\
                    (fullFreeInputEnabled() ? false : (\
                        streetFreeInputEnabled() ? (addressForm.street_free.$error.required || addressForm.street_free.$invalid) :\
                        (addressForm.street.$error.required || addressForm.street.$invalid)\
                    ))}">\
                <div ng-show="!streetFreeInputEnabled()">\
                    <label for="[[prefix]]_street">Улица</label>\
                    <a class="btn btn-link nomarpad pull-right" ng-click="setStreetInputFree(true, true)" ng-disabled="!editMode()"\
                        tooltip-popup-delay="1000" tooltip="Если введенная улица не найдена в справочнике адресов Кладр, её можно заполнить в свободном виде">Ввести вручную</a>\
                    <wm-kladr-street id="[[prefix]]_street" name="street"\
                        ng-model="addressModel.address.street" ng-required="!fullFreeInputEnabled() && !streetFreeInputEnabled() && addressForm.$dirty"\
                        disabled="!editMode()">\
                    </wm-kladr-street>\
                </div>\
                <div ng-show="streetFreeInputEnabled()">\
                    <label for="[[prefix]]_street_free">Улица в свободном виде</label>\
                    <a class="btn btn-link nomarpad pull-right" ng-click="setStreetInputFree(false, true)" ng-disabled="!editMode()">Выбрать из Кладр</a>\
                    <wm-kladr-street-free id="[[prefix]]_street_free" name="street_free"\
                        model="addressModel.address.street_free" required="!fullFreeInputEnabled() && streetFreeInputEnabled() && addressForm.$dirty"\
                        disabled="!editMode()">\
                    </wm-kladr-street-free>\
                </div>\
            </div>\
            <div class="form-group col-md-12" ng-show="fullFreeInputEnabled()"\
                 ng-class="{\'has-error\': addressForm.$dirty && fullFreeInputEnabled() &&\
                    addressForm.free_input.$error.required && addressForm.free_input.$invalid}">\
                <label for="[[prefix]]_free_input">В свободном виде</label>\
                <a class="btn btn-link nomarpad pull-right" ng-click="setFullFreeInput(false, true, true)" ng-disabled="!editMode()">Выбрать из Кладр</a>\
                <wm-kladr-free-input id="[[prefix]]_free_input" name="free_input"\
                    model="addressModel.free_input" required="fullFreeInputEnabled() && addressForm.$dirty"\
                    disabled="!editMode()">\
                </wm-kladr-free-input>\
            </div>\
        </div>\
    </div>\
    <div class="col-md-3">\
        <div class="row">\
            <div class="form-group col-md-12"\
                 ng-class="{\'has-error\': addressForm.$dirty && addressForm.locality_type.$invalid}">\
                <label for="[[prefix]]_locality_type">Тип населенного пункта</label>\
                <wm-kladr-locality-type id="[[prefix]]_locality_type" name="locality_type"\
                    model="addressModel.locality_type" required="addressForm.$dirty"\
                    disabled="!editMode()">\
                </wm-kladr-locality-type>\
            </div>\
            <div ng-show="!fullFreeInputEnabled()">\
                <div class="form-group col-md-4"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.house_number.$error.required && addressForm.house_number.$invalid}">\
                    <label for="[[prefix]]_house_number">Дом</label>\
                    <wm-kladr-house-number id="[[prefix]]_house_number" name="house_number"\
                        model="addressModel.address.house_number" required="!fullFreeInputEnabled() && addressForm.$dirty"\
                        disabled="!editMode()">\
                    </wm-kladr-house-number>\
                </div>\
                <div class="form-group col-md-4"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.corpus_number.$invalid}">\
                    <label for="[[prefix]]_corpus_number">Корпус</label>\
                    <wm-kladr-corpus-number id="[[prefix]]_corpus_number" name="corpus_number"\
                        model="addressModel.address.corpus_number"\
                        disabled="!editMode()">\
                    </wm-kladr-corpus-number>\
                </div>\
                <div class="form-group col-md-4"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.flat_number.$invalid}">\
                    <label for="[[prefix]]_flat_number">Квартира</label>\
                    <wm-kladr-flat-number id="[[prefix]]_flat_number" name="flat_number"\
                        model="addressModel.address.flat_number"\
                        disabled="!editMode()">\
                    </wm-kladr-flat-number>\
                </div>\
            </div>\
        </div>\
    </div>\
    </div>\
</div>\
</div>'
        };
    }]).
    directive('wmKladrLocality', ['$http', function($http) {
        return {
            require: ['^?wmKladrAddress', '^ngModel'],
            restrict: 'E',
            scope: {
                ngRequired: '=',
                disabled: '='
            },
            controller: function($scope) {
                $scope.refreshLocalityList = function(search_query) {
                    $scope.searchInput = search_query;
                    if (!search_query || search_query.length < 2) return [];
                    var url = '{0}{1}/'.format(search_kladr_city, search_query);
                    $http.get(url, {}).then(function(res) {
                        $scope.locality_list =  res.data.result;
                    });
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                if (kladrCtrl) {
                    kladrCtrl.registerWidget('locality', scope);
                }

                scope.getText = function() {
                    return modelCtrl.$modelValue ? modelCtrl.$modelValue.fullname : scope.searchInput;
                };
            },
            template:
'<ui-select theme="bootstrap" reset-search-input="false"\
        ng-required="ngRequired" ng-disabled="disabled">\
    <ui-select-match placeholder="Введите адрес для поиска" allow-clear>[[$select.selected.fullname]]</ui-select-match>\
    <ui-select-choices repeat="locality in locality_list track by $index"\
            refresh="refreshLocalityList($select.search)">\
        <div ng-bind-html="locality.fullname | highlight: $select.search"></div>\
    </ui-select-choices>\
</ui-select>'
        }
    }]).
    directive('wmKladrLocalityType', ['RefBookService', function(RefBookService) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                scope.rbLocalityType = RefBookService.get('LocalityType');
                kladrCtrl.registerWidget('locality_type', scope);

//                modelCtrl.$parsers.unshift(function(viewValue) {
//                    if (modelCtrl.$isEmpty(viewValue)) {
//                        modelCtrl.$setValidity('select', false);
//                        return undefined;
//                    }
//                    modelCtrl.$setValidity('select', true);
//                    return viewValue;
//                });
            },
            template:
                '<select class="form-control" ng-model="model"\
                    ng-options="item as item.name for item in rbLocalityType.objects track by item.id"\
                    ng-required="required" ng-disabled="disabled">\
                    <option value="">Не выбрано</option>\
                 </select>'
        }
    }]).
    directive('wmKladrStreet', ['$http', function($http) {
        return {
            require: ['^wmKladrAddress', '^ngModel'],
            restrict: 'E',
            scope: {
                ngRequired: '=',
                disabled: '='
            },
            controller: function($scope) {
                $scope.refreshStreetList = function(search_query) {
                    $scope.searchInput = search_query;
                    var locality_code = $scope.getSelectedLocation();
                    if (!locality_code || !search_query || search_query.length < 2) return [];
                    var url = '{0}{1}/{2}/'.format(search_kladr_street, locality_code, search_query);
                    $http.get(url, {}).then(function(res) {
                        $scope.street_list =  res.data.result;
                    });
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                kladrCtrl.registerWidget('street', scope);

                scope.getSelectedLocation = function() {
                    var loc = kladrCtrl.getLocation();
                    return loc ? loc.code : undefined;
                };
                scope.getText = function() {
                    return modelCtrl.$modelValue ? modelCtrl.$modelValue.name : scope.searchInput;
                };
                scope.clearSearchInput =  function() {
                    scope.searchInput = undefined;
                };
            },
            template:
'<ui-select theme="bootstrap" reset-search-input="false"\
        ng-required="ngRequired" ng-disabled="disabled">\
    <ui-select-match placeholder="Введите улицу для поиска" allow-clear>[[$select.selected.name]]</ui-select-match>\
    <ui-select-choices repeat="street in street_list track by $index"\
            refresh="refreshStreetList($select.search)">\
        <div ng-bind-html="street.name | highlight: $select.search"></div>\
    </ui-select-choices>\
</ui-select>'
        }
    }]).
    directive('wmKladrStreetFree', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('streetfree', scope);
            },
            template:
'<input type="text" class="form-control" autocomplete="off"\
    ng-model="model" ng-required="required" ng-disabled="disabled">'
        }
    }]).
    directive('wmKladrHouseNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('housenumber', scope);
            },
            template:
                '<input type="text" class="form-control" autocomplete="off"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrCorpusNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('corpusnumber', scope);
            },
            template:
                '<input type="text" class="form-control" autocomplete="off"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrFlatNumber', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            link: function(scope, elm, attrs, kladrctrl) {
                kladrctrl.registerWidget('flatnumber', scope);
            },
            template:
                '<input type="text" class="form-control" autocomplete="off"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"/>'
        }
    }]).
    directive('wmKladrFreeInput', [function() {
        return {
            require: '^wmKladrAddress',
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            controller: function($scope) {
            },
            link: function(scope, elm, attrs, kladrCtrl) {
                kladrCtrl.registerWidget('freeinput', scope);
            },
            template:
                '<textarea class="form-control" rows="3" autocomplete="off" placeholder="Адрес в свободном виде"\
                    ng-model="model" ng-required="required" ng-disabled="disabled"></textarea>'
        }
    }])
;