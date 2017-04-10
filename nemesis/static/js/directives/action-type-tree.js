/**
 * Created by mmalkov on 14.07.14.
 */
angular.module('WebMis20.directives.ActionTypeTree', ['WebMis20.directives.goodies'])
.service('ActionTypeTreeService', ['ApiCalls', '$q', 'CurrentUser', 'WMConfig', function (ApiCalls, $q, CurrentUser, WMConfig) {
    var trees = [],
        cur_user = CurrentUser.get_main_user();
    var Tree = function () {
        var self = this;
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
                this.note_mandatory = false;
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
                this.note_mandatory = source[11];
            } else {
                angular.extend(this, source)
            }
            this.children = []
        };
        TreeItem.prototype.clone = function () {
            return new TreeItem(this)
        };
        TreeItem.prototype.sort_children = function () {
            if (this.children && _.isArray(this.children)) {
                this.children.sort(function (x, y) {
                    var a = self.lookup[x],
                        b = self.lookup[y];
                    if (a.code > b.code) {
                        return 1;
                    } else if (a.code < b.code) {
                        return -1;
                    } else {
                        return 0;
                    }
                })
            }
        };
        self.lookup = {};
        self.set_data = function (data) {
            self.lookup = _.chain(
                data
            ).makeObject(
                function (item) { return item[0] },
                function (item) { return new TreeItem(item) }
            ).each(function (item, at_id, context) {
                if (item.gid && _.has(context, item.gid)) {
                    context[item.gid].children.push(at_id);
                }
            }).value()
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
            var item_test_data = '{0} {1}'.format(item.name, item.code).toLowerCase();
            return _.all(keywords, function (keyword) {
                return item_test_data.indexOf(keyword) !== -1
            });
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
            _.chain(
                self.lookup
            ).filter(
                _.partial(is_acceptable, keywords)
            ).each(
                function (value) {
                    var id = value.id;
                    var clone = filtered[id] = value.clone();
                    // Построение недостающих родительских узлов - подъём по дереву вверх до первого найденного
                    while (id) {
                        id = value.gid;
                        if (!id) break;
                        if (!_.has(self.lookup, id)) {
                            console.log('Проблема с ActionType.id = {0}: его родитель ActionType.id = {1} не найден или удалён'.format(value.id, value.gid));
                            return
                        }
                        value = self.lookup[id];

                        if (!_.has(filtered, id)) {
                            filtered[id] =  value.clone();
                        }
                    }
                }
            ).value();
            _.chain(
                filtered
            ).each(function (value) {
                // Установка идентификаторов дочерних элементов у каждого элемента в отфильтрованном дереве
                var gid = value.gid;
                if (!value.id) return;
                var o = filtered[gid || 'root'];
                if (o) {
                    o.children.push(value.id)
                }
            }).each(function (value) {
                // Сортировка идентификаторов дочерних элементов
                // Это нельзя сделать в перыдущей функции, потому что там они ещё не все готовы
                value.sort_children()
            }).value();
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
            var url;
            if (_.isUndefined(filter_params.event_type_id)) {
                url = '{0}{1}/'.format(WMConfig.url.actions.atl_get_flat, at_class)
            } else {
                url = '{0}{1}/{2}/'.format(WMConfig.url.actions.atl_get_flat, at_class, filter_params.event_type_id)
            }
            ApiCalls.wrapper('GET',url).then(
                function (data) {
                    trees[at_class].set_data(data);
                    deferred.resolve(trees[at_class]);
                }
            )
        } else {
            deferred.resolve(trees[at_class]);
        }
        return deferred.promise;
    }
}])
.service('APTGroupsService', ['$q', 'WebMisApi', function ($q, WebMisApi) {
    var APTGroup = function (master_id, dependent_ids) {
        this.master_apt_id = master_id;
        this.dependent_apt_ids = dependent_ids;
    };
    var ATAPTGroups = function () {
        this.groups = {};
        this.reversedGroups = {};
    };

    ATAPTGroups.prototype.available = function () {
        return !_.isEmpty(this.groups);
    };
    ATAPTGroups.prototype.addGroup = function (group) {
        this.groups[group.master_apt_id] = group;
        var that = this;
        group.dependent_apt_ids.forEach(function (dep_id) {
            if (!that.reversedGroups.hasOwnProperty(dep_id)) {
                that.reversedGroups[dep_id] = [];
            }
            that.reversedGroups[dep_id].push(group.master_apt_id);
        });
    };
    ATAPTGroups.prototype.getSelectionDeps = function (apt_id, selected) {
        // проверить дочерние apt при выборе родителя
        var res = {
            ok: true,
            dependents: []
        };
        var that = this;
        var getDeps = function (apt_id) {
            var r = [],
                new_deps;
            if (that.groups.hasOwnProperty(apt_id)) {
                // те дочерние apt_id, которые должны быть выбранными
                new_deps = _.difference(that.groups[apt_id].dependent_apt_ids, selected);
                Array.prototype.push.apply(r, new_deps);
                _.each(new_deps, function (d_apt_id) {
                    Array.prototype.push.apply(r, getDeps(d_apt_id));
                });
            }
            return r;
        };

        res.dependents = getDeps(apt_id);
        res.ok = !Boolean(res.dependents.length);
        return res;
    };
    ATAPTGroups.prototype.getUnselectionDeps = function (apt_id, selected) {
        // проверить родительские apt при снятии выбора с родителя
        var res = {
            ok: true,
            dependents: []
        };
        var that = this;
        var getDeps = function (apt_id) {
            var r = [],
                new_deps;
            if (that.reversedGroups.hasOwnProperty(apt_id)) {
                // те родительские apt_id, которые не должны остаться выбранными
                new_deps = _.intersection(that.reversedGroups[apt_id], selected);
                Array.prototype.push.apply(r, new_deps);
                _.each(new_deps, function (d_apt_id) {
                    Array.prototype.push.apply(r, getDeps(d_apt_id));
                });
            }
            return r;
        };

        res.dependents = getDeps(apt_id);
        res.ok = !Boolean(res.dependents.length);
        return res;
    };

    var groups = {};
    this.get = function (action_type_id) {
        var deferred = $q.defer();
        if (!groups.hasOwnProperty(action_type_id)) {
            WebMisApi.action.get_apt_groups(action_type_id)
                .then(function (group_data) {
                    var g = groups[action_type_id] = new ATAPTGroups();
                    angular.forEach(group_data, function (id_list, master_id) {
                        g.addGroup(new APTGroup(parseInt(master_id), id_list));
                    });
                    deferred.resolve(g);
                });
        } else {
            deferred.resolve(groups[action_type_id]);
        }
        return deferred.promise;
    };
}])
.service('ActionTypeTreeModal', [
        '$modal', '$http', 'ActionTypeTreeService', 'WMWindowSync', 'WMEventServices', 'AccountingService',
        'MessageBox', 'WMConfig', 'RefBookService', '$timeout', 'WebMisApi', 'APTGroupsService',
        function ($modal, $http, ActionTypeTreeService, WMWindowSync, WMEventServices, AccountingService,
                  MessageBox, WMConfig, RefBookService, $timeout, WebMisApi, APTGroupsService) {
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
                $scope.url_for_schedule_html_action = WMConfig.url.actions.action_html;
                $scope.event_id = event_id;
                var conditions = $scope.conditions = {
                    query: '',
                    os_check: true,
                    person_check: true
                };
                var ServiceKind = RefBookService.get('ServiceKind');
                var sk_lab_action_id;
                ServiceKind.get_by_code_async('lab_action').then(function (res) {
                    sk_lab_action_id = res.id;
                });
                $scope.query = '';
                $scope.os_check_enabled = true;
                $scope.personal_check_enabled = true;
                $scope.tree = undefined;
                $scope.at_service_data = {};
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
                $scope.all_nodes_expanded = {value: false};
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
                    var service_data, sd, no_ss;
                    if ($scope.at_service_data.hasOwnProperty(node.id)) {
                        sd = $scope.at_service_data[node.id];
                        no_ss = sd.service_kind.id === sk_lab_action_id && sd.is_complex_service;
                        service_data = {
                            service_data: {
                                service_kind_id: sd.service_kind.id,
                                price_list_item_id: sd.price_list_item_id,
                                event_id: $scope.event_id,
                                serviced_entity_from_search: angular.extend({}, sd, {no_subservices: no_ss}),
                                no_subservices: no_ss
                            }
                        }
                    }
                    WebMisApi.action.get_new_lab(node.id, $scope.event_id, service_data)
                        .then(function (newAction) {
                            $scope.prepared2create.push(newAction);
                        });
                };
                $scope.create_action = function (node) {
                    // или сохранить сразу или открыть вкладку с редактированием нового экшена
                    if (filter_params.instant_create) {
                        var service;
                        if ($scope.at_service_data.hasOwnProperty(node.id)) {
                            service = angular.extend($scope.at_service_data[node.id], {event_id: $scope.event_id});
                        }
                        var data = {
                            action_type_id: node.id,
                            event_id: $scope.event_id,
                            service: service
                        };
                        $http.post(WMConfig.url.actions.action_save.format(''), data)
                            .then(
                                $scope.$close,
                                function (response) {
                                    return MessageBox.error(
                                        'Ошибка сохранения',
                                        response.data.meta.name
                                    );
                                }
                            )
                            .then(onCreateCallback);
                    } else {
                        var service_available = $scope.at_service_data.hasOwnProperty(node.id),
                            service_data = $scope.at_service_data[node.id];
                        var url = WMConfig.url.actions.action_html + '?action_type_id=' + node.id +
                            '&event_id=' + $scope.event_id;
                        if (service_available) {
                            url = '{0}&price_list_item_id={1}&service_kind_id={2}'.format(
                                url, service_data.price_list_item_id, service_data.service_kind.id
                            );
                        }
                        WMWindowSync.openTab(url, onCreateCallback);
                        $scope.$close();
                    }
                };
                $scope.create_actions = function () {
                    $http.post(
                        WMConfig.url.actions.create_lab_direction,
                        {
                            event_id: event_id,
                            directions: $scope.prepared2create.map(function (action) {
                                return {
                                    type_id: action.type_id,
                                    props_data: action.props_data,
                                    planned_end_date: action.planned_end_date,
                                    service: action.service,
                                    urgent: action.urgent,
                                    ttj: {
                                        selected_tissue_type: action.selected_tissue_type
                                    },
                                    note: action.note
                                }
                            })
                        }
                    ).success(function (data) {
                        $scope.$close('created');
                        (onCreateCallback || angular.noop)();
                    }).error(function (data) {
                        var msg = 'Невозможно создать направление на лаб. исследование: {0}.'.format(data.meta.name);
                        MessageBox.error(
                            'Ошибка',
                            msg
                        );
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
                    return self_service.openAppointmentModal(action, false)
                        .then(function () {
                            if (action.service) {
                                action.service.serviced_entity.tests_data.props_data = action.props_data;
                                AccountingService.refreshServiceSubservices(action.service)
                                    .then(function (upd_service) {
                                        angular.copy(upd_service, action.service);
                                    });
                            }
                        });
                };
                $scope.get_at_item_price = function (at_id) {
                    var price = '',
                        sd;
                    if ($scope.at_service_data.hasOwnProperty(at_id)) {
                        sd = $scope.at_service_data[at_id];
                        if (Boolean(sd.is_accumulative_price)) {
                            price = 'Составная стоимость'
                        } else {
                            price = String(sd.price) + ' руб.';
                        }
                    }
                    return price;
                };
                $scope.action_has_price = function (action) {
                    return Boolean(action.service);
                };
                $scope.get_action_price = function (action) {
                    return safe_traverse(action, ['service', 'sum']);
                };
                $scope.filterItemLabTissueType = function (action) {
                    return function (item) {
                        return action.available_tissue_types.has(item.id);
                    }
                };
                $scope.labHasTestsWithPrices = function (action) {
                    return action.service.service_kind.id === sk_lab_action_id &&
                        action.service.is_complex_service;
                };
                $scope.labTestsServiceErrorVisible = function (action) {
                    return !action.service || ($scope.labHasTestsWithPrices(action) &&
                        !action.service.subservice_list.length);
                };
                $scope.labTestsServicesSelected = function () {
                    return $scope.prepared2create.filter(function (action) {
                        return action.service && $scope.labHasTestsWithPrices(action);
                    }).every(function (action) {
                        return action.service.subservice_list.length > 0;
                    });
                };
                $scope.actionReasonRequired = function (action) {
                    return Boolean(action.note_mandatory);
                };

                AccountingService.getServiceActionTypePrices(filter_params.contract_id)
                    .then(function (at_service_data) {
                        $scope.at_service_data = at_service_data;
                    });
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
                        if (at_item.children.length) {
                            $scope.hidden_nodes.push(at_item.id);  // по умолчанию все узлы свернуты
                        }
                    });
                    $scope.conditions.os_check = $scope.os_check_enabled = os_check;
                    $scope.conditions.person_check = $scope.personal_check_enabled = personal_check;
                    $scope.set_filter();
                });
                $scope.$watch('all_nodes_expanded.value', function(n, o){
                    if (n!=o){
                        if (n){
                            $scope.hidden_nodes = [];
                        } else {
                            angular.forEach($scope.tree.children, function (at_item) {
                                if (at_item.children.length) {
                                    $scope.hidden_nodes.push(at_item.id)
                                }
                            });
                        }
                    }
                })
            };
            var modalInstance = $modal.open({
                templateUrl: templateUrl,
                backdrop : 'static',
                size: 'lg',
                controller: Controller,
                windowClass: 'modal-scrollable'
            });

            modalInstance.opened.then(function () {
                var lastScrollTop = 0;
                $timeout(function(){
                    $(".affix-container").on("scroll", function(e){
                        var $box=$(e.target);
                        var $ad=$(e.target).find(".modal-affix");

                        var scrollTop=$box.scrollTop();
                        var adHeight=$ad.height();
                        var boxHeight=($box.height() - 250) > 0 ? $box.height() - 250 : $box.height();
                        var adTop = parseInt($ad.css("top"));
                            if(isNaN(adTop)) adTop = 0;

                        if (scrollTop > lastScrollTop){
                           // downscroll code
                           $ad.css("position","relative").css("top", adTop < (scrollTop + boxHeight - adHeight) ? adTop + Math.abs(scrollTop-lastScrollTop) : adTop + "px");
                        } else {
                          // upscroll code
                          $ad.css("position","relative").css("top", adTop > (scrollTop) ? adTop - Math.abs(scrollTop-lastScrollTop) : adTop + "px");
                        }

                        lastScrollTop = scrollTop;
                    });
                }, 200);
            });

            return modalInstance;
        },
        openAppointmentModal: function (model, date_required) {
            var assigned = {},
                t_model = {
                    props_data: model.props_data.clone(),
                    planned_end_date: model.planned_end_date,
                    ped_disabled: model.ped_disabled,
                    available_tissue_types: model.available_tissue_types,
                    selected_tissue_type: model.selected_tissue_type,
                    tissue_type_visible: model.tissue_type_visible
                },
                apt_names = {};
            t_model.props_data.forEach(function (prop) {
                assigned[prop.type_id] = prop;
            });
            model.assignable.forEach(function (apt) {
                apt_names[apt[0]] = apt[1];
            });
            var Controller = function ($scope) {
                $scope.model = model;
                $scope.apt_names = apt_names;
                $scope.action_type_id = model.type_id;
                $scope.assigned = assigned;
                $scope.date_required = date_required;
                $scope.t_model = t_model;
                $scope.apt_groups = undefined;
                var getCheckedApts = function (o) {
                    var res = [];
                    _.each(o, function (prop, type_id) {
                        if (prop.is_assigned) {
                            res.push(parseInt(type_id));
                        }
                    });
                    return res;
                };
                APTGroupsService.get($scope.action_type_id)
                    .then(function (apt_groups) {
                        $scope.apt_groups = apt_groups;
                        if ($scope.apt_groups.available()) {
                            $scope.$watch('assigned', function (n, o) {
                                var newSelectedApts = getCheckedApts(n),
                                    oldSelected = getCheckedApts(o);
                                if (!angular.equals(newSelectedApts, oldSelected)) {
                                    var newAptIds = _.difference(newSelectedApts, oldSelected),
                                        cancelledAptIds = _.difference(oldSelected, newSelectedApts),
                                        messages = [],
                                        yesToggle = [],
                                        noToggle = [];

                                    // были выбраны те, которые требуют выбор других
                                    _.each(newAptIds, function (apt_id) {
                                        var check = $scope.apt_groups.getSelectionDeps(apt_id, newSelectedApts),
                                            msg = [];
                                        if (!check.ok) {
                                            msg.push('Показатель "{0}" зависит от других показателей:<br>'.format($scope.apt_names[apt_id]));
                                            _.each(check.dependents, function (d_apt_id) {
                                                msg.push('  - "{0}"<br>'.format($scope.apt_names[d_apt_id]));
                                            });
                                            msg.push('<br>Выбрать данные параметры исследования?<br>');

                                            messages.push(msg.join(''));
                                            Array.prototype.push.apply(yesToggle, check.dependents);
                                            noToggle.push(apt_id);
                                        }
                                    });
                                    // был снят выбор с тех, которые требуются для выбора других
                                    _.each(cancelledAptIds, function (apt_id) {
                                        var check = $scope.apt_groups.getUnselectionDeps(apt_id, newSelectedApts),
                                            msg = [];
                                        if (!check.ok) {
                                            msg.push('От показателя "{0}" зависят другие показатели:<br>'.format($scope.apt_names[apt_id]));
                                            _.each(check.dependents, function (d_apt_id) {
                                                msg.push('  - "{0}"<br>'.format($scope.apt_names[d_apt_id]));
                                            });
                                            msg.push('<br>Снять выбор с этих параметров исследования?<br>');

                                            messages.push(msg.join(''));
                                            Array.prototype.push.apply(yesToggle, check.dependents);
                                            noToggle.push(apt_id);
                                        }
                                    });

                                    if (messages.length) {
                                        MessageBox.question(
                                            'Внимание', messages.join('<br>')
                                        ).then(function () {
                                            _.each(yesToggle, function (apt_id) {
                                                $scope.assigned[apt_id].is_assigned = !$scope.assigned[apt_id].is_assigned;
                                            });
                                        }, function () {
                                            _.each(noToggle, function (apt_id) {
                                                $scope.assigned[apt_id].is_assigned = !$scope.assigned[apt_id].is_assigned;
                                            });
                                        })
                                    }
                                }
                            }, true);
                        }
                    });

                $scope.check_all_selected = function () {
                    return model.assignable.every(function (prop) {
                        var type_id = prop[0];
                        return $scope.assigned[type_id].is_assigned;
                    });
                };
                $scope.select_all = function () {
                    var enabled = !$scope.check_all_selected();
                    model.assignable.forEach(function (prop) {
                        var type_id = prop[0],
                            mandatory = prop[3];
                        $scope.assigned[type_id].is_assigned =  mandatory ? true : enabled;
                    });
                };
                $scope.price_available = function (prop) {
                    return prop.length > 2 && _.isNumber(prop[2]) && !_.isNaN(prop[2]);
                };
                $scope.get_price = function (prop) {
                    return prop[2];
                };
                $scope.filterItemLabTissueType = function () {
                    return function (item) {
                        return t_model.available_tissue_types.has(item.id);
                    }
                };
                $scope.testReasonRequired = function (prop) {
                    return prop[4];
                };
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-action-assignments.html',
                backdrop : 'static',
//                size: 'sm',
                controller: Controller
            });
            return instance.result.then(function () {
                model.props_data = t_model.props_data;
                model.planned_end_date = t_model.planned_end_date;
                model.selected_tissue_type = t_model.selected_tissue_type;
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
            <input class="form-control" type="text" ng-model="conditions.query" wm-slow-change="set_filter()" />\
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
            <button type="button" class="btn btn-default" ng-click="all_nodes_expanded.value=!all_nodes_expanded.value">\
            [[all_nodes_expanded.value ? \'Свернуть все узлы\' : \'Развернуть все узлы\']]</button>\
            <div class="ui-treeview treeview-striped">\
                <ul ng-repeat="root in tree.children">\
                    <li sf-treepeat="node in children of root">\
                        <a ng-click="create_action(node)" \
                           ng-if="!node.children.length" target="_blank">\
                            <div class="tree-label leaf">&nbsp;</div>\
                            [ [[node.code]] ] [[ node.name ]] <span class="text-danger" ng-bind="get_at_item_price(node.id)"></span>\
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
        <div class="modal-body modal-scrollable affix-container">\
            <div class="row">\
                <div class="col-md-6">\
                    <input class="form-control" type="text" ng-model="conditions.query" wm-slow-change="set_filter()" />\
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
                    <button type="button" class="btn btn-default" ng-click="all_nodes_expanded.value=!all_nodes_expanded.value">\
                    [[all_nodes_expanded.value ? \'Свернуть все узлы\' : \'Развернуть все узлы\']]</button>\
                    <div class="ui-treeview treeview-striped">\
                        <ul ng-repeat="root in tree.children">\
                            <li sf-treepeat="node in children of root">\
                                <a ng-click="add_prepared_action(node)" ng-if="!node.children.length" class="leaf">\
                                    <div class="tree-label leaf">&nbsp;</div>\
                                    [ [[node.code]] ] [[ node.name ]] <span class="text-danger" ng-bind="get_at_item_price(node.id)"></span>\
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
                <div class="col-md-6 modal-affix">\
                    <ul class="list-group">\
                        <li ng-repeat="action in prepared2create" class="list-group-item">\
                            <div class="row" ng-if="labTestsServiceErrorVisible(action)">\
                            <div class="col-md-12">\
                                <span class="text-danger">Не выбрано ни одного показателя исследования</span>\
                            </div>\
                            </div>\
                            <div class="row">\
                            <div class="col-md-8">\
                                <span ng-if="!action.assignable.length"><span ng-bind="action.type_name" class="rmargin10"></span></span>\
                                <span ng-if="action.assignable.length"><a ng-click="open_assignments(action)" ng-bind="action.type_name" class="rmargin10"></a></span>\
                                <span ng-if="action_has_price(action)" class="nowrap">Стоимость: <span class="text-danger" ng-bind="get_action_price(action)"></span> руб.</span>\
                            </div>\
                            <div class="col-md-4">\
                                <div class="pull-right">\
                                    <button class="btn-sm" checkbox-button="action.urgent">Срочно</button>\
                                    <button class="btn btn-danger btn-sm" ng-click="prepared2create.splice($index, 1)">\
                                        <i class="glyphicon glyphicon-trash"></i>\
                                    </button>\
                                </div>\
                            </div>\
                            </div>\
                            <hr style="margin-top: 7px; margin-bottom: 7px">\
                            <div class="row">\
                            <div class="col-md-8">\
                                <wm-datetime-as ng-model="action.planned_end_date" wm-validate="validate_direction_date"></wm-datetime-as>\
                            </div>\
                            <div class="col-md-4">\
                                <rb-select ref-book="rbTissueType" ng-model="action.selected_tissue_type"\
                                    custom-filter="filterItemLabTissueType(action)">\
                                </rb-select>\
                            </div>\
                            </div>\
                            <div class="form-group" ng-if="actionReasonRequired(action)">\
                                <label class="control-label">Обоснование <span class="text-danger">*</span></label>\
                                <textarea class="form-control" rows="1" ng-model="action.note"\
                                     ng-required="true" placeholder="Укажите обоснование для назначения"></textarea>\
                            </div>\
                        </li>\
                    </ul>\
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
                ng-disabled="labDirectionsForm.$invalid || !labTestsServicesSelected()">Создать направления</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-action-assignments.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">Назначаемые исследования</h4>\
        </div>\
        <div class="modal-body">\
            <ng-form name="testsForm">\
            <div class="row">\
                <div class="col-md-6" ng-if="date_required">\
                    <label for="ped">Дата/время назначения</label>\
                    <wm-datetime-as id="ped" ng-model="t_model.planned_end_date" ng-disabled="t_model.ped_disabled"></wm-datetime-as>\
                </div>\
                <div class="col-md-6" ng-if="t_model.tissue_type_visible">\
                    <label for="tissue_type">Тип биоматериала</label>\
                    <rb-select id="tissue_type" ref-book="rbTissueType" ng-model="t_model.selected_tissue_type"\
                        custom-filter="filterItemLabTissueType()" ng-required="true">\
                    </rb-select>\
                </div>\
            </div>\
            <div class="checkbox">\
                <label><input type="checkbox" ng-checked="check_all_selected()" ng-click="select_all()">Выбрать все</label>\
            </div>\
            <hr class="novmargin"/>\
            <div class="checkbox" ng-repeat="prop in model.assignable">\
                <label><input type="checkbox" ng-model="assigned[prop[0]].is_assigned" ng-disabled="prop[3]">[[ prop[1] ]]\
                    <span ng-if="price_available(prop)"><span class="text-danger lmargin20" ng-bind="get_price(prop)"></span> руб.</span></label>\
                <div class="row" ng-if="testReasonRequired(prop)">\
                    <div class="col-md-10">\
                    <textarea class="form-control lmargin20" rows="1" ng-model="assigned[prop[0]].note"\
                         ng-required="assigned[prop[0]].is_assigned" placeholder="Укажите обоснование для назначения"></textarea>\
                    </div>\
                </div>\
            </div>\
            </ng-form>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            <button type="button" class="btn btn-success" ng-disabled="testsForm.$invalid"\
                ng-click="$close()">Подтвердить</button>\
        </div>')
}])
;