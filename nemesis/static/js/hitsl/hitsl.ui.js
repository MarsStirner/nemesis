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
.directive('wmSortableHeader', [function () {
    return {
        restrict: 'A',
        controllerAs: 'wmSortableHeaderCtrl',
        controller: function () {
            this.orders = ['DESC', 'ASC'];
            this.sort_cols = [];
            this.register_col = function (col) {
                this.sort_cols.push(col);
            };
            this.clear_other = function (cur_col) {
                this.sort_cols.forEach(function (col) {
                    if (col !== cur_col) {
                        col.order = undefined;
                    }
                });
            }
        }
    }
}])
.directive('wmSortableColumn', ['$compile', function ($compile) {
    return {
        restrict: 'A',
        require: '^wmSortableHeader',
        scope: {
            onChangeOrder: '&?'
        },
        link: function (scope, element, attrs, allColsCtrl) {
            allColsCtrl.register_col(scope);
            scope.order = undefined;
            scope.column_name = attrs.wmSortableColumn;

            element.click(function () {
                scope.$apply(function () {
                    allColsCtrl.clear_other(scope);
                    scope.order = (scope.order === allColsCtrl.orders[0]) ?
                        allColsCtrl.orders[1] :
                        allColsCtrl.orders[0];
                    scope.onChangeOrder({
                        params: {
                            order: scope.order,
                            column_name: scope.column_name
                        }
                    });
                });
            });
            element.addClass('cursor-pointer text-nowrap');
            var arrow = $('<span class="fa header-sorter"></span>');
            arrow.attr('ng-class', "{'fa-caret-down': order === 'DESC', 'fa-caret-up': order === 'ASC'}");
            element.append(arrow);
            $compile(arrow)(scope);
        }
    }
}])
;