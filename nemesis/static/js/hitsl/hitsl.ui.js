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
;