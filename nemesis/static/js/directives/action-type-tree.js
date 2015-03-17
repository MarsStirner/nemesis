/**
 * Created by mmalkov on 14.07.14.
 */
angular.module('WebMis20.directives.ActionTypeTree', ['WebMis20.directives.goodies'])
.service('ActionTypeTreeService', ['$http', '$q', 'CurrentUser', function ($http, $q, CurrentUser) {
    var trees = [],
        cur_user = CurrentUser.get_main_user();
    var Tree = function () {
        var TreeItem = function (source) {
            if (!source) {
                this.id = null;
                this.name = null;
                this.code = null;
                this.flat_code = null;
                this.gid = null;
                this.age = null;
                this.sex = null;
                this.osids = [];
                this.tissue_required = false;
                this.assignable = [];
            } else if (angular.isArray(source)) {
                this.id = source[0];
                this.name = source[1];
                this.code = source[2];
                this.flat_code = source[3];
                this.gid = source[4];
                this.age = source[5];
                this.sex = source[6];
                this.osids = source[7];
                this.tissue_required = source[8];
                this.assignable = source[9];
            } else {
                angular.extend(this, source)
            }
            this.children = []
        };
        TreeItem.prototype.clone = function () {
            return new TreeItem(this)
        };
        var self = this;
        self.lookup = {};
        self.set_data = function (data) {
            self.lookup = {};
            data.map(function (item) {
                self.lookup[item[0]] =  new TreeItem(item)
            });
            angular.forEach(self.lookup, function (tree_item, at_id) {
                if (tree_item.gid && self.lookup.hasOwnProperty(tree_item.gid)) {
                    self.lookup[tree_item.gid].children.push(at_id);
                }
            });
        };
        function tissue_acceptable(action_type, tissue_required) {
            // split at_class 1 in diag action types and lab action types
            return (tissue_required === undefined || action_type.tissue_required === tissue_required);
        }
        self.tissue_acceptable = tissue_acceptable;
        function age_acceptable(client_info, selector) {
            return ! (
                selector[0] != 0 && client_info.age_tuple[selector[0] - 1] < selector[1] ||
                selector[2] != 0 && client_info.age_tuple[selector[2] - 1] > selector[3]
            );
        }
        function sex_acceptable(client_info, sex) {
            return ! (sex && sex != client_info.sex_raw);
        }
        function os_acceptable(orgstructures) {
            return orgstructures && aux.any_in(cur_user.action_type_org_structures, orgstructures)
        }
        self.os_acceptable = os_acceptable;
        function personally_acceptable(id) {
            return cur_user.action_type_personally.length && cur_user.action_type_personally.has(id)
        }
        self.personally_acceptable = personally_acceptable;
        function keywords_acceptable(keywords, item) {
            return keywords.filter(function (keyword) {
                return (item.name.toLowerCase() + ' ' + item.code.toLowerCase()).indexOf(keyword) !== -1
            }).length == keywords.length;
        }
        self.filter = function (query, client_info, check_os, check_person, tissue_required) {
            function is_acceptable(keywords, item) {
                return Boolean(
                    tissue_acceptable(item, tissue_required)
                    && ! item.children.length
                    && sex_acceptable(client_info, item.sex)
                    && age_acceptable(client_info, item.age)
                    && (!check_os || os_acceptable(item.osids))
                    && (!check_person || personally_acceptable(item.id))
                    // TODO: Check for MES
                    && keywords_acceptable(keywords, item)
                )
            }
            var keywords = query.toLowerCase().split(/\s+/i);
            console.log(keywords);
            var filtered = {
                root: new TreeItem(null)
            };
            angular.forEach(self.lookup, function (value, key) {
                try {
                    if (is_acceptable(keywords, value)) {
                        var clone = value.clone();
                        clone.assignable = clone.assignable.filter(function (item) {
                            return age_acceptable(client_info, item[2]) && sex_acceptable(client_info, item[3])
                        });
                        filtered[key] = clone;
                        for (var id = value.gid, value = self.lookup[id]; id; id = value.gid, value = self.lookup[id]) {
                            if (id && !filtered.hasOwnProperty(id)) {
                                filtered[id] =  self.lookup[id].clone();
                            }
                        }
                    }
                } catch(e) {
                    // possible ActionType inconsistency
                    console.log('Error filtering ActionType tree branch for at_id = ' + key);
                }
            });
            angular.forEach(filtered, function (value) {
                var gid = value.gid;
                if (!value.id) return;
                var o = filtered[gid || 'root'];
                if (o) {
                    o.children.push(value.id)
                }
            });
            var render_node = function (id) {
                var value = filtered[id];
                value.children = value.children.map(render_node);
                return value;
            };
            return render_node('root');
        }
    };
    this.get = function (filter_params) {
        var deferred = $q.defer(),
            at_class = filter_params.at_class;
        if (! trees[at_class]) {
            trees[at_class] = new Tree();
            $http.get(url_for_schedule_api_atl_get_flat, {
                params: {
                    at_class: at_class,
                    event_type_id: filter_params.event_type_id,
                    contract_id: filter_params.contract_id
                }
            }).success(function (data) {
                trees[at_class].set_data(data.result);
                deferred.resolve(trees[at_class]);
            })
        } else {
            deferred.resolve(trees[at_class]);
        }
        return deferred.promise;
    }
}])
.service('ActionTypeTreeModal', ['$modal', '$http', 'ActionTypeTreeService', 'WMWindowSync',
        function ($modal, $http, ActionTypeTreeService, WMWindowSync) {
    return {
        open: function (event_id, client_info, filter_params, onCreateCallback) {
            var self_service = this;
            var at_class = undefined,
                tissue = undefined,
                templateUrl,
                at_group = filter_params.at_group;
            switch (at_group) {
                case 'medical_documents':
                    at_class = 0;
                    templateUrl = '/WebMis20/modal-action-create.html';
                    break;
                case 'treatments':
                    at_class = 2;
                    templateUrl = '/WebMis20/modal-action-create.html';
                    break;
                case 'diagnostics':
                    at_class = 1;
                    tissue = false;
                    templateUrl = '/WebMis20/modal-action-create.html';
                    break;
                case 'lab':
                    at_class = 1;
                    tissue = true;
                    templateUrl = '/WebMis20/modal-laboratory-create.html';
                    break;
                default:
                    throw 'bee-dah!'
            }
            filter_params.at_class = at_class;
            delete filter_params.at_group;
            var Controller = function ($scope, $modalInstance) {
                var service;
                $scope.prepared2create = [];
                $scope.url_for_schedule_html_action = url_for_schedule_html_action;
                $scope.event_id = event_id;
                var conditions = $scope.conditions = {
                    query: '',
                    os_check: true,
                    person_check: true
                };
                $scope.query = '';
                $scope.os_check_enabled = true;
                $scope.personal_check_enabled = true;
                $scope.tree = undefined;
                $scope.set_filter = function () {
                    if (typeof service === 'undefined') return;
                    $scope.tree = service.filter(
                        conditions.query,
                        client_info,
                        conditions.os_check,
                        conditions.person_check,
                        tissue
                    );
                };
                $scope.hidden_nodes = [];
                $scope.toggle_vis = function (node_id) {
                    if ($scope.hidden_nodes.has(node_id)) {
                        $scope.hidden_nodes.splice($scope.hidden_nodes.indexOf(node_id), 1);
                    } else {
                        $scope.hidden_nodes.push(node_id);
                    }
                };
                $scope.subtree_shown = function (node_id) {
                    return !$scope.hidden_nodes.has(node_id);
                };
                $scope.cancel = function () {
                    $modalInstance.dismiss('close');
                };
                $scope.add_prepared_action = function (node) {
                    $scope.prepared2create.push({
                        type_id: node.id,
                        type_name: node.name,
                        assigned: node.assignable.map(function (prop) {return prop[0]}),
                        assignable: node.assignable,
                        planned_end_date: new Date()
                    })
                };
                $scope.create_action = function (node_id) {
                    var url = url_for_schedule_html_action + '?action_type_id=' + node_id + '&event_id=' + $scope.event_id;
                    WMWindowSync.openTab(url, onCreateCallback);
                    $scope.$close();
                };
                $scope.create_actions = function () {
                    $http.post(
                        url_schedule_api_create_lab_direction,
                        {
                            event_id: event_id,
                            directions: $scope.prepared2create.map(function (action) {
                                return {
                                    type_id: action.type_id,
                                    assigned: action.assigned,
                                    planned_end_date: action.planned_end_date
                                }
                            })
                        }
                    ).success(function (data) {
                        $scope.$close('created');
                        (onCreateCallback || angular.noop)();
                    }).error(function (data) {
                        var msg = 'Невозможно создать направление на лаб. исследование: {0}.'.format(data.meta.name);
                        alert(msg);
                    });
                };
                $scope.validate_direction_date = function (model_val) {
                    var result = {
                        type: 'directionDate',
                        success: moment(model_val).isAfter(moment())
                    };
                    return result;
                };
                $scope.open_assignments = function (action) {
                    return self_service.openAppointmentModal(action, false);
                };

                ActionTypeTreeService.get(filter_params).then(function (tree) {
                    service = tree;
                    var os_check = false,
                        personal_check = false;
                    angular.forEach(tree.lookup, function (at_item) {
                        if (at_item.osids
                                && service.os_acceptable(at_item.osids)
                                && service.tissue_acceptable(at_item, tissue)) {
                            os_check = true;
                        }
                        if (service.personally_acceptable(at_item.id) && service.tissue_acceptable(at_item, tissue)) {
                            personal_check = true;
                        }
                    });
                    $scope.conditions.os_check = $scope.os_check_enabled = os_check;
                    $scope.conditions.person_check = $scope.personal_check_enabled = personal_check;
                    $scope.set_filter();
                });
            };
            return $modal.open({
                templateUrl: templateUrl,
                size: 'lg',
                controller: Controller,
                windowClass: 'modal-scrollable'
            })
        },
        openAppointmentModal: function (model, date_required) {
            var assigned = {},
                ped = {
                    planned_end_date: model.planned_end_date
                };
            model.assignable.forEach(function (prop) {
                assigned[prop[0]] = model.assigned.has(prop[0]);
            });
            var Controller = function ($scope) {
                $scope.model = model;
                $scope.assigned = assigned;
                $scope.date_required = date_required;
                $scope.ped = ped;
                $scope.ped_disabled = Boolean(model.ped_disabled);
                $scope.assignable = model.assignable.map(function (item) {
                    return item[0];
                });
                $scope.check_all_selected = function () {
                    return $scope.assignable.every(function (prop_id) {
                        return $scope.assigned[prop_id];
                    });
                };
                $scope.select_all = function () {
                    var enabled = !$scope.check_all_selected();
                    $scope.assignable.forEach(function (prop_id) {
                        $scope.assigned[prop_id] = enabled;
                    });
                };
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-action-assignments.html',
//                size: 'sm',
                controller: Controller
            });
            return instance.result.then(function () {
                var result = [];
                for (var key in assigned) {
                    if (! assigned.hasOwnProperty(key)) continue;
                    if (assigned[key]) result.push(parseInt(key));
                }
                model.assigned = result;
                model.planned_end_date = ped.planned_end_date;
            });
        }
    }
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-action-create.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="cancel()">&times;</button>\
            <h4 class="modal-title" id="myModalLabel">Новое действие</h4>\
        </div>\
        <div class="modal-body modal-scrollable">\
            <input class="form-control" type="text" ng-model="conditions.query" wm-slow-change="set_filter()"></input>\
            <div class="checkbox">\
                <label>\
                    <input type="checkbox" ng-model="conditions.person_check" ng-change="set_filter()" ng-disabled="!personal_check_enabled" />\
                    Только разрешённые мне\
                </label>\
            </div>\
            <div class="checkbox">\
                <label>\
                    <input type="checkbox" ng-model="conditions.os_check" ng-change="set_filter()" ng-disabled="!os_check_enabled" />\
                    Только разрешённые в моём отделении\
                </label>\
            </div>\
            <div class="ui-treeview">\
                <ul ng-repeat="root in tree.children">\
                    <li sf-treepeat="node in children of root">\
                        <a ng-click="create_action(node.id)" \
                           ng-if="!node.children.length" target="_blank">\
                            <div class="tree-label leaf">&nbsp;</div>\
                            [ [[node.code]] ] [[ node.name ]]\
                        </a>\
                        <a ng-if="node.children.length" ng-click="toggle_vis(node.id)" class="node">\
                            <div class="tree-label"\
                                 ng-class="{\'collapsed\': !subtree_shown(node.id),\
                                            \'expanded\': subtree_shown(node.id)}">&nbsp;</div>\
                            [ [[node.code]] ] [[ node.name ]]\
                        </a>\
                        <ul ng-if="node.children.length && subtree_shown(node.id)">\
                            <li sf-treecurse></li>\
                        </ul>\
                    </li>\
                </ul>\
            </div>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-default" ng-click="cancel()">Закрыть</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-laboratory-create.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="cancel()">&times;</button>\
            <h4 class="modal-title" id="myModalLabel">Новое направление на лаб. исследование</h4>\
        </div>\
        <div class="modal-body modal-scrollable">\
            <div class="row">\
                <div class="col-md-6">\
                    <input class="form-control" type="text" ng-model="conditions.query" wm-slow-change="set_filter()"></input>\
                    <div class="checkbox">\
                        <label>\
                            <input type="checkbox" ng-model="conditions.person_check" ng-change="set_filter()" ng-disabled="!personal_check_enabled" />\
                            Только разрешённые мне\
                        </label>\
                    </div>\
                    <div class="checkbox">\
                        <label>\
                            <input type="checkbox" ng-model="conditions.os_check" ng-change="set_filter()" ng-disabled="!os_check_enabled" />\
                            Только разрешённые в моём отделении\
                        </label>\
                    </div>\
                    <div class="ui-treeview">\
                        <ul ng-repeat="root in tree.children">\
                            <li sf-treepeat="node in children of root">\
                                <a ng-click="add_prepared_action(node)" ng-if="!node.children.length" class="leaf">\
                                    <div class="tree-label leaf">&nbsp;</div>\
                                    [ [[node.code]] ] [[ node.name ]]\
                                </a>\
                                <a ng-if="node.children.length" ng-click="toggle_vis(node.id)" class="node">\
                                    <div class="tree-label"\
                                         ng-class="{\'collapsed\': !subtree_shown(node.id),\
                                                    \'expanded\': subtree_shown(node.id)}">&nbsp;</div>\
                                    [ [[node.code]] ] [[ node.name ]]\
                                </a>\
                                <ul ng-if="node.children.length && subtree_shown(node.id)">\
                                    <li sf-treecurse></li>\
                                </ul>\
                            </li>\
                        </ul>\
                    </div>\
                </div>\
                <ng-form name="labDirectionsForm">\
                <div class="col-md-6">\
                    <table class="table table-condensed">\
                    <thead>\
                        <tr>\
                            <th>Наименование</th>\
                            <th>Дата/время назначения</th>\
                            <th>Удалить</th>\
                        </tr>\
                    </thead>\
                    <tbody>\
                        <tr ng-repeat="action in prepared2create">\
                            <td ng-if="!action.assignable.length" ng-bind="action.type_name"></td>\
                            <td ng-if="action.assignable.length"><a ng-click="open_assignments(action)" ng-bind="action.type_name"></a></td>\
                            <td><div fs-datetime ng-model="action.planned_end_date" class="validatable"\
                                    wm-validate="validate_direction_date"></div>\
                            </td>\
                            <td><button class="btn btn-danger btn-sm" ng-click="prepared2create.splice($index, 1)"><i class="glyphicon glyphicon-trash"></i></button></td>\
                        </tr>\
                    </tbody>\
                    </table>\
                    <div ng-if="labDirectionsForm.$invalid && labDirectionsForm.$error.directionDate"\
                        class="alert alert-danger">\
                        Планируемая дата и время выполнения не могут быть раньше текущей даты и времени\
                    </div>\
                </div>\
                </ng-form>\
            </div>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-default" ng-click="cancel()">Закрыть</button>\
            <button type="button" class="btn btn-success" ng-click="create_actions()"\
                ng-disabled="labDirectionsForm.$invalid">Создать направления</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-action-assignments.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">Назначаемые исследования</h4>\
        </div>\
        <div class="modal-body">\
            <div class="row" ng-if="date_required">\
                <div class="col-md-6">\
                    <label for="ped">Дата/время назначения</label>\
                    <div fs-datetime id="ped" ng-model="ped.planned_end_date" ng-disabled="ped_disabled"></div>\
                </div>\
            </div>\
            <div class="checkbox">\
                <label><input type="checkbox" ng-checked="check_all_selected()" ng-click="select_all()">Выбрать все</label>\
            </div>\
            <hr class="novmargin"/>\
            <div class="checkbox" ng-repeat="prop in model.assignable">\
                <label><input type="checkbox" ng-model="assigned[prop[0]]">[[ prop[1] ]]</label>\
            </div>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            <button type="button" class="btn btn-success" ng-click="$close()">OK</button>\
        </div>')
}])
;