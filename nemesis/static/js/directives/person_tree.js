/**
 * Created by mmalkov on 11.07.14.
 */
angular.module('WebMis20.directives.personTree', [])
.directive('personTree', ['$http', 'PersonTreeUpdater', function($http, PersonTreeUpdater) {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            personId: '=',
            userSelected: '=',
            lockedPersons: '='
        },
        template:
            '<div>\
                <span class="input-group" id="person-query-group">\
                    <span class="input-group-addon"><span class="glyphicon glyphicon-search"></span></span>\
                    <input id="person_query" class="form-control" type="text" ng-model="query" placeholder="Поиск врача" ng-change="compose()" ng-focus="show_tree()"/>\
                    <span class="input-group-btn">\
                        <button type="button" class="btn btn-danger" ng-click="clear()"><span class="glyphicon glyphicon-remove"></span></button>\
                    </span>\
                </span>\
                <div class="css-treeview well well-sm scrolled-tree" ng-mouseleave="hide_tree()" ng-class="{popup: popupable}">\
                    <ul>\
                        <li ng-repeat="spec_group in tree">\
                            <input class="group" type="checkbox" id="spec-[[spec_group.speciality.id]]" checked>\
                            <label class="group" for="spec-[[spec_group.speciality.id]]" ng-bind="spec_group.speciality.name" ></label>\
                            <ul>\
                                <li ng-repeat="person in spec_group.persons">\
                                    <a class="leaf" ng-bind="person.nameFull" ng-click="person_selected(person)"\
                                        ng-if="!checkboxed" ng-class="{\'no-schedule\': display_no_schedule(person)}"></a>\
                                    <label class="leaf" for="doc-[[person.id]]" ng-if="checkboxed" ng-class="{\'no-schedule\': display_no_schedule(person)}">\
                                        <input type="checkbox" id="doc-[[person.id]]" class="leaf" ng-model="person.checked"\
                                               ng-disabled="person.disabled" ng-change="selection_change(person)" >\
                                        [[person.name]]\
                                    </label>\
                                </li>\
                            </ul>\
                        </li>\
                    </ul>\
                </div>\
            </div>',
        link: function ($scope, element, attrs) {
            $scope.popupable = Boolean(attrs.popupable);
            $scope.checkboxed = Boolean(attrs.checkboxed);
            $scope.data = [];
            $scope.query = '';
            $scope.tree = [];
            $scope.persons_with_scheds = [];
            $scope.reloadTree = function() {
                $http.get(
                    url_schedule_all_persons_tree
                ).success(function (data) {
                    $scope.data = data.result;
                    $scope.compose();
                })
            };
            $scope.reset = function () {
                $scope.query = '';
                $scope.reloadTree();
            };
            $scope.compose = function () {
                $scope.tree = $scope.data.map(function (spec_group) {
                    return {
                        speciality: spec_group.speciality,
                        persons: (spec_group.persons).filter(function (person) {
                            var words = $scope.query.split(' ');
                            return $scope.query == '' || words.filter(function (word) {
                                var data = [].concat(person.nameFull, [spec_group.speciality.name]);
                                return data.filter(function (namePart) {
                                    return namePart.toLocaleLowerCase().startswith(word.toLocaleLowerCase())
                                }).length > 0;
                            }).length == words.length;
                        }).map(function (person) {
                            return {
                                id: person.id,
                                name: person.name + (person.org_structure ? (' (' + person.org_structure + ')') : ''),
                                nameFull: '{0}{1}'.format(
                                    person.nameFull.join(' '),
                                    person.org_structure ? (' (' + person.org_structure + ')') : ''
                                ),
                                disabled: ($scope.lockedPersons || []).has(person.id),
                                checked: [].concat($scope.lockedPersons, $scope.userSelected).has(person.id),
                                has_sched: $scope.persons_with_scheds.has(person.id)
                            }
                        })
                    }
                }).filter(function (spec_group) {
                    return spec_group.persons.length > 0;
                });
            };
            $scope.selection_change = function (person) {
                var userSelected = [];
                angular.copy($scope.userSelected, userSelected);
                var index = userSelected.indexOf(person.id);
                if (index > -1) {
                    userSelected.splice(index, 1);
                }
                $scope.tree.map(function (spec_group) {
                    spec_group.persons.filter(function (person) {
                        return person.checked;
                    }).map(function (person) {
                        if (userSelected.indexOf(person.id) == -1) {
                            userSelected.push(person.id);
                        }
                    });
                });
                $scope.userSelected = userSelected;
            };
            $scope.clear = function () {
                $scope.query = '';
                $scope.compose();
            };
            $scope.$watch('lockedPersons', function (new_value, old_value) {
                $scope.compose();
            });
            $scope.$watch('personId', function (new_value, old_value) {
                $scope.compose();
            });
            var we = $(element);
            var person_input = we.find('input#person_query');
            var person_query_group = we.find('#person-query-group');
            var person_tree_div = we.find('div.scrolled-tree');
            $scope.show_tree = function () {
                if (!$scope.popupable) return;
                $scope.compose();
                if (person_tree_div) {
                    person_tree_div.width(person_query_group.width() - 20);
                    person_tree_div.show();
                }
            };
            $scope.hide_tree = function () {
                if (!$scope.popupable) return;
                if (person_tree_div) {
                    person_tree_div.hide();
                    person_input.blur();
                }
            };
            $scope.person_selected = function (person) {
                $scope.query = person.nameFull;
                $scope.hide_tree();
                $scope.personId = person.id;
            };

            $scope.display_no_schedule = function (person) {
                var schedule_dates = PersonTreeUpdater.get_schedule_period();
                return schedule_dates && schedule_dates.length && !person.has_sched;
            };
            $scope.refresh_schedule_info = function (date_period) {
                if (!date_period || !date_period.length) return;
                $http.get(url_api_persons_tree_schedule_info, {
                    params: {
                        beg_date: date_period[0].toISOString(),
                        end_date: date_period[1].toISOString()
                    }
                }).success(function (data) {
                    $scope.persons_with_scheds = data.result.persons_with_scheds;
                    $scope.tree.forEach(function (spec_group) {
                        spec_group.persons.forEach(function (person) {
                            person.has_sched = $scope.persons_with_scheds.has(person.id);
                        });
                    });
                });
            };
            $scope.$watch(PersonTreeUpdater.get_schedule_period, function (n, o) {
                $scope.refresh_schedule_info(n);
            });
            $scope.reset();
        }
    }
}])
.service('PersonTreeUpdater', [function () {
    var schedule_period;
    return {
        get_schedule_period: function () {
            return schedule_period;
        },
        set_schedule_period: function (start_date, end_date) {
            schedule_period = [start_date, end_date];
        }
    };
}]);