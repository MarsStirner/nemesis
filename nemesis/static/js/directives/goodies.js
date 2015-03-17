/**
 * Created by mmalkov on 15.07.14.
 */
angular.module('WebMis20.directives.goodies', [])
.factory('TimeoutCallback', ['$timeout', '$interval', function ($timeout, $interval) {
    var Timeout = function (callback, timeout) {
        this.timeout = timeout;
        this.hideki = null;
        this.interval_promise = null;
        this.callback = callback;
    };
    Timeout.prototype.kill = function () {
        if (this.hideki) {
            $timeout.cancel(this.hideki);
        }
        if (this.interval_promise) {
            $interval.cancel(this.interval_promise);
        }
    };
    Timeout.prototype.start = function (timeout) {
        this.kill();
        if (timeout !== undefined) {
            this.timeout = timeout;
        }
        this.hideki = $timeout(this.callback, this.timeout);
    };
    Timeout.prototype.start_interval = function (count, timeout) {
        this.kill();
        if (timeout !== undefined) {
            this.timeout = timeout;
        }
        this.interval_promise = $interval(this.callback, this.timeout, count || 0, false);
    };
    return Timeout;
}])
.factory('FlatTree', [function () {
    var Tree = function (masterField) {
        this.nodes = [];
        this.array = [];
        this.masterField = masterField;
        var idField = this.idField = arguments[1] || 'id';
        var childrenField = this.childrenField = arguments[2] || 'children';
        this.masterDict = dict({
            root: []
        })
    };
    Tree.prototype.set_array = function (array) {
        var idField = this.idField,
            masterField = this.masterField,
            idDict = this.idDict = new dict({
                root: null
            });
        this.array = array;
        array.forEach(function (item) {
            var id = item[idField];
            idDict[id] = item;
        });
        var nodes = this.nodes = [];
        array.forEach(function (item) {
            var master = item[masterField] || 'root';
            if (!nodes.has(master)) nodes.push(master);
        });
        return this;
    };
    Tree.prototype.filter = function (filter_function) {
        var idDict = this.idDict,
            masterField = this.masterField,
            idField = this.idField;
        var masterDict = this.masterDict = new dict({
            root: []
        });
        var filtered;
        if (filter_function === undefined) {
            filtered = this.array;
        } else {
            filtered = this.array.filter(function (item) {
                return filter_function(item, idDict)
            });
        }
        filtered.forEach(function (item) {
            do {
                var master = item[masterField] || 'root';
                if (!idDict.hasOwnProperty(master)) {master = 'root'}
                if (masterDict[master] === undefined) masterDict[master] = [];
                if (masterDict[master].has(item[idField])) return;
                masterDict[master].push(item[idField]);
                item = idDict[master];
            } while (item)
        });
        return this;
    };
    Tree.prototype.render = function (make_object) {
        var masterDict = this.masterDict,
            childrenField = this.childrenField,
            idDict = this.idDict,
            nodes = this.nodes;
        function recurse(id) {
            var childrenObject = {};
            var children_list = masterDict[id] || [];
            childrenObject[childrenField] = children_list.map(recurse);
            return angular.extend({}, make_object(idDict[id], nodes.has(id)), childrenObject);
        }
        return {
            root: recurse('root'),
            idDict: idDict,
            masterDict: masterDict
        };
    };
    var dict = function () {
        if (arguments[0]) {angular.extend(this, arguments[0])}
    };
    dict.prototype.keys = function () {
        var result = [];
        for (var key in this) {
            if (this.hasOwnProperty(key) && !key.startswith('$') && ! (typeof this[key] === 'function')) {
                result.push(key)
            }
        }
        return result;
    };
    return Tree;
}])
.directive('wmCustomDropdown', ['$timeout', '$compile', 'TimeoutCallback', function ($timeout, $compile, TimeoutCallback) {

    return {
        restrict: 'E',
        require: 'ngModel',
        scope: {
            onSelected: '&',
            wmTimeout: '@'
        },
        link: function (scope, original_element, attrs, ngModel) {
            var wmTimeout = scope.wmTimeout || 600;
            // Templating...
            var element = $(original_element);
            var element_input = $('<input type="text" ng-model="$query" class="form-control">');
            var element_control = $('<div class="input-group"></div>');
            element_control.append('<span class="input-group-addon"><i class="glyphicon glyphicon-search"></i></span>');
            element_control.append(element_input);
            element_control.append('<span class="input-group-btn"><button class="btn btn-default" ng-click="$query=\'\'"><i class="glyphicon glyphicon-remove"></i></button></span>');
            var element_popup = $('<div class="wm-popup well well-sm"></div>');
            element_popup.append(element.html());
            var element_wrapper = $('<div style="display: inline"></div>');
            element_wrapper.append(element_control).append(element_popup);
            element.replaceWith(element_wrapper);

            // Handling popups...
            var popupTimeoutObject = new TimeoutCallback(hide_popup, wmTimeout);
            var changeTimeoutObject = new TimeoutCallback(function () {
                scope.$broadcast('FilterChanged', scope.$query)
            }, 400);
            scope.$watch('$query', function (n, o) {
                if (angular.equals(n, o)) return n;
                changeTimeoutObject.start()
            });
            function hide_popup () {
                popupTimeoutObject.kill();
                element_popup.hide();
            }
            function show_popup () {
                popupTimeoutObject.kill();
                element_popup.width(element_control.width() - 20);
                element_popup.show();
            }
            element_input.focusin(show_popup);
            element_input.click(show_popup);
            element_popup.mouseenter(show_popup);
            element_popup.mouseleave(function() {popupTimeoutObject.start()});

            scope.$ctrl = {
                $set_query: function (query) {scope.$query = query},
                $select: function (item) {
                    ngModel.$setViewValue(item);
                    ngModel.$render();
                    if (scope.onSelected) scope.onSelected(item);
                    hide_popup();
                }
            };
            scope.$query = '';

            $compile(element_wrapper)(scope);
        }
    }
}])
.directive('wmSlowChange', function ($timeout) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, element, attr, ngModel) {
            var query_timeout = null;
            function ensure_timeout_killed () {
                if (query_timeout) {
                    $timeout.cancel(query_timeout);
                    query_timeout = null;
                }
            }
            ngModel.$viewChangeListeners.push(function () {
                ensure_timeout_killed();
                query_timeout = $timeout(function () {
                    scope.$eval(attr.wmSlowChange)
                }, attr.wmSlowChangeTimeout || 600)
            });
        }
    }
})
.directive('wmDebounce', function($timeout) {
    // or ngModelOptions in angularjs 1.3+
    return {
        restrict: 'A',
        require: 'ngModel',
        priority: 99,
        link: function(scope, elm, attr, ngModelCtrl) {
            if (attr.type === 'radio' || attr.type === 'checkbox') return;

            elm.unbind('input');
            var debounce;
            elm.bind('input', function() {
                $timeout.cancel(debounce);
                debounce = $timeout(function() {
                    scope.$apply(function() {
                        ngModelCtrl.$setViewValue(elm.val());
                    });
                }, attr.ngDebounce || 1000);
            });
            elm.bind('blur', function() {
                scope.$apply(function() {
                    ngModelCtrl.$setViewValue(elm.val());
                });
            });
        }
    }
})
.directive('bindOnce', function() {
    // until angularjs 1.3+ one-time-binding ::
    return {
        scope: true,
        link: function( $scope, $element ) {
            setTimeout(function() {
                $scope.$destroy();
                $element.removeClass('ng-binding ng-scope');
            }, 0);
        }
    }
});
