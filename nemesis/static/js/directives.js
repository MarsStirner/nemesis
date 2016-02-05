'use strict';

angular.module('WebMis20.directives', ['ui.bootstrap', 'ui.select', 'ngSanitize', 'WebMis20.directives.goodies']);

angular.module('WebMis20.directives')
    .directive('rbSelect', ['$compile', function($compile) {
        return {
            restrict: 'E',
            require: '^ngModel',
            scope: true,
            link: function (scope, element, attrs, ctrl) {
                var _id = attrs.id,
                    name = attrs.name,
                    theme = attrs.theme || "select2",
                    ngDisabled = attrs.ngDisabled,
                    ngRequired = attrs.ngRequired,
                    placeholder = attrs.placeholder,
                    ngModel = attrs.ngModel,
                    refBook = attrs.refBook,
                    customFilter = attrs.customFilter,
                    extraFilter = attrs.extraFilter,
                    getName = attrs.customName ? scope.$eval(attrs.customName) : function (selected) {
                        return selected ? selected.name : undefined;
                    },
                    orderBy = attrs.orderBy,
                    ngChange = attrs.ngChange,
                    allowClear = Boolean(attrs.allowClear),
                    autofocus = attrs.autofocus,
                    limitTo = attrs.limitTo || 10;
                scope.getName = getName;
                if (!ngModel) throw new Error('<rb-select> must have ng-model attribute');
                if (!refBook) throw new Error('<rb-select> must have rb attribute');
                var uiSelect = $('<ui-select></ui-select>');
                var uiSelectMatch = $(
                    '<ui-select-match allow-clear="{0}">[[getName($select.selected)]]</ui-select-match>'.format(
                        allowClear
                    )
                );
                var uiSelectChoices = $(
                    '<ui-select-choices repeat="item in $refBook.objects | {0}filter: $select.search {1} {2} | limitTo:{3} track by item.id">\
                        <div ng-bind-html="getName(item) | highlight: $select.search"></div>\
                    </ui-select-choices>'
                    .format(
                        extraFilter ? (extraFilter + ' | '): '',
                        customFilter ? ('| filter: ' + customFilter): '',
                        orderBy ? ('| orderBy: ' + orderBy) : '',
                        limitTo
                    )
                );
                if (_id) uiSelect.attr('id', _id);
                if (name) uiSelect.attr('name', name);
                if (theme) uiSelect.attr('theme', theme);
                if (ngDisabled) uiSelect.attr('ng-disabled', ngDisabled);
                if (ngRequired) uiSelect.attr('ng-required', ngRequired);
                if (ngModel) uiSelect.attr('ng-model', ngModel);
                if (placeholder) uiSelectMatch.attr('placeholder', placeholder);
                if (refBook) uiSelect.attr('ref-book', refBook);
                if (ngChange) uiSelect.attr('ng-change', ngChange);
                if (autofocus) uiSelect.attr('autofocus', '');
                uiSelect.append(uiSelectMatch);
                uiSelect.append(uiSelectChoices);
                $(element).replaceWith(uiSelect);
                $compile(uiSelect)(scope);
            }
        };
    }])
    .directive('wmPersonSelect', ['$compile', '$http', function ($compile, $http) {
        return {
            restrict: 'E',
            scope: true,
            require: 'ngModel',
            link: function (scope, element, attrs) {
                scope.persons = [];
                scope.refresh_choices = function (query) {
                    if (!query) { return; }
                    $http.get(url_api_search_persons, {
                        params: {
                            q: query,
                            only_doctors: scope.$eval(attrs.onlyDoctors || "true") ? undefined : false
                        }
                    }).success(function (data) {
                        scope.persons = data.result;
                    });
                };

                var template = '\
    <ui-select {0} {1} theme="{2}" autocomplete="off" ng-model="{3}" {4} {5} {6}>\
        <ui-select-match placeholder="{7}"><span ng-bind="$select.selected.full_name || $select.selected.short_name"></span></ui-select-match>\
        <ui-select-choices refresh="refresh_choices($select.search)" repeat="person in persons | filter: $select.search">\
            <span ng-bind-html="person.short_name | highlight: $select.search"></span>\
        </ui-select-choices>\
    </ui-select>'.format(
                    attrs.id ? 'id="{0}"'.format(attrs.id) : '',
                    attrs.name ? 'name="{0}"'.format(attrs.name) : '',
                    attrs.theme ? attrs.theme : 'select2',
                    attrs.ngModel,
                    attrs.ngDisabled ? 'ng-disabled="{0}"'.format(attrs.ngDisabled) : '', // 4
                    attrs.ngRequired ? 'ng-required="{0}"'.format(attrs.ngRequired) : '', // 5
                    attrs.ngChange ? 'ng-change="{0}"'.format(attrs.ngChange) : '', // 6
                    attrs.placeholder ? attrs.placeholder : 'не выбрано' // 7
                );
                var elm = $compile(template)(scope);
                element.replaceWith(elm);
            }
        }
    }])
    .directive('bakLabView', [function () {
        return {
            restrict: 'E',
            scope: {
                bak_model: '=model'
            },
            link: function (scope, elm, attrs) {
                scope.get_row_num = function (organism) {
                    return organism.sens_values.length || 1;
                };
            },
            template:
    '<legend class="vmargin10">Результаты БАК исследования</legend>\
     <div class="row">\
        <div class="col-md-6">\
            <label>Подписавший врач:&nbsp;</label>\
            <span>[[bak_model.doctor ? \'{0}, {1}\'.format(bak_model.doctor.name, bak_model.doctor.speciality.name) : \'\']]</span>\
        </div>\
        <div class="col-md-6">\
            <label>Код Лис:&nbsp;</label><span>[[bak_model.code_lis]]</span>\
        </div>\
     </div>\
     <div class="row">\
        <div class="col-md-6">\
            <label>Завершено:&nbsp;</label><span>[[bak_model.final ? "Да" : "Нет"]]</span>\
        </div>\
        <div class="col-md-6">\
            <label>Дефекты БМ:&nbsp;</label><span>[[bak_model.defects]]</span>\
        </div>\
     </div>\
     <table class="table table-condensed table-bordered table-bak">\
        <thead ng-if="bak_model.organisms.length">\
            <tr>\
                <th rowspan="2">Микроорганизм</th>\
                <th rowspan="2">Концентрация</th>\
                <th colspan="3">Чувствительность к антибиотикам</th>\
            </tr>\
            <tr>\
                <th>Антибиотик</th>\
                <th>Концентрация</th>\
                <th>Чувствительность</th>\
            </tr>\
        </thead>\
        <tbody ng-repeat="organism in bak_model.organisms" ng-class="{\'bg-muted\': hover}" ng-mouseenter="hover=true" ng-mouseleave="hover=false">\
            <tr>\
                <td rowspan="[[get_row_num(organism)]]">[[organism.microorganism]]</td>\
                <td rowspan="[[get_row_num(organism)]]">[[organism.concentration]]</td>\
                <td>[[organism.sens_values[0].antibiotic]]</td>\
                <td>[[organism.sens_values[0].mic]]</td>\
                <td>[[organism.sens_values[0].activity]]</td>\
            </tr>\
            <tr ng-repeat="sens in organism.sens_values.slice(1)">\
                <td>[[sens.antibiotic]]</td>\
                <td>[[sens.mic]]</td>\
                <td>[[sens.activity]]</td>\
            </tr>\
        </tbody>\
        <tbody ng-if="bak_model.comments.length">\
            <tr>\
                <th colspan="5">Комментарии</th>\
            </tr>\
            <tr ng-repeat="comment in bak_model.comments" ng-class="{\'bg-muted\': hover}" ng-mouseenter="hover=true" ng-mouseleave="hover=false">\
                <td colspan="5">[[comment.text]]</td>\
            </tr>\
        </tbody>\
     </table>'
        };
    }])
    .directive('medicationPrescriptions', ['$modal', 'CurrentUser', 'PharmExpertIntegration', function ($modal, CurrentUser, PharmExpertIntegration) {
        function get_rls_name (rls) {
            if (!rls) { return '-' }
            else if (rls.dosage.unit) {
                return '{0} ({1} {2}; {3}; {4})'.format(
                    rls.trade_name,
                    rls.dosage.value,
                    rls.dosage.unit.short_name,
                    rls.form,
                    rls.packing
                )
            } else {
                return '{0} ({1}; {2})'.format(
                    rls.trade_name,
                    rls.form,
                    rls.packing
                )
            }
        }
        function controller ($scope, $modalInstance, $http, model) {
            $scope.model = model;
            $scope.get_rls_name = get_rls_name;
            $scope.get_rls = function (query){
                if (!query) return;
                return $http.get(url_rls_search, {
                    params: {
                        q: query,
                        short: true,
                        limit: 20
                    }
                })
                .then(function (res) {
                    return $scope.rls_list = res.data.result;
                });
            };
            $scope.model_incomplete = function () {
                return !model.rls
                    || !model.dose || !model.dose.value || !model.dose.unit
                    || !model.frequency || !model.frequency.value || !model.frequency.unit
                    || !model.duration || !model.duration.value || !model.duration.unit
                    || !model.method
            }
        }
        function edit_dialog (model) {
            var deferred = $modal.open({
                templateUrl: '/WebMis20/modal-prescription-edit.html',
                controller: controller,
                size: 'lg',
                resolve: {
                    model: function () {
                        return model;
                    }
                }
            });
            return deferred.result;
        }
        function cancel_dialog (model) {
            var deferred = $modal.open({
                templateUrl: '/WebMis20/modal-prescription-cancel.html',
                controller: controller,
                size: 'lg',
                resolve: {
                    model: function () {
                        return model;
                    }
                }
            });
            return deferred.result;
        }
        return {
            restrict: 'E',
            scope: {
                model: '=',
                action: '='
            },
            link: function (scope, element, attrs) {
                scope.edit = function (p) {
                    edit_dialog(_.deepCopy(p)).then(function (model) {
                        angular.extend(p, model);
                        checkPE();
                    })
                };
                scope.remove = function (p) {
                    if (!p.id) {
                        p.deleted = true;
                        checkPE();
                    } else {
                        cancel_dialog(_.deepCopy(p)).then(function (model) {
                            angular.extend(p, model);
                            p.deleted = true;
                            checkPE();
                        })
                    }
                };
                scope.add = function () {
                    edit_dialog({}).then(function (model) {
                        scope.model.push(model);
                        checkPE();
                    })
                };
                scope.restore = function (p) {
                    delete p.deleted;
                    checkPE();
                };
                scope.get_rls_name = get_rls_name;
                scope.canEdit = function (p) {
                    var is_editor = [
                        safe_traverse(p, ['related', 'action_person_id'])
                    ].has(CurrentUser.id);
                    return (is_editor && !p.closed) || !p.id;
                };
                scope.canRemove = function (p) {
                    var cancellers = [
                        safe_traverse(p, ['related', 'action_person_id']),
                        safe_traverse(p, ['related', 'action_set_person_id']),
                        safe_traverse(p, ['related', 'event_exec_person_id'])
                    ],
                        is_canceller = cancellers.has(CurrentUser.id);
                    return (is_canceller && !p.closed) || !p.id
                };
                scope.canAdd = function () {
                    return safe_traverse(scope, ['action', 'person', 'id']) == CurrentUser.id
                };
                scope.canCheck = function () {
                    return PharmExpertIntegration.enabled() && pharmExpertResult.url;
                };
                scope.btnCheckClass = function () {
                    if (pharmExpertResult.value_max > 1) return 'btn-danger';
                    if (pharmExpertResult.value_max > 0) return 'btn-warning';
                    return 'btn-default';
                };
                scope.check = function () {
                    PharmExpertIntegration.modal(pharmExpertResult);
                };
                var pharmExpertResult = {};
                var checkPE = function () {
                    var data = prepareDataPharmExpert();
                    PharmExpertIntegration.check(data).then(
                        function (result) {
                            _.extend(pharmExpertResult, {
                                value_max: parseInt(result.value_max),
                                url: result.url
                            });
                        }
                    )
                };
                var prepareDataPharmExpert = function () {
                    var client = scope.action.client;
                    return {
                        medicaments: _.chain(scope.model)
                            .filter(function (record) { return ! record.deleted })
                            .map(function makeMedicineFE(record) {
                                return {
                                    name: record.rls.trade_name,
                                    data1: scope.action.beg_date, // MAY GOD HAVE MERCY ON THOSE POOR BUZZARDS
                                    // data2: ,
                                    dosage: {
                                        // лекарственная форма
                                        formulation: {
                                            name: record.rls.form,
                                            value: record.dose.value,
                                            unit: record.dose.unit.code
                                        },
                                        // способ применения
                                        dosing_formulation: {
                                            name: record.method.name
                                        },
                                        // частота
                                        dosage_frequency: '{0} раз в {1}'.format(record.frequency.value, record.frequency.unit.name),
                                        // длительность
                                        dosage_duration: '{0} {1}'.format(record.duration.value, record.duration.unit.name)
                                    },
                                    patient: 'hitsl.mis:{0}'.format(client.id)
                                }
                            })
                            .makeObject(function (item, index, object) { return index })
                            .value()
                        ,
                        user_info: {
                            age_days: String(client.age_tuple[0]),
                            sex: (client.sex_raw == 2)?('f'):('m')
                        }
                    }
                };
                checkPE();
            },
            templateUrl: '/WebMis20/prescription-edit.html'
        }
    }])
    .run(['$templateCache', function ($templateCache) {
        $templateCache.put(
            '/WebMis20/prescription-edit.html',
            '<table class="table">\
                <thead>\
                <tr>\
                    <th>Препарат</th>\
                    <th>Доза</th>\
                    <th>Частота</th>\
                    <th>Длительность</th>\
                    <th>Путь введения</th>\
                    <th colspan="2">Примечание</th>\
                </tr>\
                </thead>\
                <tbody ng-repeat="p in model">\
                    <tr ng-if="p.deleted">\
                        <td colspan="7" class="text-center"><a href="#" ng-click="restore(p)">Восстановить</a></td>\
                    </tr>\
                    <tr ng-if="!p.deleted">\
                        <td>[[ get_rls_name(p.rls) ]]</td>\
                        <td class="text-nowrap">[[ p.dose.value ]] [[ p.dose.unit.short_name ]]</td>\
                        <td class="text-nowrap">[[ p.frequency.value ]] раз в [[ p.frequency.unit.short_name ]]</td>\
                        <td class="text-nowrap">[[ p.duration.value ]] [[ p.duration.unit.short_name ]]</td>\
                        <td>[[ p.method.name ]]</td>\
                        <td>[[ p.note ]]</td>\
                        <td class="nowrap">\
                            <div class="pull-right">\
                                <button class="btn btn-primary" ng-click="edit(p)" ng-if="canEdit(p)"><i class="fa fa-pencil"></i></button>\
                                <button class="btn btn-danger" ng-click="remove(p)" ng-if="canRemove(p)"><i class="fa fa-trash"></i></button>\
                            </div>\
                        </td>\
                    </tr>\
                    <tr ng-if="p.status.id >= 5">\
                        <td colspan="7">\
                            <div class="pull-right">\
                                Отменено <span class="text-bold">[[ p.modify_person.name ]]</span> @ <span class="text-bold">[[ p.modify_datetime | asDateTime ]]</span>\
                            </div>\
                        </td>\
                    </tr>\
                </tbody>\
                <tbody ng-if="canAdd() || canCheck()">\
                    <tr>\
                        <td colspan="6">&nbsp;</td>\
                        <td class="text-right">\
                            <button class="btn" \
                                ng-class="btnCheckClass()" \
                                ng-if="canCheck()" ng-click="check()"><i class="fa fa-check"></i></button>\
                            <button class="btn btn-success" ng-if="canAdd()" ng-click="add()"><i class="fa fa-plus"></i></button>\
                        </td>\
                    </tr>\
                </tbody>\
            </table>'
        );
        $templateCache.put(
            '/WebMis20/modal-prescription-edit.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title" id="myModalLabel">Назначение препарата</h4>\
</div>\
<div class="modal-body">\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Наименование препарата</label></div>\
            <div class="col-md-8">\
                <ui-select theme="select2" ng-model="model.rls">\
                    <ui-select-match>[[ get_rls_name($select.selected) ]]</ui-select-match>\
                    <ui-select-choices repeat="item in rls_list | filter: $select.search | orderBy:\'trade_name\'"\
                                       refresh="get_rls($select.search)">\
                        <div ng-bind-html="get_rls_name(item) | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
        </div>\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Доза</label></div>\
            <div class="col-md-4"><input class="form-control" ng-model="model.dose.value" valid-number></div>\
            <div class="col-md-4">\
                <ui-select theme="select2" ng-model="model.dose.unit">\
                    <ui-select-match>[[ $select.selected.short_name ]]</ui-select-match>\
                    <ui-select-choices repeat="item in model.rls.unit_variants | filter: $select.search | orderBy:\'trade_name\'">\
                        <div ng-bind-html="item.short_name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
        </div>\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Частота</label></div>\
            <div class="col-md-3"><input class="form-control" ng-model="model.frequency.value" valid-number></div>\
            <div class="col-md-1">раз в</div>\
            <div class="col-md-4"><rb-select ref-book="rbUnitsGroup/time" ng-model="model.frequency.unit"></rb-select></div>\
        </div>\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Длительность</label></div>\
            <div class="col-md-4"><input class="form-control" ng-model="model.duration.value" valid-number></div>\
            <div class="col-md-4"><rb-select ref-book="rbUnitsGroup/time" ng-model="model.duration.unit"></rb-select></div>\
        </div>\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Путь введения</label></div>\
            <div class="col-md-8"><rb-select ref-book="rbMethodOfAdministration" ng-model="model.method"></rb-select></div>\
        </div>\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Примечание</label></div>\
            <div class="col-md-8"><input class="form-control" ng-model="model.note"></div>\
        </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-success" ng-disabled="model_incomplete()" ng-click="$close(model)">Сохранить</button>\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отмена</button>\
</div>'
        );
        $templateCache.put(
            '/WebMis20/modal-prescription-cancel.html',
            '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title" id="myModalLabel">Отмена назначение препарата</h4>\
</div>\
<div class="modal-body">\
        <div class="row vmargin10">\
            <div class="col-md-4"><label>Причина отмены</label></div>\
            <div class="col-md-8">\
                <input class="form-control" ng-model="model.reason">\
            </div>\
        </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-success" ng-disabled="!model.reason" ng-click="$close(model)">Сохранить</button>\
    <button type="button" class="btn btn-default" ng-click="$dismiss(\'cancel\')">Отмена</button>\
</div>'
        );
    }])
    .directive('uiAlertList', [function () {
        return {
            restrict: 'A',
            template: function (element, attrs) {
                return '<alert ng-repeat="alert in {0}" type="alert.type" close="alerts.splice(index, 1)">\
                        <span ng-bind="alert.text"></span> <span ng-if="alert.code">[[ [alert.code] ]]</span>\
                        <span ng-if="alert.data.detailed_msg">\
                            <a href="javascript:void(0);"  ng-click="show_details = !show_details">\
                                [[show_details ? "[Скрыть]" : "[Подробнее]"]]\
                            </a>\
                            <span ng-show="show_details">[[alert.data.detailed_msg]]: [[alert.data.err_msg]]</span>\
                        </span>\
                    </alert>'.format(attrs.uiAlertList)
            }
        }
    }])
    .service('PrintingDialog', ['$modal', function ($modal) {
        var ModalPrintDialogController = function ($scope, $modalInstance, ps, context_extender, meta_values, fast_print) {
            $scope.aux = aux;
            $scope.page = 0;
            $scope.ps = ps;
            $scope.selected_templates = [];
            $scope.mega_model = {};
            $scope.toggle_select_template = function (template) {
                if ($scope.selected_templates.has(template)) {
                    $scope.selected_templates.remove(template);
                    $scope.mega_model[template.id] = undefined;
                } else {
                    $scope.selected_templates.push(template);
                    make_model(template);
                }
                $scope.selected_templates.sort(function (left, right) {
                    return (left.code < right.code) ? -1 : (left.code > right.code ? 1 : 0)
                });
            };
            $scope.select_all_templates = function () {
                if ($scope.selected_templates.length == ps.templates.length) {
                    $scope.selected_templates = [];
                    $scope.mega_model = {};
                } else {
                    $scope.selected_templates = ps.templates.map(function (template) {
                        if (!$scope.selected_templates.has(template)) {
                            make_model(template)
                        }
                        return template;
                    })
                }
            };
            $scope.btn_next = function () {
                $scope.page = 1;
            };
            $scope.btn_prev = function () {
                $scope.mega_model = {};
                $scope.page = 0;
            };
            function prepare_data () {
                return $scope.selected_templates.map(function (template) {
                    var context = {};
                    template.meta.map(function (meta) {
                        var name = meta.name;
                        var typeName = meta['type'];
                        var value = $scope.mega_model[template.id][name];
                        if (typeName == 'Integer')
                            context[name] = parseInt(value);
                        else if (typeName == 'Float')
                            context[name] = parseFloat(value);
                        else if (typeName == 'Boolean')
                            context[name] = Boolean(value);
                        else if (['Organisation', 'OrgStructure', 'Person', 'Service'].has(typeName))
                            context[name] = value ? value.id : null;
                        else if (typeName == 'SpecialVariable') {
                            if (!('special_variables' in context))
                                context['special_variables']={};
                            context['special_variables'][name] = meta['arguments'];
                        }

                        else context[name] = value
                    });
                    return {
                        template_id: template.id,
                        context: angular.extend(context, context_extender)
                    }
                })
            }
            function make_model (template) {
                if (template.meta) {
                    var desc = $scope.mega_model[template.id] = {};
                    template.meta.map(function (variable) {
                        desc[variable.name] = variable.default || (
                            meta_values !== undefined ? meta_values[variable.name] : undefined
                        );
                    })
                }
            }
            $scope.print_separated = function () {
                ps.print_template(prepare_data(), true).then(
                    function () {
                        angular.noop();
                    },
                    function () {
                        $scope.$close();
                    }
                );
            };
            $scope.print_compact = function () {
                ps.print_template(prepare_data(), false).then(
                    function () {
                        angular.noop();
                    },
                    function () {
                        $scope.$close();
                    }
                );
            };
            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
            $scope.instant_print = function () {
                return ! $scope.selected_templates.filter(function (template) {
                    return Boolean(template.meta.length)
                }).length;
            };
            $scope.can_print = function () {
                return $scope.selected_templates.length > 0;
            };
            $scope.template_has_meta = function (template) {
                return Boolean(template.meta.length);
            };

            if (fast_print) {
                $scope.select_all_templates();
                var dont_need_meta = $scope.instant_print(),
                    no_template_choice = $scope.selected_templates.length === 1;
                if (dont_need_meta && no_template_choice) {
                    $scope.print_separated();
                } else {
                    $scope.page = no_template_choice ? (dont_need_meta ? 0 : 1) : 0;
                }
            }
        };

        return {
            open: function (ps, context_extender, meta_values, fast_print) {
                return $modal.open({
                    templateUrl: '/WebMis20/modal-print-dialog.html',
                    controller: ModalPrintDialogController,
                    size: 'lg',
                    resolve: {
                        ps: function () {
                            return ps;
                        },
                        context_extender: function () {
                            return context_extender
                        },
                        meta_values: function () {
                            return meta_values;
                        },
                        fast_print: function () {
                            return fast_print;
                        }
                    }
                });
            }
        }
    }])
    .run(['$templateCache', function ($templateCache) {
        $templateCache.put('/WebMis20/modal-print-dialog.html',
'<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="cancel()">&times;</button>\
    <h4 class="modal-title" id="myModalLabel">Печать документов</h4>\
</div>\
<div class="modal-body">\
    <table ng-show="page == 0" class="table table-condensed modal-body">\
        <thead>\
            <tr>\
                <th>\
                    <input type="checkbox" ng-checked="ps.templates.length == selected_templates.length" ng-click="select_all_templates()">\
                </th>\
                <th>Наименование</th>\
            </tr>\
        </thead>\
        <tbody>\
            <tr ng-repeat="template in ps.templates">\
                <td>\
                <input type="checkbox" ng-checked="selected_templates.has(template)" id="template-id-[[template.id]]" ng-click="toggle_select_template(template)">\
                </td>\
                <td>\
                    <label for="template-id-[[template.id]]" ng-bind="template.name"></label>\
                </td>\
            </tr>\
        </tbody>\
    </table>\
    <div ng-show="page == 1">\
        <form name="printing_meta">\
            <div ng-repeat="template in selected_templates | filter:template_has_meta">\
                <h4 class="marginal" ng-bind="template.name"></h4>\
                <div class="row marginal" ng-repeat="var_meta in template.meta">\
                    <div class="col-md-3">\
                        <label ng-bind="var_meta.title"></label>\
                    </div>\
                    <div class="col-md-9" ui-print-variable meta="var_meta" model="mega_model[template.id][var_meta.name]">\
                    </div>\
                </div>\
            </div>\
        </form>\
    </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-success" ng-click="btn_next()" ng-if="page == 0 && !instant_print()">\
        Далее &gt;&gt;</button>\
    <button type="button" class="btn btn-default" ng-click="btn_prev()" ng-if="page == 1 && !instant_print()">\
        &lt;&lt; Назад</button>\
    <button type="button" class="btn btn-primary" ng-click="print_separated()" ng-if="page == 1 || instant_print()"\
        ng-disabled="printing_meta.$invalid">Печать</button>\
    <button type="button" class="btn btn-primary" ng-click="print_compact()" ng-if="page == 1 || instant_print()"\
        ng-disabled="printing_meta.$invalid">Печать компактно</button>\
    <button type="button" class="btn btn-default" ng-click="cancel()">Отмена</button>\
</div>')
    }])
    .directive('uiPrintButton', ['PrintingDialog', 'MessageBox', function (PrintingDialog, MessageBox) {
        return {
            restrict: 'E',
            replace: true,
            template: function(el, attributes) {
                var btnText = el.html();
                return '<button class="btn btn-default" ng-click="print_templates()" title="Печать" ng-disabled="disabled()">\
                    <i class="glyphicon glyphicon-print"></i>\
                    <i class="glyphicon glyphicon-remove text-danger" ng-show="disabled()"></i>' + btnText +'</button>'},
            scope: {
                $ps: '=ps',
                beforePrint: '&?',
                lazyLoadContext: '@?',
                fastPrint: '=?'
            },
            link: function (scope, element, attrs) {
                var resolver_call = attrs.resolve;
                if (!attrs.beforePrint) {
                    scope.beforePrint = null;
                }
                scope.disabled = function () {
                    return !scope.$ps.is_available();
                };
                scope.print_templates = function() {
                    if (scope.beforePrint) {
                        scope.beforePrint().then(function () {
                            // чтобы диалог печати не вызывался до обновления страницы после сохранения действия
                            if (!window.sessionStorage.getItem('open_action_print_dlg')) {
                                scope.open_print_window();
                            }
                        });
                    } else {
                        scope.open_print_window();
                    }
                };
                scope.open_print_window = function () {
                    if (!scope.$ps.is_loaded()) {
                        scope.$ps.set_context(scope.lazyLoadContext)
                            .then(function () {
                                PrintingDialog.open(scope.$ps, scope.$parent.$eval(resolver_call), undefined,
                                    scope.fastPrint);
                            }, function () {
                                MessageBox.error(
                                    'Печать недоступна',
                                    'Сервис печати недоступен. Свяжитесь с администратором.'
                                );
                            });
                    } else {
                        PrintingDialog.open(scope.$ps, scope.$parent.$eval(resolver_call), undefined,
                                    scope.fastPrint);
                    }
                };
            }
        }
    }])
    .directive('refBook', ['RefBookService', function (RefBookService) {
        return {
            restrict: 'A',
            link: function (scope, elem, attrs) {
                var isolatedScope = elem.isolateScope();
                if (isolatedScope){
                    isolatedScope.$refBook = RefBookService.get(attrs.refBook);
                } else {
                scope.$refBook = RefBookService.get(attrs.refBook);
                }
            }
        }
    }])
    .directive("refbookCheckbox", [
        '$window', function($window) {
          return {
            restrict: "A",
            scope: {
              disabled: '=ngDisabled',
              required: '=',
              errors: '=',
              inline: '='
            },
            require: '?ngModel',
            replace: true,
            template: function(el, attrs) {
              var itemTpl, template;
              itemTpl = el.html() || 'template me: {{item | json}}';
              return template = "<div class='fs-racheck fs-checkbox' ng-class=\"{disabled: disabled, enabled: !disabled}\">\n  <div ng-repeat='item in $refBook.objects'>\n    <a class=\"fs-racheck-item\"\n       href='javascript:void(0)'\n       ng-disabled=\"disabled\"\n       ng-click=\"toggle(item)\"\n       fs-space='toggle(item)'>\n      <span class=\"fs-check-outer\"><span ng-show=\"isSelected(item)\" class=\"fs-check-inner\"></span></span>\n      " + itemTpl + "\n    </a>\n  </div>\n</div>";
            },
            controller: function($scope, $element, $attrs) {
              $scope.toggle = function(item) {
                if ($scope.disabled) {
                  return;
                }
                if (!$scope.isSelected(item)) {
                  $scope.selectedItems.push(item);
                } else {
                  $scope.selectedItems.splice(indexOf($scope.selectedItems, item), 1);
                }
                return false;
              };
              $scope.isSelected = function(item) {
                return indexOf($scope.selectedItems, item) > -1;
              };
              $scope.invalid = function() {
                return ($scope.errors != null) && $scope.errors.length > 0;
              };
              return $scope.selectedItems = [];
            },
            link: function(scope, element, attrs, ngModelCtrl, transcludeFn) {
              var setViewValue;
              if (ngModelCtrl) {
                setViewValue = function(newValue, oldValue) {
                  if (!angular.equals(newValue, oldValue)) {
                    var new_value = scope.selectedItems.length ? scope.selectedItems : undefined;
                    return ngModelCtrl.$setViewValue(new_value);
                  }
                };
                scope.$watch('selectedItems', setViewValue, true);
                return ngModelCtrl.$render = function() {
                  if (!scope.disabled) {
                    return scope.selectedItems = ngModelCtrl.$viewValue || [];
                  }
                };
              }
            }
          };
        }
      ])
    .directive("refbookMultiselect", [
        '$window', function($window) {
          return {
            restrict: "A",
            scope: {
              disabled: '=ngDisabled',
              freetext: '@',
              "class": '@'
            },
            require: '?ngModel',
            replace: true,
            template: function(el, attributes) {
              var defaultItemTpl, itemTpl;
              defaultItemTpl = "{{ item }}";
              itemTpl = el.html() || defaultItemTpl;
              return "<div class='fs-multiselect fs-widget-root' ng-class='{ \"fs-with-selected-items\": selectedItems.length > 0 }'>\n  <div class='fs-multiselect-wrapper'>\n    <div class=\"fs-multiselect-selected-items\" ng-if=\"selectedItems.length > 0\">\n      <a ng-repeat='item in selectedItems' class=\"btn\" ng-click=\"unselectItem(item)\" ng-disabled=\"disabled\">\n        " + itemTpl + "\n        <span class=\"glyphicon glyphicon-remove\" ></span>\n      </a>\n    </div>\n\n    <input ng-keydown=\"onkeys($event)\"\n           fs-null-form\n           ng-disabled=\"disabled\"\n           fs-input\n           fs-hold-focus\n           fs-on-focus=\"active = true\"\n           fs-on-blur=\"onBlur()\"\n           fs-blur-when=\"!active\"\n           fs-down='listInterface.move(1)'\n           fs-up='listInterface.move(-1)'\n           fs-pgup='listInterface.move(-11)'\n           fs-pgdown='listInterface.move(11)'\n           fs-enter='onEnter()'\n           fs-esc='active = false'\n           class=\"form-control\"\n           type=\"text\"\n           placeholder=\"{{ placeholder }}\"\n           ng-model=\"search\" />\n\n    <div ng-if=\"active && dropdownItems.length > 0\" class=\"open\">\n      <div fs-list items=\"dropdownItems\">\n        " + itemTpl + "\n      </div>\n    </div>\n  </div>\n</div>";
            },
            controller: function($scope, $element, $attrs, $filter) {
              $scope.limit = parseInt($attrs.limit) || 25;
              $scope.placeholder = $attrs.placeholder;
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
                allItems = $scope.dynamicItems();
                if ($scope.$refBook){
                     allItems = allItems.concat($scope.$refBook.objects)
                }
                return $scope.dropdownItems = limitFilter(
                    searchFilter(
                        excludeFilter(
                            allItems,
                            $scope.selectedItems),
                        $scope.search),
                    $scope.limit);
              };
              $scope.selectItem = function(item) {
                if ((item != null) && indexOf($scope.selectedItems, item) === -1) {
                  $scope.selectedItems = $scope.selectedItems.concat([item]);
                }
                return $scope.search = '';
              };
              $scope.unselectItem = function(item) {
                var index;
                index = indexOf($scope.selectedItems, item);
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
              $scope.$watchCollection('$refBook', function() {
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
        }
      ])
    .directive("refbookRadio", [
    '$window', function($window) {
      return {
        restrict: "A",
        scope: {
          required: '=',
          disabled: '=ngDisabled',
          inline: '=',
          keyAttr: '@',
          valueAttr: '@'
        },
        require: '?ngModel',
        template: function(el, attrs) {
          var itemTpl, name, template;
          itemTpl = el.html() || '{{item.label}}';
          name = "fsRadio_" + "{{item.code}}";
          return template = "<div class='fs-widget-root fs-radio fs-racheck' ng-class=\"{disabled: disabled, enabled: !disabled}\">\n  <div class=\"fs-radio-item\"\n     ng-repeat=\"item in $refBook.objects\" >\n    <input\n     fs-null-form\n     type=\"radio\"\n     ng-model=\"$parent.selectedItem\"\n     name=\"" + name + "\"\n     ng-value=\"item\"\n     ng-disabled=\"disabled\"\n     id=\"" + name + "_[[$index]]\" />\n\n    <label for=\"" + name + "_[[$index]]\">\n      <span class='fs-radio-btn'><span></span></span>\n\n      " + itemTpl + "\n    </label>\n  </div>\n</div>";
        },
        link: function(scope, element, attrs, ngModelCtrl, transcludeFn) {
          if (ngModelCtrl) {
            scope.$watch('selectedItem', function(newValue, oldValue) {
              if (!angular.equals(newValue, oldValue)) {
                return ngModelCtrl.$setViewValue(scope.selectedItem);
              }
            });
            scope.$watchCollection('$refBook.objects', function(newValue, oldValue) {
                if (!angular.equals(newValue, oldValue)) {
                    var index = indexOf(scope.$refBook.objects, ngModelCtrl.$modelValue);
                    return scope.selectedItem = index>=0 ? scope.$refBook.objects[index] : ngModelCtrl.$modelValue;
                }
            });
            return ngModelCtrl.$render = function() {
                if(scope.$refBook){
                    var index = indexOf(scope.$refBook.objects, ngModelCtrl.$modelValue);
                    return scope.selectedItem = index>=0 ? scope.$refBook.objects[index] : ngModelCtrl.$modelValue;
                } else {
                    return scope.selectedItem = ngModelCtrl.$modelValue;
                }
            };
          }
        }
      };
    }
    ])
    .directive('uiPrintVariable', ['$compile', 'RefBookService', function ($compile, RefBookService) {
        var ui_select_template =
            '<div fs-select="" items="$refBook.objects" ng-required="true" ng-model="model" class="validatable">[[item.name]]</div>';
        var templates = {
            Integer: '<input ng-required="true" class="validatable form-control" type="text" ng-pattern="/^([1-9]\\d*|0)$/" ng-model="model"></input>',
            String:  '<input ng-required="true" class="validatable form-control" type="text" ng-model="model"></input>',
            Float:   '<input ng-required="true" class="validatable form-control" type="text" ng-pattern="/^([1-9]\\d*|0)(.\\d+)?$/" ng-model="model"></input>',
            Boolean:
                '<div class="fs-checkbox fs-racheck">\
                    <a class="fs-racheck-item" href="javascript:void(0)" ng-click="model = !model" fs-space="model = !model">\
                <span class="fs-check-outer"><span ng-show="model" class="fs-check-inner"></span></span>[[ metadata.title ]]</a></div>',
            Date:    '<div fs-date ng-required="true" ng-model="model" class="validatable"></div>',
            Time:    '<div fs-time ng-required="true" ng-model="model" class="validatable"></div>',
            List:    '<div fs-select items="metadata.arguments" ng-model="model" ng-required="true" class="validatable">[[ item ]]</div>',
            Multilist: '<div fs-checkbox items="metadata.arguments" ng-model="model" class="validatable">[[ item ]]</div>',
            RefBook: ui_select_template,
            Organisation:
                '<div fs-select="" items="$refBook.objects" ng-required="true" ng-model="model" class="validatable">[[item.short_name]]</div>',
            OrgStructure: ui_select_template,
            Person:  ui_select_template,
            Service: ui_select_template,
            MKB: '<ui-mkb ng-model="model"></ui-mkb>',
            SpecialVariable: 'Special Variable'
        };
        return {
            restrict: 'A',
            scope: {
                metadata: '=meta',
                model: '=model'
            },
            link: function (scope, element, attributes) {
                var typeName = scope.metadata['type'];
                if (typeName == "RefBook") scope.$refBook = RefBookService.get(scope.metadata['arguments'][0]);
                if (typeName == "Organisation") scope.$refBook = RefBookService.get('Organisation');
                if (typeName == "OrgStructure") scope.$refBook = RefBookService.get('OrgStructure');
                if (typeName == "Person") scope.$refBook = RefBookService.get('Person');
                if (typeName == "Service") scope.$refBook = RefBookService.get('rbService');
                var template = templates[typeName];
                var child = $(template);
                $(element).append(child);
                $compile(child)(scope);
            }
        }
    }])
    .service('TocSpy', ['$window', function ($window) {
        var cache = [];
        var toc = null;
        var self = this;
        this.register = function (ctrl, element) {
            cache.push([ctrl, element[0]]);
            var parent = element.parent().controller('tocElement');
            if (parent) {
                parent.$children.push(ctrl);
            }
            element.on('$destroy', function () {
                self.unregister(ctrl);
            });
            $($window).scroll(function () {
                if (!toc) return;
                var i = cache.length;
                var something_changed = false;
                while (i--) {
                    var ctrl = cache[i][0];
                    var elem = cache[i][1];
                    var top = elem.getOffsetRect().top;
                    var height = elem.getBoundingClientRect().height;
                    var shift = $window.pageYOffset - top + 20;
                    var new_active = 0 < shift && shift < height;
                    if (new_active != ctrl.tocIsActive) {
                        ctrl.tocIsActive = new_active;
                        something_changed = true;
                    }
                }
                if (something_changed) {
                    toc.$digest();
                }
            })
        };
        this.unregister = function (ctrl) {
            var i = cache.length;
            while (i--) {
                if (cache[i][0] == ctrl) {
                    cache.splice(i, 1);
                    break;
                }
            }
            if (ctrl.$parent) {
                ctrl.$parent.$children.remove(ctrl)
            }
        };
        this.registerToc = function (the_toc) {
            toc = the_toc;
        }
    }])
    .directive('tocElement', ['TocSpy', function (TocSpy) {
        var merr = angular.$$minErr('tocElement');
        return {
            restrict: 'A',
            require: ['tocElement', '?form'],
            controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
                var self = this;
                if ($scope.hasOwnProperty('$index')) {
                    this.$name = $attrs.name + '_' + $scope.$index;
                } else {
                    this.$name = $attrs.name;
                }
                this.$children = [];
                this.$title = $attrs.tocElement;
                this.$form = null;
                this.$parent = $element.parent().controller('tocElement') || null;
                this.$invalid = function () {
                    if (self.$form) {
                        return self.$form.$invalid;
                    } else {
                        return false;
                    }
                };
                this.tocIsActive = false;
            }],
            link: function (scope, element, attrs, ctrls) {
                if (!attrs.name) {
                    merr('name', 'tocElement directive must have "name" attribute')
                }
                var self_ctrl = ctrls[0],
                    parent_ctrl = element.parent().controller('tocElement');
                self_ctrl.$form = ctrls[1];

                if (parent_ctrl) {
                    TocSpy.register(self_ctrl, element);
                }
                if (attrs.tocName) {
                    scope[attrs.tocName] = self_ctrl;
                }
                var jElement = $(element);
                jElement.attr('id', self_ctrl.$name);
                self_ctrl.element = jElement;
                if (attrs.tocDynamic) {
                    scope.$watch(attrs.tocDynamic, function (new_name) {
                        self_ctrl.$title = new_name;
                    })
                }
            }
        }
    }])
    .directive('tocAffix', ['TocSpy', function (TocSpy) {
        return {
            restrict: 'E',
            scope: {
                tocName: '='
            },
            replace: true,
            transclude: true,
            template:
                '<div class="toc">\
                    <ul class="nav">\
                        <li ng-repeat="node in tocName.$children" ng-class="{\'toc-selected-top\': node.tocIsActive}">\
                            <a ng-href="#[[node.$name]]" target="_self" class="wrap-btn" ng-class="{\'text-danger bg-danger\': node.$invalid()}">\
                                [[ node.$title ]]\
                            </a>\
                            <ul ng-if="node.$children.length" class="nav">\
                                <li ng-repeat="node in node.$children" ng-class="{\'toc-selected-bottom\': node.tocIsActive}">\
                                    <a ng-href="#[[node.$name]]" target="_self" class="wrap-btn" ng-class="{\'text-danger bg-danger\': node.$invalid()}">\
                                        [[ node.$title ]]\
                                    </a>\
                                </li>\
                            </ul>\
                        </li>\
                    </ul>\
                    <div ng-transclude></div>\
                </div>',
            link: function (scope, element, attrs) {
                TocSpy.registerToc(scope);
            }
        }
    }])
    .directive('wmOrgStructureTree', ['SelectAll', '$compile', '$http', 'FlatTree', function (SelectAll, $compile, $http, FlatTree) {
        // depends on wmCustomDropdown
        return {
            restrict: 'E',
            scope: {
                onSelect: '&?',
                nodesSelectable: '@'
            },
            template:
                '<div class="ui-treeview">\
                    <ul ng-repeat="root in tree.children">\
                        <li sf-treepeat="node in children of root">\
                            <a ng-click="select(node)" ng-if="!node.is_node" class="leaf">\
                                <div class="tree-label leaf">&nbsp;</div>\
                                [[ node.name ]]\
                            </a>\
                            <a ng-if="node.is_node && !nodesSelectable" ng-click="sas.toggle(node.id)" class="node">\
                                <div class="tree-label"\
                                     ng-class="{\'collapsed\': !sas.selected(node.id),\
                                                \'expanded\': sas.selected(node.id)}">&nbsp;</div>\
                                [[ node.name ]]\
                            </a>\
                            <a ng-if="node.is_node && nodesSelectable" class="leaf">\
                                <div class="tree-label" ng-click="sas.toggle(node.id)"\
                                     ng-class="{\'collapsed\': !sas.selected(node.id),\
                                                \'expanded\': sas.selected(node.id)}">&nbsp;</div>\
                                <span ng-click="select(node)" ng-bind="node.name"><span>\
                            </a>\
                            <ul ng-if="node.is_node && sas.selected(node.id)">\
                                <li sf-treecurse></li>\
                            </ul>\
                        </li>\
                    </ul>\
                </div>',
            link: function (scope) {
                var scope_query = '';
                var sas = scope.sas = new SelectAll([]);
                var der_tree = new FlatTree('parent_id');
                var tree = scope.tree = {};

                function doFilter() {
                    var keywords = scope_query.toLowerCase().split();
                    tree = der_tree.filter(function filter(item, idDict) {
                        return !keywords.length || keywords.filter(function (keyword) {
                            return (item.name.toLowerCase()).indexOf(keyword) !== -1
                        }).length == keywords.length
                    });
                    doRender();
                    sas.setSource(tree.masterDict.keys().map(function (key) {
                        var result = parseInt(key);
                        if (isNaN(result)) {
                            return key
                        } else {
                            return result
                        }
                    }));
                    sas.selectAll();
                }

                function doRender() {
                    tree = der_tree.render(make_object);
                    scope.tree.children = tree.root.children;
                }

                function make_object(item, is_node) {
                    if (item === null) {
                        var result = {};
                        result.parent_id = null;
                        result.id = 'root';
                        result.children = [];
                        result.is_node = true;
                        return result
                    }
                    return angular.extend(item, {is_node: is_node});
                }
                $http.get(url_get_orgstructure, {
                    params: {
                        org_id: 3479
                    }
                })
                .success(function (data) {
                    der_tree.set_array(data.result);
                    doFilter();
                });
                scope.$on('FilterChanged', function (event, query) {
                    scope_query = query;
                    doFilter()
                });
                scope.select = function (node) {
                    if (scope.$parent.$ctrl) {
                        scope.$parent.$ctrl.$set_query(node.name);
                        scope.$parent.$ctrl.$select(node);
                    }
                    scope.onSelect(node);
                }
            }
        }
    }])
    .directive('wmDiagnosisNew', ['$timeout', 'DiagnosisModal', 'WMEventServices', 'WMEventCache', 'WMWindowSync', 'RefBookService',
            function($timeout, DiagnosisModal, WMEventServices, WMEventCache, WMWindowSync, RefBookService) {
        return{
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                action: '=?',
                event: '=?',
                diagTypes: '=',
//                params: '=?',
//                listMode: '=',
                canAddNew: '=',
//                canDelete: '=',
                canEdit: '='
//                clickable: '=',
//                disabled: '='
            },
            controller: function ($scope) {
//                $scope.set_defaults = function (diagnosis){
//                    var defaults = $scope.params['defaults'];
//                    for (var key in defaults) {
//                        diagnosis[key] = defaults[key];
//                    }
//                };
                $scope.rbDiagnosisKind = RefBookService.get('rbDiagnosisKind');
                $scope.add_new_diagnosis = function (diag_type) {
                    var new_diagnosis = WMEventServices.get_new_diagnosis($scope.action);
                    var associated = this.rbDiagnosisKind.get_by_code('associated');
                    $scope.diagTypes.forEach(function(diagnosis_type){
                        new_diagnosis['diagnosis_types'][diagnosis_type.code] = associated;
                    })
//                    new_diagnosis.diagnosis_type = diag_type;
                    DiagnosisModal.openDiagnosisModal(new_diagnosis, $scope.action, $scope.params).then(function () {
                        $scope.model.push(new_diagnosis);
//                        WMEventServices.add_diagnosis($scope.event, new_diagnosis);
                    });
                };
//                $scope.delete_diagnosis = function (diagnosis, deleted) {
//                    if (arguments.length == 1) {
//                        deleted = 1;
//                    }
//                    if ($scope.listMode) {
//                        WMEventServices.delete_diagnosis($scope.model, diagnosis, deleted);
//                    } else {
//                        $scope.model = null;
//                    }
//                    WMEventServices.delete_diagnosis($scope.event.diagnoses, diagnosis, deleted);
//                };
                $scope.edit_diagnosis = function (diagnosis) {
                    DiagnosisModal.openDiagnosisModal(diagnosis, $scope.action, $scope.params);
                };
//                $scope.open_action = function (action_id) {
//                    if(action_id && $scope.clickable) {
//                        var url = url_for_schedule_html_action + '?action_id=' + action_id;
//                        WMWindowSync.openTab(url, $scope.update_event);
//                    }
//                };
//                $scope.update_event = function () {
//                    $scope.event.reload().then(function () {
//                        $scope.$root.$broadcast('event_loaded');
//                    });
//                };
                $scope.kind_change = function (diag){
                    diag.kind_changed = true;
                };
            },
            templateUrl: function(el, attrs){
                return '/WebMis20/wm-diagnosis-new.html'},
            link: function(scope, elm, attrs) {
//                scope.add_new_btn_visible = function () {
//                    return scope.canAddNew && (scope.listMode ? true : !scope.model)
//                };
//                if (scope.action && ! scope.risar) {
//                    WMEventCache.get(scope.action.event_id).then(function (event) {
//                        scope.event = event;
//                    });
//                }
            }
        }
    }])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/wm-diagnosis-new.html',
        '<div>\
            <ul class="nav nav-pills">\
                <li role="presentation" ng-repeat="diag_type in diagTypes" ng-class="{\'active\': $index == 0}">\
                    <a href="#[[diag_type.code]]" aria-controls="home" role="tab" data-toggle="tab" class="cuslom-tab-pills">[[diag_type.name]]</a>\
                </li>\
            </ul>\
            <div class="tab-content">\
                <div ng-repeat="diag_type in diagTypes" role="tabpanel" class="tab-pane" id="[[diag_type.code]]"  ng-class="{\'active\': $index == 0}">\
                    <table class="table table-condensed centered-table">\
                        <thead>\
                            <tr>\
                                <th class="col-md-2">Тип диазноза</th>\
                                <th class="col-md-3">Заболевание</th>\
                                <th class="col-md-2">Характер</th>\
                                <th class="col-md-2">Стадия</th>\
                                <th class="col-md-1">Установлен</th>\
                                <th class="col-md-1">Изменен</th>\
                                <th class="col-md-1" ng-if="canEdit"></th>\
                            </tr>\
                        </thead>\
                        <tbody>\
                            <tr ng-repeat="diag in model">\
                                <td><rb-select ng-model="diag.diagnosis_types.[[diag_type.code]]" ref-book="rbDiagnosisKind"\
                                     id="diag_type" name="diag_type" ng-change="kind_change(diag)" ng-if="canEdit"></rb-select>\
                                    <span ng-if="!canEdit" \
                                          ng-class="{\'text-bold\': !diag.diagnosis_types.[[diag_type.code]].code == \'associated\'}"\
                                          ng-bind="diag.diagnosis_types.[[diag_type.code]].name"></span>\
                                </td>\
                                <td>[[diag.diagnostic.mkb.code]] <em>[[diag.diagnostic.mkb.name]]</em></td>\
                                <td>[[diag.diagnostic.character.name]]</td>\
                                <td>[[diag.diagnostic.stage.name]]</td>\
                                <td>[[diag.set_date | asDate ]]</td>\
                                <td><span ng-if="diag.end_date">[[diag.diagnostic.ache_result.name ]] [[diag.end_date | asDate ]]</span>\
                                    <span ng-if="!diag.end_date">[[diag.diagnostic.createDatetime | asDate ]]</span>\
                                </td>\
                                <td ng-if="canEdit">\
                                    <button type="button" class="btn btn-sm btn-primary" title="Редактировать"\
                                            ng-click="edit_diagnosis(diag)"><span class="glyphicon glyphicon-pencil"></span>\
                                    </button>\
                                </td>\
                            </tr>\
                            <tr ng-if="canAddNew">\
                                <td colspan="6">\
                                    <div class="pull-right">\
                                        <button class="btn btn-primary" ng-click="add_new_diagnosis(diag_type)">Добавить новое заболевание</button>\
                                    </div>\
                                </td>\
                            </tr>\
                        </tbody>\
                    </table>\
                </div>\
            </div>\
        </div>')
    }])
    .directive('wmDiagnosis', ['$timeout', 'DiagnosisModal', 'WMEventServices', 'WMEventCache', 'WMWindowSync',
            function($timeout, DiagnosisModal, WMEventServices, WMEventCache, WMWindowSync) {
        return{
            restrict: 'E',
            replace: true,
            scope: {
                model: '=',
                action: '=?',
                event: '=?',
                params: '=?',
                listMode: '=',
                canAddNew: '=',
                canDelete: '=',
                canEdit: '=',
                clickable: '=',
                risar: '=',
                disabled: '='
            },
            controller: function ($scope) {
                $scope.set_defaults = function (diagnosis){
                    var defaults = $scope.params['defaults'];
                    for (var key in defaults) {
                        diagnosis[key] = defaults[key];
                    }
                };
                $scope.add_new_diagnosis = function () {
                    var new_diagnosis = WMEventServices.get_new_diagnosis($scope.action);
                    if ($scope.params && $scope.params['defaults']){
                        $scope.set_defaults(new_diagnosis)
                    }
                    if ($scope.risar) {
                        var sequence = $scope.action && $scope.listMode;
                        DiagnosisModal.openDiagnosisModalRisar(new_diagnosis, $scope.event, $scope.action, $scope.params, sequence).
                            then(function (rslt) {
                                var result = rslt[0], restart = rslt[1];
                                if ($scope.listMode) {
                                    $scope.model.push(new_diagnosis);
                                }
                                else {
                                    $scope.model = new_diagnosis;
                                }
                                if (sequence && restart) {
                                    $timeout($scope.add_new_diagnosis)
                                }
                            });
                    }
                    else {
                        DiagnosisModal.openDiagnosisModal(new_diagnosis, $scope.action, $scope.params).then(function () {
                            if ($scope.listMode) {
                                $scope.model.push(new_diagnosis);
                            }
                            else {
                                $scope.model = new_diagnosis;
                            }
                            WMEventServices.add_diagnosis($scope.event, new_diagnosis);
                        });
                    }

                };
                $scope.delete_diagnosis = function (diagnosis, deleted) {
                    if (arguments.length == 1) {
                        deleted = 1;
                    }
                    if ($scope.listMode) {
                        WMEventServices.delete_diagnosis($scope.model, diagnosis, deleted);
                    } else {
                        $scope.model = null;
                    }
                    WMEventServices.delete_diagnosis($scope.event.diagnoses, diagnosis, deleted);
                };
                $scope.edit_diagnosis = function (diagnosis) {
                    if ($scope.risar) {
                        DiagnosisModal.openDiagnosisModalRisar(diagnosis, $scope.event, $scope.action, $scope.params);
                    } else {
                        DiagnosisModal.openDiagnosisModal(diagnosis, $scope.action, $scope.params);
                    }
                };
                $scope.open_action = function (action_id) {
                    if(action_id && $scope.clickable) {
                        var url = url_for_schedule_html_action + '?action_id=' + action_id;
                        WMWindowSync.openTab(url, $scope.update_event);
                    }
                };
                $scope.update_event = function () {
                    $scope.event.reload().then(function () {
                        $scope.$root.$broadcast('event_loaded');
                    });
                };
            },
            templateUrl: function(el, attrs){
                return attrs.risar ? '/WebMis20/wm-diagnosis-risar.html': '/WebMis20/wm-diagnosis.html'},
            link: function(scope, elm, attrs) {
                scope.add_new_btn_visible = function () {
                    return scope.canAddNew && (scope.listMode ? true : !scope.model)
                };
                if (scope.action && ! scope.risar) {
                    WMEventCache.get(scope.action.event_id).then(function (event) {
                        scope.event = event;
                    });
                }
            }
        }
    }])
