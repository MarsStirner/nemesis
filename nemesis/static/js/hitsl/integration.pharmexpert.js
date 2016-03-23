/**
 * Created by mmalkov on 20.01.16.
 */

angular.module('hitsl.core')
.service('PharmExpertIntegration', ['$modal', '$http', '$q', '$rootScope', '$sce', 'WMConfig', 'NotificationService', function ($modal, $http, $q, $rootScope, $sce, WMConfig, NotificationService) {

    var security_key = '8ab87e9fe50512461b04d16e97b88bc9857387d32c9b2f9a577c2928';

    /* Extracted from AngularJS */
    function forEachSorted(obj, iterator, context) {
        var keys = Object.keys(obj).sort();
        for (var i = 0; i < keys.length; i++) {
            iterator.call(context, obj[keys[i]], keys[i]);
        }
        return keys;
    }
    function encodeUriQuery(val, pctEncodeSpaces) {
        return encodeURIComponent(val).
        replace(/%40/gi, '@').
        replace(/%3A/gi, ':').
        replace(/%24/g, '$').
        replace(/%2C/gi, ',').
        replace(/%3B/gi, ';').
        replace(/%20/g, (pctEncodeSpaces ? '%20' : '+'));
    }
    function serializeValue(v) {
        if (_.isObject(v)) {
            return _.isDate(v) ? v.toISOString() : angular.toJson(v);
        }
        return v;
    }

    /* Backport from AngularJS 1.4 */
    function jQueryLikeParamSerializer(params) {
        if (!params) return '';
        var parts = [];
        serialize(params, '', true);
        return parts.join('&');

        function serialize(toSerialize, prefix, topLevel) {
            if (toSerialize === null || _.isUndefined(toSerialize)) return;
            if (_.isArray(toSerialize)) {
                _.forEach(toSerialize, function(value) {
                    serialize(value, prefix + '[]');
                });
            } else if (_.isObject(toSerialize) && !_.isDate(toSerialize)) {
                forEachSorted(toSerialize, function(value, key) {
                    serialize(value, prefix +
                        (topLevel ? '' : '[') +
                        key +
                        (topLevel ? '' : ']'));
                });
            } else {
                parts.push(encodeUriQuery(prefix) + '=' + encodeUriQuery(serializeValue(toSerialize)));
            }
        }
    }
    this.check = function (data) {
        if (data.medicaments.length < 1) {return $q.reject(null)}
        var defer = $q.defer();
        function process(response) {
            if (response.status != 200) {
                var text = (response.status === 500) ? 'Внутренняя ошибка сервера.<br/>{0}' : 'Ошибка.<br/>{0}';
                NotificationService.notify(
                    response.status,
                    text.format(response.textStatus),
                    'danger'
                );
                console.error(text);
                defer.reject();
            } else {
                defer.resolve(response.data);
            }
            return response;
        }
        var config = {
            method: 'POST',
            url: '{0}?security_key={1}'.format(
                WMConfig.url.pharmexpert.get_info_preparation,
                WMConfig.local_config.pharmexpert.security_key
            ),
            data: jQueryLikeParamSerializer(data),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        };
        $http(config).then(process, process);
        return defer.promise;
    };
    this.modal = function (config) {
        var scope = $rootScope.$new(true);
        scope.url = $sce.trustAsResourceUrl(config.url);
        $modal.open({
            templateUrl: '/WebMis20/modal-pharmexpert.html',
            backdrop : 'static',
            scope: scope,
            size: 'lg'
        });
    };
    this.enabled = function () {
        return WMConfig.local_config.pharmexpert.enabled;
    };
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put(
        '/WebMis20/modal-pharmexpert.html',
'<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
    <button type="button" class="close" ng-click="$dismiss(\'cancel\')">&times;</button>\
    <h4 class="modal-title" id="myModalLabel">Назначение препарата</h4>\
</div>\
<div class="modal-body">\
    <iframe ng-src="[[ url ]]" seamless="seamless" style="min-height: 500px"></iframe>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-default" ng-click="$dismiss()">Закрыть</button>\
</div>'
    );
}])
;
