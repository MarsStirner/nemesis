/**
 * Created by mmalkov on 12.02.15.
 */

angular.module('hitsl.ui')
.directive("wmMultiselect", ['$window', '$templateCache', function($window, $templateCache) {
    return {
        restrict: "A",
        scope: {
            items: '=',
            disabled: '=ngDisabled',
            freetext: '@',
            "class": '@',
            limit: '@'
        },
        require: '?ngModel',
        replace: true,
        template: function(el, attributes) {
            var defaultItemTpl, itemTpl;
            defaultItemTpl = "{{ item }}";
            itemTpl = el.html() || defaultItemTpl;
            return $templateCache.get('templates/fs/multiselect.html').replace(/::item-template/g, itemTpl);
        },
        controller: function($scope, $element, $attrs, $filter) {
            if ($attrs.freetext != null) {
                $scope.dynamicItems = function() {
                    if ($scope.search) {
                        return [$scope.search];
                    } else {
                        return [];
                    }
                };
            } else {
                $scope.dynamicItems = function() {
                    return [];
                };
            }
            $scope.updateDropdownItems = function() {
                var allItems, excludeFilter, searchFilter, limitFilter;
                searchFilter = $filter('filter');
                excludeFilter = $filter('exclude');
                limitFilter = $filter('limitTo');
                allItems = ($scope.items || []).concat($scope.dynamicItems());
                return $scope.dropdownItems = limitFilter(searchFilter(excludeFilter(allItems, $scope.selectedItems), $scope.search), $scope.limit);
            };
            $scope.selectItem = function(item) {
                if ((item != null) && _.indexOf($scope.selectedItems, item) === -1) {
                    $scope.selectedItems = $scope.selectedItems.concat([item]);
                }
                return $scope.search = '';
            };
            $scope.unselectItem = function(item) {
                var index;
                index = _.indexOf($scope.selectedItems, item);
                if (index > -1) {
                    return $scope.selectedItems.splice(index, 1);
                }
            };
            $scope.onBlur = function() {
                $scope.active = false;
                return $scope.search = '';
            };
            $scope.onEnter = function() {
                return $scope.selectItem($scope.dropdownItems.length > 0 ? $scope.listInterface.selectedItem : null);
            };
            $scope.listInterface = {
                onSelect: function(selectedItem) {
                    return $scope.selectItem(selectedItem);
                },
                move: function() {
                    return console.log("not-implemented listInterface.move() function");
                }
            };
            $scope.dropdownItems = [];
            $scope.active = false;
            $scope.$watchCollection('selectedItems', function() {
                return $scope.updateDropdownItems();
            });
            $scope.$watchCollection('items', function() {
                return $scope.updateDropdownItems();
            });
            $scope.$watch('search', function() {
                return $scope.updateDropdownItems();
            });
            return $scope.updateDropdownItems();
        },
        link: function($scope, element, attrs, ngModelCtrl, transcludeFn) {
            var setViewValue;
            if (ngModelCtrl) {
                setViewValue = function(newValue, oldValue) {
                    if (!angular.equals(newValue, oldValue)) {
                        return ngModelCtrl.$setViewValue(newValue);
                    }
                };
                $scope.$watch('selectedItems', setViewValue, true);
                return ngModelCtrl.$render = function() {
                    return $scope.selectedItems = ngModelCtrl.$modelValue || [];
                };
            }
        }
    };
}])
.directive('wmInputFile', ['$log', function ($log) {
    return {
        restrict: 'A',
        scope: {
            file: '=',
            onChange: '&?'
        },
        link: function (scope, elem, attrs) {
            var reader = new FileReader(),
                is_image = false;
            reader.onloadend = function () {
                scope.$apply(function () {
                    if (is_image) {
                        scope.file.image = new Image();
                        scope.file.image.src = reader.result;
                        scope.file.binary_b64 = null;
                    } else {
                        $log.info('file is not an image');
                        scope.file.binary_b64 = reader.result;
                        scope.file.image = null;
                    }
                    console.log(scope.file);
                });
            };
            elem.change(function (event) {
                var file = event.target.files[0];
                scope.file.selected = Boolean(file);
                if (scope.file.selected) {
                    scope.file.mime = file.type;
                    scope.file.size = file.size;
                    scope.file.name = file.name;
                    is_image = /image/.test(file.type);
                    scope.file.type = is_image ? 'image' : 'other';
                    if (is_image) {
                        reader.readAsDataURL(file);
                    } else {
                        reader.readAsDataURL(file);
                    }
                    scope.onChange();
                }
            });
            scope.$watch('file.selected', function (n, o) {
                if (n !== true) {
                    elem.val('');
                }
            })
        }
    }
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-MessageBox-info.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-error.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$dismiss()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-question.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="question"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
        </div>'
    );
}]);