.service('DiagnosisModal', ['$modal', 'WMEventCache', 'CurrentUser', function ($modal, WMEventCache, CurrentUser) {
    return {
        openDiagnosisModal: function (model, action, params) {
            var locModel = angular.copy(model);
            var Controller = function ($scope) {
                $scope.model = locModel;

                // https://github.com/angular-ui/bootstrap/issues/969
                // http://stackoverflow.com/questions/19312936/angularjs-modal-dialog-form-object-is-undefined-in-controller
                $scope.form = {};
                $scope.diag_type_codes = ['2', '3', '7', '9', '11'];
                $scope.params = params;

                $scope.event = null;
                WMEventCache.get(action.event_id).then(function (event) {
                    $scope.event = event;
                    $scope.can_set_final_diag = (
                        // только лечащий врач
                        (CurrentUser.id === event.info.exec_person.id ||
                            CurrentUser.get_main_user().id === event.info.exec_person.id) &&
                        // в текущем действии еще нет заключительных диагнозов
                        action.properties.filter(function (prop) {
                            return (prop.type.type_name === 'Diagnosis' && (
                                prop.type.vector ? (
                                    prop.value.length && prop.value.some(function (diag) {
                                        return diag.diagnosis_type.code === '1' && diag.deleted === 0;
                                    })
                                ) : (prop.value && prop.value.diagnosis_type.code === '1' && diag.deleted === 0))
                            )
                        }).length === 0 &&
                        // в других *закрытых* действиях нет заключительных диагнозов
                        event.diagnoses.filter(function (diag) {
                            return diag.diagnosis_type.code === '1' && diag.action.status.code === 'finished';
                        }).length === 0
                    );
                    if ($scope.can_set_final_diag) {
                        $scope.diag_type_codes.push('1');
                    }
                });

                $scope.filter_type = function() {
                    return function(elem) {
                        return $scope.diag_type_codes.has(elem.code);
                    };
                };
                $scope.result_required = function () {
                    return safe_traverse($scope.model, ['diagnosis_type', 'code']) === '1';
                };

                $scope.$watch('form.DiagnosisForm.$dirty', function(n, o) {
                    $scope.model.diagnostic_changed = n;
                });
            };

            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-edit-diagnosis.html',
                size: 'lg',
                controller: Controller
            });
            return instance.result.then(function() {
                angular.extend(model, locModel);
            });
        },
        openDiagnosisModalRisar: function (model, event, action, params, sequence) {
            var locModel = angular.copy(model);
            var Controller = function ($scope) {
                $scope.model = locModel;
                $scope.action = action ? action : model.action;
                $scope.sequence = sequence;
                $scope.diag_type_codes = ['2', '3', '7', '9', '11'];
                $scope.params = params;

                $scope.can_set_final_diag = true;
                if ($scope.can_set_final_diag) {
                    $scope.diag_type_codes.push('1');
                }
                $scope.filter_type = function() {
                    return function(elem) {
                        return $scope.diag_type_codes.has(elem.code);
                    };
                };
                $scope.result_required = function () {
                    return safe_traverse($scope.model, ['diagnosis_type', 'code']) === '1';
                };
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-edit-diagnosis-risar.html',
                size: 'lg',
                controller: Controller
            });
            return instance.result.then(function(rslt) {
                angular.extend(model, locModel);
                return rslt
            });
        }
    }
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/wm-diagnosis.html',
        '<div class="row">\
            <div class="col-md-12">\
                <table class="table table-condensed">\
                    <thead>\
                        <tr>\
                            <th>Дата начала</th>\
                            <th>Тип</th>\
                            <th>Течение</th>\
                            <th>Код МКБ</th>\
                            <th>Врач</th>\
                            <th>Примечание</th>\
                            <th></th>\
                            <th></th>\
                        </tr>\
                    </thead>\
                    <tbody>\
                        <tr ng-if="!listMode && model" class="[[clickable && model.action_id ? \'row-clickable\' : \'\']]">\
                            <td ng-click="open_action(model.action_id)">[[model.set_date | asDate]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.diagnosis_type.name]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.character.name]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.diagnosis.mkb.code]] [[model.diagnosis.mkb.name]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.person.name]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.notes]]</td>\
                            <td>\
                                <button type="button" class="btn btn-sm btn-primary" title="Редактировать" ng-if="canEdit"\
                                        ng-click="edit_diagnosis(model)"><span class="glyphicon glyphicon-pencil"></span>\
                                </button>\
                            </td>\
                            <td>\
                                <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-if="canDelete"\
                                        ng-click="delete_diagnosis(model)"><span class="glyphicon glyphicon-trash"></span>\
                                </button>\
                            </td>\
                        </tr>\
                        <tr ng-if="listMode" class="[[clickable && diag.action_id ? \'row-clickable\' : \'\']]" ng-repeat="diag in model | flt_not_deleted">\
                            <td ng-click="open_action(diag.action_id)">[[diag.set_date | asDate]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.diagnosis_type.name]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.character.name]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.diagnosis.mkb.code]] [[diag.diagnosis.mkb.name]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.person.name]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.notes]]</td>\
                            <td>\
                                <button type="button" class="btn btn-sm btn-primary" title="Редактировать" ng-if="canEdit"\
                                        ng-click="edit_diagnosis(diag)"><span class="glyphicon glyphicon-pencil"></span>\
                                </button>\
                            </td>\
                            <td>\
                                <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-if="canDelete"\
                                        ng-click="delete_diagnosis(diag)"><span class="glyphicon glyphicon-trash"></span>\
                                </button>\
                            </td>\
                        </tr>\
                        <tr ng-show="add_new_btn_visible()">\
                            <td colspan="6">\
                                <button type="button" class="btn btn-sm btn-primary" title="Добавить"\
                                        ng-click="add_new_diagnosis()">Добавить\
                                </button>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
            </div>\
        </div>')
    }])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/wm-diagnosis-risar.html',
        '<div class="row">\
            <div class="col-md-12">\
                <table class="table table-condensed" ng-if="action">\
                    <thead>\
                        <tr>\
                            <th class="col-md-2">Дата начала</th>\
                            <th class="col-md-2">Дата окончания</th>\
                            <th class="col-md-2">Тип</th>\
                            <th class="col-md-2">Код МКБ</th>\
                            <th class="col-md-2">Врач</th>\
                            <th class="col-md-1">Описание</th>\
                            <th class="col-md-1"></th>\
                        </tr>\
                    </thead>\
                    <tbody>\
                        <tr ng-if="!listMode && model" class="[[clickable && model.action_id ? \'row-clickable\' : \'\']]">\
                            <td ng-click="open_action(model.action_id)">[[model.set_date | asDate]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.end_date | asDate]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.diagnosis_type.name]]</td>\
                            <td ng-click="open_action(model.action_id)"><span class="bottom_dotted" tooltip="[[ model.diagnosis.mkb.name ]]">[[model.diagnosis.mkb.code]]</span></td>\
                            <td ng-click="open_action(model.action_id)">[[model.person.name]]</td>\
                            <td ng-click="open_action(model.action_id)">[[model.diagnosis_description ? \'есть\': \'нет\']]</td>\
                            <td style="white-space:nowrap;">\
                                <button type="button" class="btn btn-sm btn-primary" title="Редактировать" ng-if="canEdit"\
                                        ng-click="edit_diagnosis(model)" ng-disabled="disabled"><span class="glyphicon glyphicon-pencil"></span>\
                                </button>\
                                <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-if="canDelete"\
                                        ng-click="delete_diagnosis(model)" ng-disabled="disabled"><span class="glyphicon glyphicon-trash"></span>\
                                </button>\
                            </td>\
                        </tr>\
                        <tr ng-if="listMode" class="[[clickable && diag.action_id ? \'row-clickable\' : \'\']]" ng-repeat="diag in model | flt_not_deleted">\
                            <td ng-click="open_action(diag.action_id)">[[diag.set_date | asDate]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.end_date | asDate]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.diagnosis_type.name]]</td>\
                            <td ng-click="open_action(diag.action_id)"><span class="bottom_dotted" tooltip="[[diag.diagnosis.mkb.name]]">[[diag.diagnosis.mkb.code]]</span></td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.person.name]]</td>\
                            <td ng-click="open_action(diag.action_id)">[[diag.diagnosis_description ? \'есть\': \'нет\']]</td>\
                            <td style="white-space:nowrap;">\
                                <button type="button" class="btn btn-sm btn-primary" title="Редактировать" ng-if="canEdit"\
                                        ng-click="edit_diagnosis(diag)" ng-disabled="disabled"><span class="glyphicon glyphicon-pencil"></span>\
                                </button>\
                                <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-if="canDelete"\
                                        ng-click="delete_diagnosis(diag)" ng-disabled="disabled"><span class="glyphicon glyphicon-trash"></span>\
                                </button>\
                            </td>\
                        </tr>\
                        <tr ng-show="add_new_btn_visible()">\
                            <td colspan="6">\
                                <button type="button" class="btn btn-sm btn-primary" title="Добавить"\
                                        ng-click="add_new_diagnosis()" ng-disabled="disabled">Добавить\
                                </button>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
                <table class="table table-condensed" ng-if="listMode && !action">\
                    <thead>\
                        <tr>\
                            <th class="col-md-1">Диагноз</th>\
                            <th class="col-md-2">Тип</th>\
                            <th class="col-md-1">Начало</th>\
                            <th class="col-md-1">Окончание</th>\
                            <th ng-if="!action" class="col-md-3">Контекст</th>\
                            <th class="col-md-1"></th>\
                        </tr>\
                    </thead>\
                    <tbody>\
                        <tr ng-if="listMode" class="[[clickable && diag.action_id ? \'row-clickable\' : \'\']]" ng-repeat="diag in model">\
                            <td ng-if="diag.deleted" colspan="6" style="text-align:center;">Диагноз [[diag.diagnosis.mkb.code]] был удален. <a ng-click="delete_diagnosis(diag, 0)" style="cursor: pointer">Восстановить</a>?</td>\
                            <td ng-if="diag.deleted == 0" ng-click="open_action(diag.action_id)" style="text-align:center;"><span class="bottom_dotted" tooltip="[[diag.diagnosis.mkb.name]]">[[diag.diagnosis.mkb.code]]</span></td>\
                            <td ng-if="diag.deleted == 0" ng-click="open_action(diag.action_id)">[[diag.diagnosis_type.name]]</td>\
                            <td ng-if="diag.deleted == 0" ng-click="open_action(diag.action_id)">[[diag.set_date | asDate]] </br> [[diag.person.name]]</td>\
                            <td ng-if="diag.deleted == 0" ng-click="open_action(diag.action_id)">[[diag.end_date | asDate]] </br> [[diag.end_date ? diag.modify_person.name : ""]]</td>\
                            <td ng-if="diag.deleted == 0" ng-click="open_action(diag.action_id)">[[diag.action.action_type.name]] - [[diag.action_property_name]]</td>\
                            <td ng-if="diag.deleted == 0" style="white-space:nowrap;">\
                                <button type="button" class="btn btn-sm btn-primary" title="Редактировать" ng-if="canEdit"\
                                        ng-click="edit_diagnosis(diag)"><span class="glyphicon glyphicon-pencil"></span>\
                                </button>\
                                <button type="button" class="btn btn-sm btn-danger" title="Удалить" ng-if="canDelete"\
                                        ng-click="delete_diagnosis(diag)"><span class="glyphicon glyphicon-trash"></span>\
                                </button>\
                            </td>\
                        </tr>\
                        <tr ng-show="add_new_btn_visible()">\
                            <td colspan="6">\
                                <button type="button" class="btn btn-sm btn-primary" title="Добавить"\
                                        ng-click="add_new_diagnosis()">Добавить\
                                </button>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
            </div>\
        </div>')
    }])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-edit-diagnosis.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">Диагноз</h4>\
        </div>\
        <div class="modal-body">\
            <ng-form name="form.DiagnosisForm">\
                <div class="row marginal">\
                    <div class="col-md-8">\
                        <div class="form-group" ng-class="{\'has-error\': form.DiagnosisForm.mkb.$invalid}">\
                            <label for="MKB" class="control-label">МКБ</label>\
                            <ui-mkb ng-model="model.diagnostic.mkb" name="mkb" ng-required="true"></ui-mkb>\
                        </div>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-8">\
                        <div class="form-group">\
                            <label for="MKB" class="control-label">МКБ дополнительный код (причина травмы, инфекционный агент)</label>\
                            <ui-mkb ng-model="model.diagnostic.mkbex" name="mkb" ng-disabled="true"></ui-mkb>\
                        </div>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="trauma" class="control-label">Травма</label>\
                        <ui-select class="form-control" name="trauma" theme="select2"\
                            ng-model="model.diagnostic.trauma" ref-book="rbTraumaType">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="tt in ($refBook.objects | filter: $select.search) track by tt.id">\
                                <span ng-bind-html="tt.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-11">\
                        <label for="diagnosis_description" class="control-label">Описание диагноза</label>\
                        <wysiwyg ng-model="model.diagnostic.diagnosis_description" thesaurus-code="[[params.thesaurus_code]]"/>\
                    </div>\
                </div>\
                <div class="row tmargin20 marginal">\
                    <div class="col-md-3">\
                        <label for="trauma" class="control-label">Характер</label>\
                        <ui-select class="form-control" name="diagnosis_character" theme="select2"\
                            ng-model="model.diagnostic.character" ref-book="rbDiseaseCharacter">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="ct in ($refBook.objects | filter: $select.search) track by ct.id">\
                                <span ng-bind-html="ct.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="phase" class="control-label">Фаза</label>\
                        <ui-select class="form-control" name="phase" theme="select2"\
                            ng-model="model.diagnostic.phase" ref-book="rbDiseasePhases">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="dp in ($refBook.objects | filter: $select.search) track by dp.id">\
                                <span ng-bind-html="dp.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="stage" class="control-label">Стадия</label>\
                        <ui-select class="form-control" name="stage" theme="select2"\
                            ng-model="model.diagnostic.stage" ref-book="rbDiseaseStage">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="ds in ($refBook.objects | filter: $select.search) track by ds.id">\
                                <span ng-bind-html="ds.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-6">\
                        <div class="form-group"\
                        ng-class="{\'has-error\': model.person == null}">\
                            <label for="diagnosis_person" class="control-label">Врач</label>\
                            <wm-person-select ng-model="model.person" name="diagnosis_person" ng-required="true"></wm-person-select>\
                        </div>\
                    </div>\
                    <div class="col-md-3">\
                        <div class="form-group" ng-class="{\'has-error\': form.DiagnosisForm.set_date.$invalid}">\
                            <label for="diagnosis_date" class="control-label">Дата начала</label>\
                            <wm-date name="set_date" ng-model="model.set_date" ng-required="true">\
                            </wm-date>\
                        </div>\
                    </div>\
                    <div class="col-md-3">\
                        <div class="form-group" ng-class="{\'has-error\': form.DiagnosisForm.end_date.$invalid}">\
                            <label for="diagnosis_date" class="control-label">Дата окончания</label>\
                            <wm-date name="end_date" ng-model="model.end_date">\
                            </wm-date>\
                        </div>\
                    </div>\
                </div>\
                <div class="row marginal">\
                    <div class="col-md-4">\
                        <label for="ache_result" class="control-label">Исход заболевания</label>\
                        <ui-select class="form-control" name="ache_result" theme="select2"\
                            ng-model="model.diagnostic.ache_result" ref-book="rbAcheResult">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="ar in ($refBook.objects | filter: $select.search) track by ar.id">\
                                <span ng-bind-html="ar.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                    <div class="col-md-3">\
                        <label for="health_group" class="control-label">Группа здоровья</label>\
                        <ui-select class="form-control" name="health_group" theme="select2"\
                            ng-model="model.diagnostic.health_group" ref-book="rbHealthGroup">\
                            <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                            <ui-select-choices repeat="hg in ($refBook.objects | filter: $select.search) track by hg.id">\
                                <span ng-bind-html="hg.name | highlight: $select.search"></span>\
                            </ui-select-choices>\
                        </ui-select>\
                    </div>\
                </div>\
                <div class="row">\
                    <div class="col-md-11">\
                    <label for="notes" class="control-label">Примечание</label>\
                    <textarea class="form-control" id="notes" name="notes" rows="2" autocomplete="off" ng-model="model.diagnostic.notes"></textarea>\
                    </div>\
                </div>\
            </ng-form>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
            <button type="button" class="btn btn-success" ng-click="$close()"\
            ng-disabled="form.DiagnosisForm.$invalid">Сохранить</button>\
        </div>')
    }])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-edit-diagnosis-risar.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">Диагноз</h4>\
        </div>\
        <div class="modal-body">\
            <ng-form name="DiagnosisForm">\
                <table class="table table-condensed">\
                    <thead>\
                    <tr>\
                        <th class="col-md-3"></th>\
                        <th class="col-md-9"></th>\
                    </tr>\
                    </thead>\
                    <tbody>\
                        <tr>\
                            <th class="text-right">Тип <span class="text-danger">*</span></th>\
                            <td>\
                                <div class="form-group col-sm-5 col-md-4 col-lg-4"\
                                     ng-class="{\'has-error\': DiagnosisForm.diagnosis_type.$invalid}">\
                                    <ui-select class="form-control" name="diagnosis_type" theme="select2"\
                                        ng-model="model.diagnosis_type" ref-book="rbDiagnosisType"\
                                        ng-required="true" ng-disabled="[[params.disabled.diagnosis_type]]">\
                                        <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                                        <ui-select-choices repeat="dt in ($refBook.objects | filter: $select.search | filter: filter_type()) track by dt.id">\
                                            <span ng-bind-html="dt.name | highlight: $select.search"></span>\
                                        </ui-select-choices>\
                                    </ui-select>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">Характер <span>&nbsp;</span></th>\
                            <td>\
                                <div class="col-sm-5 col-md-4 col-lg-4">\
                                <ui-select class="form-control" name="diagnosis_character" theme="select2"\
                                    ng-model="model.character" ref-book="rbDiseaseCharacter">\
                                    <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                                    <ui-select-choices repeat="ct in ($refBook.objects | filter: $select.search) track by ct.id">\
                                        <span ng-bind-html="ct.name | highlight: $select.search"></span>\
                                    </ui-select-choices>\
                                </ui-select>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">Дата начала <span class="text-danger">*</span></th>\
                            <td>\
                                <div class="form-group col-sm-5 col-md-4 col-lg-4" ng-class="{\'has-error\': DiagnosisForm.set_date.$invalid}">\
                                    <wm-date name="set_date" ng-model="model.set_date" ng-required="true">\
                                    </wm-date>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">МКБ <span class="text-danger">*</span></th>\
                            <td>\
                                <div class="form-group col-sm-11 col-md-11 col-lg-11"\
                                ng-class="{\'has-error\': DiagnosisForm.mkb.$invalid}">\
                                    <ui-mkb ng-model="model.diagnosis.mkb" name="mkb" ng-required="true"></ui-mkb>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">Врач <span>&nbsp;</span></th>\
                            <td>\
                                <div class="form-group col-sm-6 col-md-5 col-lg-5"\
                                ng-class="{\'has-error\': model.person == null}">\
                                    <wm-person-select ng-model="model.person" name="diagnosis_person" ng-required="true"></wm-person-select>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">Дата окончания <span>&nbsp;</span></th>\
                            <td>\
                                <div class="form-group col-sm-5 col-md-4 col-lg-4" ng-class="{\'has-error\': DiagnosisForm.end_date.$invalid}">\
                                    <wm-date name="end_date" ng-model="model.end_date" ng-required="[[params.required.end_date]]">\
                                    </wm-date>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">Результат <span>&nbsp;</span></th>\
                            <td>\
                                <div class="col-sm-5 col-md-4 col-lg-4" ng-class="{\'has-error\': DiagnosisForm.result.$invalid}">\
                                    <ui-select class="form-control" name="result" theme="select2"\
                                        ng-model="model.result" ref-book="rbResult"\
                                        ng-required="result_required()">\
                                        <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                                        <ui-select-choices repeat="r in ($refBook.objects | filter: $select.search | rb_result_filter: 2) track by r.id">\
                                            <span ng-bind-html="r.name | highlight: $select.search"></span>\
                                        </ui-select-choices>\
                                    </ui-select>\
                                </div>\
                            </td>\
                        </tr>\
                        <tr>\
                            <th class="text-right">Описание <span>&nbsp;</span></th>\
                            <td>\
                                <div class="col-sm-11 col-md-11 col-lg-11">\
                                <wysiwyg ng-model="model.diagnosis_description" thesaurus-code="[[params.thesaurus_code]]"/>\
                                </div>\
                            </td>\
                        </tr>\
                    </tbody>\
                </table>\
            </ng-form>\
        </div>\
        <div class="modal-footer">\
            <label ng-hide="!sequence"><input type="checkbox" class="checkbox checkbox-inline" ng-model="restart">Создать ещё</label>\
            <button type="button" class="btn btn-success" ng-click="$close([model, restart])"\
            ng-disabled="DiagnosisForm.$invalid">Сохранить</button>\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
        </div>')
    }])
