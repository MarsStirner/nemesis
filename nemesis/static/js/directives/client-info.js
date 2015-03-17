'use strict';

angular.module('WebMis20.directives')
.directive('wmClientInfo', ['$filter', '$window', function ($filter, $window) {
    return {
        restrict: 'E',
        scope: {
            client: '='
        },
        link: function (scope, element, attrs) {
            scope.format_doc = function (docs) {
                return docs && docs.length ? docs[0].doc_text : '&nbsp;';
            };
            scope.format_address = function (address) {
                return address ? address.text_summary : '&nbsp;';
            };
            scope.format_code = function (code) {
                return code ? ('' + code) : '&nbsp;';
            };
            scope.format_birth_date = function (birth_date) {
                return $filter('asDate')(birth_date) || '&nbsp;';
            };
            scope.format_age = function (age) {
                return age || '&nbsp;';
            };
            scope.format_sex = function (sex) {
                return sex || '&nbsp;';
            };
            scope.open_patient_info = function(client_id) {
                $window.open(url_for_patien_info_full + '?client_id=' + client_id, '_blank');
            };
        },
        template:
    '<div class="well well-sm">\
        <div class="row">\
            <div class="col-md-9">\
                <dl class="dl-horizontal novmargin">\
                    <dt ng-if="client.contacts.length">Контакты:</dt>\
                        <dd ng-if="client.contacts.length">\
                            <wm-client-contacts contacts="client.contacts"></wm-client-contacts>\
                        </dd>\
                    <dt>Адрес регистрации:</dt><dd ng-bind-html="format_address(client.reg_address)"></dd>\
                    <dt>Адрес проживания:</dt><dd ng-bind-html="format_address(client.live_address)"></dd>\
                    <dt>Документ:</dt><dd ng-bind-html="format_doc(client.id_docs)"></dd>\
                    <dt>Медицинский полис:</dt>\
                        <dd ng-if="client.compulsory_policy.id" ng-bind="client.compulsory_policy.policy_text"></dd>\
                        <dd ng-repeat="pol in client.voluntary_policies">[[pol.policy_text]]</dd>\
                </dl>\
            </div>\
            <div class="col-md-3">\
                <dl class="dl-horizontal novmargin pull-right">\
                    <dt>Код пациента:</dt><dd ng-bind-html="format_code(client.info.id)"></dd>\
                    <dt>Дата рождения:</dt><dd ng-bind-html="format_birth_date(client.info.birth_date)"></dd>\
                    <dt>Возраст:</dt><dd ng-bind-html="format_age(client.info.age)"></dd>\
                    <dt>Пол:</dt><dd ng-bind-html="format_sex(client.info.sex.name)"></dd>\
                </dl>\
                <button class="btn btn-sm btn-primary pull-right vmargin10" ng-click="open_patient_info(client.info.id)">Детальнее</button>\
            </div>\
        </div>\
    </div>'
    };
}])
.directive('wmClientContacts', [function () {
    return {
        restrict: 'E',
        scope: {
            contacts: '='
        },
        link: function (scope, element, attrs) {
            scope.show_all = false;
            scope.more_than_one = function () {
                return scope.contacts.length > 1;
            };
            scope.change_state = function () {
                scope.show_all = !scope.show_all;
            };
            scope.format_contact = function (contact) {
                var contact_val = '';
                switch (contact.contact_type.code) {
                    // телефоны как иконки
                    case '01':
                    case '02':
                    case '03':
                        contact_val = '<span class="glyphicon glyphicon-phone-alt"></span> {0}'.format(contact.contact_text);
                        break;
                    // email - maito
                    case '04':
                        contact_val = '<a href="mailto:{0}"><span class="glyphicon glyphicon-envelope"></span> {0}</a>'
                            .format(contact.contact_text);
                        break;
                    // остальное - текст
                    default:
                        contact_val = '{0}: {1}'.format(contact.contact_type.name, contact.contact_text);
                        break;
                }
                return '<span class="nowrap">{0}</span>{ (|1|)}'.formatNonEmpty(contact_val, contact.notes);
            };
        },
        template:
'<div>\
    <ul class="list-unstyled">\
        <li ng-repeat="contact in contacts" ng-show="$first || show_all">\
            <span ng-bind-html="format_contact(contact)" bind-once></span>\
            <span ng-show="$first">\
                <a href="javascript:void(0);" ng-show="more_than_one()" ng-click="change_state()"\
                    ng-bind="show_all ? \'[скрыть]\' : \'[ещё]\'"></a>\
            </span>\
        </li>\
    </ul>\
</div>'
    };
}]);