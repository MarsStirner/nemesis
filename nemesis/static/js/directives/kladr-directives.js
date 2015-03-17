'use strict';

angular.module('WebMis20.directives').
    directive('wmKladrAddress', [function () {
        return {
            restrict: 'E',
            require: '^form',
            transclude: true,
            scope: {
                prefix: '@',
                addressModel: '=',
                dependentAddress: '=',
                editMode: '&'
            },
            controller: function ($scope) {
                var widgets = $scope.widgets = {};
                var mode = $scope.mode = {};
                mode.kladr_addr_valid = false;
                mode.switch_to_free_input = false;

                this.registerWidget = function(name, w) {
                    widgets[name] = w;
                };

                $scope.inFreeInputMode = function() {
                    return mode.switch_to_free_input;
                };

                $scope.show_warning = function () {
                  return (!$scope.mode.kladr_addr_valid && $scope.addressForm.$dirty) &&
                      !($scope.addressModel.synced && $scope.dependentAddress)
                };

                $scope.setFreeInputText = function(switched) {
                    var text = '';
                    if (switched) {
                        text = [
                            widgets.locality.getText(),
                            widgets.street.getText(),
                            'д. ' + (widgets.housenumber.model || '') + (widgets.corpusnumber.model ?
                                                                         'к. ' + widgets.corpusnumber.model : ''),
                            'кв. ' + (widgets.flatnumber.model || '')
                        ].join(', ');
                    }
                    widgets.freeinput.model = text;
                };

                this.getLocation = function() {
                    return widgets.locality.model;
                };

                $scope.clearStreet = function() {
                    widgets.street.reset();
                };
            },
            link: function(scope, elm, attrs, formCtrl) {
                scope.addressForm = formCtrl;

                scope.$watchCollection(function() {
                    return [scope.widgets.locality.model, scope.widgets.street.model];
                }, function(n, o) {
                    scope.mode.kladr_addr_valid = n.filter(function(model) {
                        return angular.isDefined(model);
                    }).length === n.length;
                });
                var unregister_init_mode_set = scope.$watch('widgets.freeinput.model', function(n, o) {
                    // для совпадающих адресов
                    if (angular.isString(n) && n !== '') {
                        scope.mode.switch_to_free_input = true;
//                        unregister_init_mode_set();
                    } else {
                         scope.mode.switch_to_free_input = false;
                    }
                });
                scope.$watch('mode.switch_to_free_input', function(n, o) {
                    if (n !== o) {
                        scope.setFreeInputText(n);
                        scope.$broadcast('switch_to_freeinput', n);
                    }
                });
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
                scope.$watch(function() {
                    return scope.widgets.locality.model;
                }, function(n, o) {
                    if (n !== o) { scope.clearStreet(); }
                });
            },
            template:
'<div>\
    <div class="panel panel-default">\
        <div class="panel-body">\
            <div ng-transclude></div>\
            <alert ng-show="show_warning()" type="danger">Введенный адрес не найден в справочнике адресов Кладр.\
                <a ng-click="mode.switch_to_free_input = !mode.switch_to_free_input">\
                [[mode.switch_to_free_input ? "Выбрать из Кладр" : "Ввести адрес вручную?"]]</a>\
            </alert>\
            <div class="row">\
                <div class="form-group col-md-9"\
                     ng-class="{\'has-error\': addressForm.$dirty &&\
                        (addressForm.locality.$error.required || (!inFreeInputMode() && addressForm.locality.$invalid))}">\
                    <label for="[[prefix]]_locality">Населенный пункт</label>\
                    <wm-kladr-locality id="[[prefix]]_locality" name="locality"\
                        model="addressModel.address.locality" required="!inFreeInputMode() && addressForm.$dirty"\
                        disabled="mode.switch_to_free_input || !editMode()">\
                    </wm-kladr-locality>\
                </div>\
                <div class="form-group col-md-3"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.locality_type.$invalid}">\
                    <label for="[[prefix]]_locality_type">Тип населенного пункта</label>\
                    <wm-kladr-locality-type id="[[prefix]]_locality_type" name="locality_type"\
                        model="addressModel.locality_type" required="addressForm.$dirty"\
                        disabled="!editMode()">\
                    </wm-kladr-locality-type>\
                </div>\
            </div>\
\
            <div class="row">\
                <div class="form-group col-md-9"\
                     ng-class="{\'has-error\': addressForm.$dirty &&\
                        (addressForm.street.$error.required || (!inFreeInputMode() && addressForm.street.$invalid))}">\
                    <label for="[[prefix]]_street">Улица</label>\
                    <wm-kladr-street id="[[prefix]]_street" name="street"\
                        model="addressModel.address.street" required="!inFreeInputMode() && addressForm.$dirty"\
                        disabled="mode.switch_to_free_input || !editMode()">\
                    </wm-kladr-street>\
                </div>\
                <div class="form-group col-md-1"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.house_number.$error.required && addressForm.house_number.$invalid}">\
                    <label for="[[prefix]]_house_number">Дом</label>\
                    <wm-kladr-house-number id="[[prefix]]_house_number" name="house_number"\
                        model="addressModel.address.house_number" required="!inFreeInputMode() && addressForm.$dirty"\
                        disabled="mode.switch_to_free_input || !editMode()">\
                    </wm-kladr-house-number>\
                </div>\
                <div class="form-group col-md-1"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.corpus_number.$error.required && addressForm.corpus_number.$invalid}">\
                    <label for="[[prefix]]_corpus_number">Корпус</label>\
                    <wm-kladr-corpus-number id="[[prefix]]_corpus_number" name="corpus_number"\
                        model="addressModel.address.corpus_number" required="false"\
                        disabled="mode.switch_to_free_input || !editMode()">\
                    </wm-kladr-corpus-number>\
                </div>\
                <div class="form-group col-md-1"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.flat_number.$error.required && addressForm.flat_number.$invalid}">\
                    <label for="[[prefix]]_flat_number">Квартира</label>\
                    <wm-kladr-flat-number id="[[prefix]]_flat_number" name="flat_number"\
                        model="addressModel.address.flat_number" required="false"\
                        disabled="mode.switch_to_free_input || !editMode()">\
                    </wm-kladr-flat-number>\
                </div>\
            </div>\
\
            <div class="row" ng-show="inFreeInputMode()">\
                <div class="form-group col-md-12"\
                     ng-class="{\'has-error\': addressForm.$dirty && addressForm.free_input.$error.required && addressForm.free_input.$invalid}">\
                    <label for="[[prefix]]_free_input">В свободном виде</label>\
                    <wm-kladr-free-input id="[[prefix]]_free_input" name="free_input"\
                        model="addressModel.free_input" required="inFreeInputMode() && addressForm.$dirty"\
                        disabled="!mode.switch_to_free_input || !editMode()">\
                    </wm-kladr-free-input>\
                </div>\
            </div>\
        </div>\
    </div>\
</div>'
        };
    }]).
    directive('wmKladrLocality', ['$http', function($http) {
        return {
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            controller: function($scope) {
                $scope.getCity = function(search_q) {
                    var url = [kladr_city + 'search/' + search_q + '/'].join('');
//                    var url = url_kladr_city_get;
                    return $http.get(url, {}).then(function(res) {
                        return res.data.result;
                    });
                };
            },
            link: function(scope, elm, attrs, ctrls) {
                var kladrCtrl = ctrls[0],
                    modelCtrl = ctrls[1];
                kladrCtrl.registerWidget('locality', scope);

                scope.getText = function() {
                    return modelCtrl.$viewValue;
                };
                scope.reset =  function() {
                    scope.model = undefined;
                };

                scope.$on('switch_to_freeinput', function(event, on) {
                    modelCtrl.$setValidity('editable', on);
                });
            },
            template:
                '<input type="text" class="form-control" placeholder="" autocomplete="off"\
                    ng-model="model" typeahead="city as city.name for city in getCity($viewValue)"\
                    typeahead-wait-ms="1000" typeahead-min-length="2" typeahead-editable="false"\
                    ng-required="required" ng-disabled="disabled"/>'
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
            require: ['^wmKladrAddress', 'ngModel'],
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                required: '=',
                disabled: '='
            },
            controller: function($scope) {
                $scope.getStreet = function(search_q) {
                    var loc = $scope.getSelectedLocation();
                    if (!loc) {
                        return [];
                    }
                    var url = [kladr_street, 'search/', loc, '/', search_q, '/' ].join('');
//                    var url = url_kladr_street_get;
                    return $http.get(url, {}).then(function(res) {
                        return res.data.result;
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
                    return modelCtrl.$viewValue;
                };
                scope.reset =  function() {
                    scope.model = undefined;
                    modelCtrl.$setViewValue('');
                    modelCtrl.$render();
                };

                scope.$on('switch_to_freeinput', function(event, on) {
                    modelCtrl.$setValidity('editable', on);
                });
            },
            template:
                '<input type="text" class="form-control" autocomplete="off" placeholder=""\
                    ng-model="model" typeahead="street as street.name for street in getStreet($viewValue)"\
                    typeahead-wait-ms="1000" typeahead-min-length="2" typeahead-editable="false"\
                    ng-required="required" ng-disabled="disabled"/>'
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