;
angular.module('WebMis20.validators', [])
.directive('enumValidator', function() {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                if (viewValue && viewValue.id > 0) {
                    ctrl.$setValidity('text', true);
                    return viewValue;
                } else {
                    ctrl.$setValidity('text', false);
                    return undefined;
                }
            });
        }
    };
})
.directive('snilsValidator', ['$timeout', function ($timeout) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            function snilsCRC (value) {
                var v = value.substring(0, 3) + value.substring(4, 7) + value.substring(8, 11) + value.substring(12, 14);
                var result = 0;
                for (var i=0; i < 9; i++) {
                    result += (9 - i) * parseInt(v[i])
                }
                result = (result % 101) % 100;
                if (result < 10) return '0' + result;
                else return '' + result;
            }
            ctrl.$parsers.unshift(function(viewValue) {
                ctrl.$setValidity('text', viewValue == "" || viewValue && viewValue.substring(12, 14) == snilsCRC(viewValue));
                $timeout(function(){
                    if (ctrl.$invalid){
                        elm.trigger('show_popover');
                    } else {
                        elm.trigger('hide_popover');
                    }
                });
                return viewValue;
            });
        }
    };
}])
.directive('validatorRegexp', [function () {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, element, attrs, ctrl) {
            var regexp = null;
            var evalue = null;
            scope.$watch(attrs.validatorRegexp, function (n, o) {
                evalue = n;
                if (!evalue) {
                    if (ctrl.$viewValue) {
                        ctrl.$setViewValue('');
                        ctrl.$render();
                    }
                    ctrl.$setValidity('text', true);
                    $(element).attr('disabled', true);
                } else {
                    $(element).removeAttr('disabled');
                    regexp = new RegExp(evalue);
                    ctrl.$setValidity('text', ctrl.$viewValue && regexp.test(ctrl.$viewValue));
                }
            });
            ctrl.$parsers.unshift(function(viewValue) {
                if (evalue && regexp) {
                    if ($(element).attr('ui-mask')) {
                        viewValue = viewValue.replace(/_$/, '')
                    }
                    ctrl.$setValidity('text', viewValue && regexp.test(viewValue));
                }
                return viewValue
            });
        }
    }
}])
.directive('validNumber', function() {
    return {
        require: '?ngModel',
        link: function (scope, element, attrs, ngModelCtrl) {
            if (!ngModelCtrl) {
                return;
            }
            var allowFloat = attrs.hasOwnProperty('validNumberFloat');
            var allowNegative = attrs.hasOwnProperty('validNumberNegative');
            var regex = new RegExp('[^0-9' + (allowFloat ? '.' : '') + (allowNegative ? '-' : '') + ']+', 'g');

            var min_val,
                max_val,
                precision = 0;
            scope.$watch(function () {
                return parseInt(scope.$eval(attrs.minVal));
            }, function (n, o) {
                min_val = n;
            });
            scope.$watch(function () {
                return parseInt(scope.$eval(attrs.maxVal));
            }, function (n, o) {
                max_val = n;
            });

            function clear_char_duplicates(string, char) {
                var arr = string.split(char);
                var res;
                if (arr.length > 1) {
                    res = arr.shift();
                    res += char + arr.shift();
                    res += arr.join('');
                } else {
                    res = arr[0];
                }
                return res;
            }

            function format_view_value(val, clean_val) {
                if (allowFloat) {
                    return (val.endswith('.') &&  val.indexOf('.') === val.length - 1) ?
                        (clean_val + '.') :
                        clean_val.toFixed(precision);
                } else {
                    return clean_val;
                }
            }

            function calc_precision(val) {
                if (allowFloat){
                    var precision = val.length -
                        (val.indexOf('.') !== -1 ? val.indexOf('.') : val.length) -
                        (val.endswith('.') ? 0 : 1);
                    precision = Math.min(Math.max(precision, 0), 20);
                    return precision;
                } else {
                    return 0;
                }
            }

            ngModelCtrl.$parsers.push(function (val) {
                if (val === undefined) {
                    return val;
                } else if (angular.isNumber(val)) {
                    return val;
                }
                var clean = clear_char_duplicates(val.replace(regex, ''), '.');
                precision = calc_precision(clean);
                clean = clean !== '' ? parseFloat(clean) : min_val;
                if (!isNaN(min_val)) {
                    clean = Math.max(clean, min_val);
                }
                if (!isNaN(max_val)) {
                    clean = Math.min(clean, max_val);
                }
                if (val !== clean) {
                    ngModelCtrl.$viewValue = format_view_value(val, clean);
                    ngModelCtrl.$render();
                }
                return clean;
            });

            element.bind('keypress', function (event) {
                if (event.keyCode === 32) {
                    event.preventDefault();
                }
            });

            element.bind('blur', function (event) {
                var value = parseFloat(this.value);
                if (isNaN(value)) {
                    this.value = null;
                } else {
                    this.value = value;
                }
            });
        }
    };
})
.directive('wmValidate', [function () {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, element, attrs, ngModelCtrl) {
            ngModelCtrl.$parsers.push(function (val) {
                var validate_func = scope.$eval(attrs.wmValidate),
                    result = validate_func(val);
                ngModelCtrl.$setValidity(result.type, result.success);
                return val;
            });
        }
    };
}]);
