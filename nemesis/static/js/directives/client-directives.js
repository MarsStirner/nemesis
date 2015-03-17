'use strict';

angular.module('WebMis20.directives').
    directive('wmPolicy', ['RefBookService', '$filter',
        function(RefBookService, $filter) {
            return {
                controller: function($scope){
                    $scope.make_placeholder = function(mask){
                        if (mask){
                            return mask.replace(/[9A*]/g,"_")
                        }
                        return ""
                    };
                    $scope.placeholder_serial = $scope.modelPolicy.policy_type ? $scope.make_placeholder($scope.modelPolicy.policy_type.masks.serial) : "";
                    $scope.placeholder_number = $scope.modelPolicy.policy_type ? $scope.make_placeholder($scope.modelPolicy.policy_type.masks.number) : "";
                },
                restrict: 'E',
                require: '^form',
                scope: {
                    pType: '@',
                    idPostfix: '@',
                    modelPolicy: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    var policy_codes = (scope.pType == 0)?(['cmiOld', 'cmiTmp', 'cmiCommonPaper', 'cmiCommonElectron', 'cmiUEC', 'cmiFnkcIndustrial', 'cmiFnkcLocal']):(['vmi', '3']);

                    /* Здесь начинается костыль, который предотвращает бесконечный $digest */
                    scope.rbPolicyType = RefBookService.get('rbPolicyType');
                    scope.Organisation = RefBookService.get('Organisation');

                    scope.rbPolicyObjects = [];
                    scope.OrganisationObjects = [];

                    scope.$watch('rbPolicyType.objects',
                        function (n) {
                            scope.rbPolicyObjects = $filter('attribute')(n, 'code', policy_codes);
                        }
                    );

                    scope.$watch('Organisation.objects',
                        function (n) {
                            scope.OrganisationObjects = $filter('attribute')(n, 'is_insurer');
                        }
                    );
                    /* А здесь заканчивается костыль */

                    scope.policyForm = formCtrl;

                    scope.builder_organisation = function(name) {
                        return {
                            'id': null,
                            'full_name': name,
                            'short_name': name,
                            'infis': null,
                            'title': null
                        };
                    };

                    scope.$watch('policyForm.$dirty', function(n, o) {
                        scope.modelPolicy.dirty = n;
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': (policyForm.$dirty || modelPolicy.id) && policyForm.pol_type.$invalid}">\
                <label for="pol_type[[idPostfix]]" class="control-label">Тип</label>\
                <ui-select class="form-control" id="pol_type[[idPostfix]]" name="pol_type" theme="select2"\
                           ng-model="modelPolicy.policy_type" ng-disabled="!edit_mode()" ng-required="policyForm.$dirty">\
                    <ui-select-match placeholder="Тип полиса">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="pt in rbPolicyObjects | filter: $select.search">\
                        <div ng-bind-html="pt.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-1"\
                 ng-class="{\'has-error\': ((policyForm.$dirty || modelPolicy.id) && policyForm.pol_serial.$invalid) || policyForm.pol_serial.$error.required}">\
                <label for="pol_serial[[idPostfix]]" class="control-label">Серия</label>\
                <input type="text" class="form-control" id="pol_serial[[idPostfix]]" name="pol_serial"\
                       ui-mask="[[modelPolicy.policy_type.masks.serial]]" autocomplete="off" \
                       placeholder="[[placeholder_serial]]" validator-regexp="modelPolicy.policy_type.validators.serial"\
                       ng-model="modelPolicy.serial" ng-disabled="!edit_mode()" ng-required="modelPolicy.policy_type.validators.serial && policyForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': (policyForm.$dirty || modelPolicy.id) && policyForm.pol_number.$invalid}">\
                <label for="pol_number[[idPostfix]]" class="control-label">Номер</label>\
                <input type="text" class="form-control" id="pol_number[[idPostfix]]" name="pol_number"\
                       ui-mask="[[modelPolicy.policy_type.masks.number]]" autocomplete="off"\
                       placeholder="[[placeholder_number]]" validator-regexp="modelPolicy.policy_type.validators.number"\
                       ng-model="modelPolicy.number" ng-required="policyForm.$dirty" ng-disabled="!edit_mode()"/>\
            </div>\
            <div class="form-group col-md-offset-1 col-md-2"\
                 ng-class="{\'has-error\': (policyForm.$dirty || modelPolicy.id) && policyForm.pol_begdate[[idPostfix]].$invalid}">\
                <label for="pol_begdate[[idPostfix]]" class="control-label">Дата выдачи</label>\
                <wm-date id="pol_begdate[[idPostfix]]"\
                         ng-model="modelPolicy.beg_date" ng-disabled="!edit_mode()" ng-required="policyForm.$dirty">\
                </wm-date>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': policyForm.pol_enddate[[idPostfix]].$invalid }">\
                <label for="pol_enddate[[idPostfix]]" class="control-label">Действителен до</label>\
                <wm-date id="pol_enddate[[idPostfix]]"\
                         ng-model="modelPolicy.end_date" ng-disabled="!edit_mode()">\
                </wm-date>\
            </div>\
        </div>\
        <div class="row">\
            <div class="form-group col-md-12"\
                 ng-class="{\'has-error\': (policyForm.$dirty || modelPolicy.id) && policyForm.pol_insurer.$invalid}">\
                <label for="pol_insurer[[idPostfix]]" class="control-label">Страховая медицинская организация</label>\
                <div ng-class="form-control" class="validatable" id="pol_insurer[[idPostfix]]" name="pol_insurer"\
                     free-input-select="" freetext="true" items="OrganisationObjects" builder="builder_organisation"\
                     ng-disabled="!edit_mode()" ng-required="policyForm.$dirty" ng-model="modelPolicy.insurer">\
                    [[ item.short_name ]]\
                </div>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmSocStatus', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    ssClass: '@',
                    idPostfix: '@',
                    modelSocStatus: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.socStatusForm = formCtrl;
                    scope.rbSocStatusType = RefBookService.get('rbSocStatusType');

                    scope.$watch('socStatusForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelSocStatus.dirty = n;
                        }
                    });

                    scope.filter_soc_status = function(s_class) {
                        return function(elem) {
                            var classes_codes = elem.classes.map(function(s_class){
                                return s_class.code;
                                });
                            return classes_codes.indexOf(s_class) != -1;
                        };
                    };
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-6"\
                 ng-class="{\'has-error\': (socStatusForm.$dirty || modelSocStatus.id) && socStatusForm.ss_type.$invalid}">\
                <label for="ss_type_[[idPostfix]]">Тип</label>\
                <ui-select class="form-control" id="ss_type_[[idPostfix]]" name="ss_type" theme="select2"\
                           ng-model="modelSocStatus.ss_type" ng-disabled="!edit_mode()" ng-required="socStatusForm.$dirty">\
                    <ui-select-match placeholder="">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="sst in rbSocStatusType.objects | filter: filter_soc_status(ssClass) | filter: $select.search">\
                        <div ng-bind-html="sst.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': ((socStatusForm.$dirty || modelSocStatus.id) && socStatusForm.ss_begdate[[idPostfix]].$invalid)}">\
                <label for="ss_begdate[[idPostfix]]" class="control-label">Дата начала</label>\
                <wm-date id="ss_begdate[[idPostfix]]"\
                         ng-model="modelSocStatus.beg_date" ng-disabled="!edit_mode()"\
                         ng-required="socStatusForm.$dirty">\
                </wm-date>\
            </div>\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': socStatusForm.ss_enddate_[[idPostfix]].$invalid}">\
                <label for="ss_enddate_[[idPostfix]]" class="control-label">Дата окончания</label>\
                <wm-date id="ss_enddate_[[idPostfix]]"\
                         ng-model="modelSocStatus.end_date" ng-disabled="!edit_mode()">\
                </wm-date>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmDocument', ['RefBookService',
        function(RefBookService) {
            return {
                controller: function($scope){
                    $scope.make_placeholder = function(mask){
                        if (mask){
                            return mask.replace(/[9A*]/g,"_")
                        }
                        return ""
                    };
                    $scope.placeholder_serial = $scope.modelDocument.doc_type ? $scope.make_placeholder($scope.modelDocument.doc_type.masks.serial) : "";
                    $scope.placeholder_number = $scope.modelDocument.doc_type ? $scope.make_placeholder($scope.modelDocument.doc_type.masks.number) : "";
                },
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    groupCode:'@',
                    modelDocument: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.docForm = formCtrl;
                    scope.rbDocumentType = RefBookService.get('rbDocumentType');
                    scope.rbUFMS = RefBookService.get('rbUFMS');
                    scope.ufmsItems = scope.rbUFMS.objects.map(function(o) {
                        return o.name;
                    });
                    scope.$watch('rbUFMS.objects', function(n, o) {
                        if (n !== o) {
                            scope.ufmsItems = n.map(function(o) {
                                return o.name;
                            });
                        }
                    });

                    scope.$watch('docForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelDocument.dirty = n;
                        }
                    });

                    scope.filter_document = function(group_code) {
                        return function(elem) {
                            return elem.group.code == group_code;
                        };
                    };
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': (docForm.$dirty || modelDocument.id) && docForm.doc_type.$invalid}">\
                <label for="doc_type[[idPostfix]]" class="control-label">Тип</label>\
                <ui-select class="form-control" id="doc_type[[idPostfix]]" name="doc_type" theme="select2"\
                           ng-model="modelDocument.doc_type" ng-disabled="!edit_mode()" ng-required="docForm.$dirty">\
                    <ui-select-match placeholder="Тип документа">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="dt in rbDocumentType.objects | filter: filter_document(groupCode) | filter: $select.search">\
                        <div ng-bind-html="dt.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': ((docForm.$dirty || modelDocument.id)  && docForm.doc_serial.$invalid) || docForm.doc_serial.$error.required}">\
                <label for="doc_serial[[idPostfix]]" class="control-label">Серия</label>\
                <input type="text" class="form-control" id="doc_serial[[idPostfix]]" name="doc_serial"\
                       ui-mask="[[modelDocument.doc_type.masks.serial]]"\
                       autocomplete="off" placeholder="[[placeholder_serial]]" validator-regexp="modelDocument.doc_type.validators.serial"\
                       ng-model="modelDocument.serial" ng-disabled="!edit_mode()"\
                       ng-required="modelDocument.doc_type.validators.serial && docForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': (docForm.$dirty || modelDocument.id) && docForm.doc_number.$invalid}">\
                <label for="doc_number[[idPostfix]]" class="control-label">Номер</label>\
                <input type="text" class="form-control" id="doc_number[[idPostfix]]" name="doc_number"\
                       ui-mask="[[modelDocument.doc_type.masks.number]]"\
                       autocomplete="off" placeholder="[[placeholder_number]]" validator-regexp="modelDocument.doc_type.validators.number"\
                       ng-model="modelDocument.number" ng-required="docForm.$dirty" ng-disabled="!edit_mode()"/>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': (docForm.$dirty || modelDocument.id) && docForm.doc_begdate[[idPostfix]].$invalid}">\
                <label for="doc_begdate[[idPostfix]]" class="control-label">Дата выдачи</label>\
                <wm-date id="doc_begdate[[idPostfix]]"\
                         ng-model="modelDocument.beg_date" ng-disabled="!edit_mode()" ng-required="docForm.$dirty">\
                </wm-date>\
            </div>\
            <div class="form-group col-md-2"\
                 ng-class="{\'has-error\': docForm.doc_enddate[[idPostfix]].$invalid }">\
                <label for="doc_enddate[[idPostfix]]" class="control-label">Действителен до</label>\
                <wm-date id="doc_enddate[[idPostfix]]" ng-model="modelDocument.end_date" ng-disabled="!edit_mode()">\
                </wm-date>\
            </div>\
        </div>\
    \
        <div class="row">\
            <div class="form-group col-md-12"\
                 ng-class="{\'has-error\': (docForm.$dirty || modelDocument.id) && docForm.doc_ufms.$invalid}">\
                <label for="doc_ufms[[idPostfix]]" class="control-label">Выдан</label>\
                <div ng-class="form-control" class="validatable" id="doc_ufms[[idPostfix]]" name="doc_ufms"\
                     fs-select="" freetext="true" items="ufmsItems"\
                     ng-disabled="!edit_mode()" ng-required="docForm.$dirty" ng-model="modelDocument.origin">\
                    {{item}}\
                </div>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmClientBloodType', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    modelBloodType: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.cbtForm = formCtrl;
                    scope.rbBloodType = RefBookService.get('rbBloodType');

                    scope.$watch('cbtForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelBloodType.dirty = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': (cbtForm.$dirty || modelBloodType.id) && cbtForm.cbt_date[[idPostfix]].$invalid}">\
                <label for="cbt_date[[idPostfix]]" class="control-label">Дата установления</label>\
                <wm-date id="cbt_date[[idPostfix]]"\
                         ng-model="modelBloodType.date" ng-disabled="!edit_mode()" ng-required="cbtForm.$dirty">\
                </wm-date>\
            </div>\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': (cbtForm.$dirty || modelBloodType.id) && cbtForm.cbt_type.$invalid}">\
                <label for="cbt_type[[idPostfix]]" class="control-label">Тип</label>\
                <ui-select class="form-control" id="cbt_type[[idPostfix]]" name="cbt_type" theme="select2"\
                           ng-model="modelBloodType.blood_type" ng-disabled="!edit_mode()" ng-required="cbtForm.$dirty">\
                    <ui-select-match placeholder="Группа крови">[[$select.selected.name]]</ui-select-match>\
                    <ui-select-choices repeat="bt in rbBloodType.objects | filter: $select.search">\
                        <div ng-bind-html="bt.name | highlight: $select.search"></div>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-5"\
                 ng-class="{\'has-error\': (cbtForm.$dirty || modelBloodType.id) && cbtForm.cbt_person.$invalid}">\
                <label for="cbt_person[[idPostfix]]" class="control-label">Врач, установивший группу крови</label>\
                <wm-person-select id="cbt_person[[idPostfix]]" name="cbt_person"\
                    ng-model="modelBloodType.person" ng-disabled="!edit_mode()" ng-required="cbtForm.$dirty">\
                </wm-person-select>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmClientAllergy', ['RefBookService',
        function(RefBookService) {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    type: '@',
                    modelAllergy: '=',
                    edit_mode: '&editMode'

                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.algForm = formCtrl;
                    scope.rbAllergyPower = RefBookService.get('AllergyPower');

                    scope.$watch('algForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelAllergy.dirty = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': (algForm.$dirty || modelAllergy.id) && algForm.alg_name.$invalid}">\
                <label for="alg_name[[idPostfix]]" class="control-label">[[type === \'allergy\' ? \'Вещество\' : \'Препарат\']]</label>\
                <input type="text" class="form-control" id="alg_name[[idPostfix]]" name="alg_name"\
                       autocomplete="off" placeholder=""\
                       ng-model="modelAllergy.name" ng-disabled="!edit_mode()" ng-required="algForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': (algForm.$dirty || modelAllerg.idy) && algForm.alg_power.$invalid}">\
                <label for="alg_power[[idPostfix]]" class="control-label">Степень</label>\
                <select class="form-control" id="alg_power[[idPostfix]]" name="alg_power"\
                        ng-model="modelAllergy.power"\
                        ng-options="pow as pow.name for pow in rbAllergyPower.objects track by pow.id"\
                        ng-disabled="!edit_mode()" ng-required="algForm.$dirty">\
                </select>\
            </div>\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': (algForm.$dirty || modelAllergy.id) && algForm.alg_date[[idPostfix]].$invalid}">\
                <label for="alg_date[[idPostfix]]" class="control-label">Дата установления</label>\
                <wm-date id="alg_date[[idPostfix]]"\
                         ng-model="modelAllergy.date" ng-disabled="!edit_mode()" ng-required="algForm.$dirty">\
                </wm-date>\
            </div>\
        </div>\
        <div class="row">\
            <div class="form-group col-md-12">\
                <label for="alg_notes[idPostfix]">Примечание</label>\
                <textarea class="form-control" id="alg_notes" name="alg_notes" rows="2" autocomplete="off"\
                    ng-model="modelAllergy.notes" ng-disabled="!edit_mode()"></textarea>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmClientContact', [
        function() {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    modelContact: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.contactForm = formCtrl;

                    scope.$watch('contactForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelContact.dirty = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-3"\
                 ng-class="{\'has-error\': (contactForm.$dirty || modelContact.id) && contactForm.contact_type.$invalid}">\
                <label for="contact_type[[idPostfix]]" class="control-label">Тип</label>\
                <ui-select class="form-control" id="contact_type[[idPostfix]]" name="contact_type" theme="select2"\
                    ng-model="modelContact.contact_type" ng-disabled="!edit_mode()" ng-required="contactForm.$dirty"\
                    ref-book="rbContactType">\
                    <ui-select-match placeholder="не выбрано">[[ $select.selected.name ]]</ui-select-match>\
                    <ui-select-choices repeat="rt in ($refBook.objects | filter: $select.search) track by rt.id">\
                        <span ng-bind-html="rt.name | highlight: $select.search"></span>\
                    </ui-select-choices>\
                </ui-select>\
            </div>\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': (contactForm.$dirty || modelContact.id) && contactForm.contact_text.$invalid}">\
                <label for="contact_text[[idPostfix]]" class="control-label">Номер</label>\
                <input type="text" class="form-control" id="contact_text[[idPostfix]]" name="contact_text"\
                       autocomplete="off" placeholder=""\
                       ng-model="modelContact.contact_text" ng-disabled="!edit_mode()" ng-required="contactForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-5"\
                 ng-class="{\'has-error\': (contactForm.$dirty || modelContact.id) && contactForm.contact_notes.$invalid}">\
                <label for="contact_notes[[idPostfix]]" class="control-label">Примечание</label>\
                <input type="text" class="form-control" id="contact_notes[[idPostfix]]" name="contact_notes"\
                       autocomplete="off" placeholder=""\
                       ng-model="modelContact.notes" ng-disabled="!edit_mode()" ng-required="false"/>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ]).
    directive('wmRelationTypeRb', [function() {
        return {
            restrict: 'E',
            replace: true,
            require: 'ngModel',
            scope: {
                $client: '=client',
                $relative: '=relative',
                $direct: '=direct'
            },
            template:
                '<select class="form-control" ref-book="rbRelationType"\
                    ng-options="item as $fmt(item) for item in ($refBook.objects | filter: $sexFilter) track by item.id">\
                 </select>',
            link: function (scope, element, attrs, ngModel) {
                scope.$sexFilter = function (item) {
                    if (scope.$client && scope.$client.sex && item) {
                        if (scope.$relative && scope.$relative.sex) {
                            return !(scope.$direct && ((item.leftSex != 0 && item.leftSex != scope.$client.sex.id) || (item.rightSex != 0 && item.rightSex != scope.$relative.sex.id)) ||
                                (!scope.$direct && ((item.rightSex != 0 && item.rightSex != scope.$client.sex.id) || (item.leftSex != 0 && item.leftSex != scope.$relative.sex.id)) ))
                        } else {
                            return !(scope.$direct && (item.leftSex != 0 && item.leftSex != scope.$client.sex.id) ||
                                (!scope.$direct && (item.rightSex != 0 && item.rightSex != scope.$client.sex.id) ))
                        }
                    }
                };
                scope.$fmt = function (item) {
                    return scope.$direct ? item.leftName + ' → ' + item.rightName : item.rightName + ' ← ' + item.leftName;
                };
                scope.$watchCollection(function() {
                    return [scope.$relative, scope.$direct];
                }, function(n, o) {
                    if (n !== o) {
                        ngModel.$setValidity('sexMatch', scope.$sexFilter(ngModel.$modelValue));
                    }
                });
                ngModel.$parsers.unshift(function(viewValue) {
                    if (viewValue && scope.$sexFilter(viewValue)) {
                        ngModel.$setValidity('sexMatch', true);
                        return viewValue;
                    } else {
                        ngModel.$setValidity('sexMatch', false);
                        return undefined;
                    }
                });
            }
        }
    }]).
    directive('wmClientsShort', ['$http', function ($http) {
        return {
            restrict: 'E',
            replace: true,
            require: '^ngModel',
            template:
                '<input type="text" class="form-control" autocomplete="off" placeholder="Пациент" \
                    typeahead="client as $fmt(client) for client in search_clients($viewValue)" \
                    typeahead-wait-ms="500" typeahead-min-length="2" typeahead-editable="false"/>',
            link: function (scope, element, attributes, ngModel) {
                scope.$fmt = function (client) {
                    return (client) ? (client.full_name + ' (' + client.birth_date + ')') : ('-');
                };
                scope.search_clients = function (query) {
                    return $http.get(url_client_search, {
                        params: {
                            q:query,
                            short: true
                        }
                    }).then(function (res) {
                        return res.data.result;
                    });
                }
            }
        }
    }]).
    directive('wmClientRelation', [
        function() {
            return {
                restrict: 'E',
                require: '^form',
                scope: {
                    idPostfix: '@',
                    modelRelation: '=',
                    modelClient: '=',
                    edit_mode: '&editMode'
                },
                link: function(scope, elm, attrs, formCtrl) {
                    scope.relationForm = formCtrl;

                    scope.$watch('relationForm.$dirty', function(n, o) {
                        if (n !== o) {
                            scope.modelRelation.dirty = n;
                        }
                    });
                },
                template:
'<div class="panel panel-default">\
    <div class="panel-body">\
        <div class="row">\
            <div class="form-group col-md-4"\
                 ng-class="{\'has-error\': (relationForm.$dirty || modelRelation.id) && relationForm.rel_type.$invalid}">\
                <label for="rel_type[[idPostfix]]" class="control-label">Тип</label>\
                <wm-relation-type-rb class="form-control" id="rel_type[[idPostfix]]" name="rel_type"\
                    client="modelClient" relative="modelRelation.relative" direct="modelRelation.direct"\
                    ng-model="modelRelation.rel_type"\
                    ng-disabled="!edit_mode()" ng-required="relationForm.$dirty"/>\
            </div>\
            <div class="form-group col-md-1">\
                <label for="rel_direct[[idPostfix]]" class="control-label">Связь</label>\
                <button type="button" class="btn btn-primary form-control" id="rel_direct[[idPostfix]]"\
                    ng-model="modelRelation.direct" ng-disabled="!edit_mode()" btn-checkbox\
                    title="[[(modelRelation.direct) ? \'Прямая\' : \'Обратная\']]">\
                    <span class="glyphicon glyphicon-arrow-[[(modelRelation.direct) ? \'right\' : \'left\']]"></span>\
                </button>\
            </div>\
            <div class="form-group col-md-7"\
                 ng-class="{\'has-error\': (relationForm.$dirty || modelRelation.id) && relationForm.rel_relative.$invalid}">\
                <label for="rel_relative[[idPostfix]]" class="control-label">Родственник</label>\
                <wm-clients-short class="form-control" id="rel_relative[[idPostfix]]" name="rel_relative"\
                    ng-model="modelRelation.relative" ng-disabled="!edit_mode()" ng-required="relationForm.$dirty"/>\
            </div>\
        </div>\
    </div>\
</div>'
            };
        }
    ])
;
