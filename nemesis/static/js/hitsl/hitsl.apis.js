/**
 * Created by mmalkov on 19.03.15.
 */


angular.module('hitsl.core')
.service('ApiCalls', function ($q, $http, NotificationService) {
    this.wrapper = function (method, url, params, data) {
        var defer = $q.defer();
        $http({
            method: method,
            url: url,
            params: params,
            data: data
        })
        .success(function (data) {
            defer.resolve(data.result)
        })
        .error(function (data, code) {
            var text = (code === 500) ? 'Внутренняя ошибка сервера.<br/>{0}' : 'Ошибка.<br/>{0}';
            NotificationService.notify(
                code,
                text.format(data.meta.name),
                'danger'
            );
            defer.reject(data.meta)
        });
        return defer.promise;
    };
})
.service('NotificationService', function () {
    var self = this;
    var recompilers = [];
    this.notifications = [];
    this.notify = function (code, message, severity) {
        var id = Math.floor(Math.random() * 65536);
        self.notifications.push({
            id: id,
            code: code,
            message: message,
            severity: severity
        });
        notify_recompilers();
        return id;
    };
    this.dismiss = function (id) {
        self.notifications = self.notifications.filter(function (notification) {
            return notification.id != id;
        });
        notify_recompilers();
    };
    this.register = function (recompile_function) {
        recompilers.push(recompile_function);
    };
    var notify_recompilers = function () {
        recompilers.forEach(function (recompile) {
            recompile(self.notifications);
        });
    }
})
.directive('alertNotify', function (NotificationService, $compile) {
    return {
        restrict: 'AE',
        scope: {},
        link: function (scope, element, attributes) {
            var template =
                '<div class="alert alert-{0}" role="alert">\
                    <button type="button" class="close" ng-click="$dismiss({2})">\
                        <span aria-hidden="true">&times;</span>\
                        <span class="sr-only">Close</span>\
                    </button>\
                    {1}\
                </div>';
            scope.$dismiss = function (id) {
                NotificationService.dismiss(id);
            };
            function compile (arg) {
                if (_.isArray(arg)) {
                    return arg.map(compile).join('');
                } else if (typeof arg === 'string') {
                    return arg;
                } else if (typeof arg !== 'object') {
                    return '';
                }
                var wrapper = '{0}';
                if (arg.hasOwnProperty('bold') && arg.bold) {
                    wrapper = '<b>{0}</b>'.format(wrapper)
                }
                if (arg.hasOwnProperty('italic') && arg.bold) {
                    wrapper = '<i>{0}</i>'.format(wrapper)
                }
                if (arg.hasOwnProperty('underline') && arg.bold) {
                    wrapper = '<u>{0}</u>'.format(wrapper)
                }
                if (arg.hasOwnProperty('link')) {
                    wrapper = '<a href={0}>{1}</a>'.format(arg.link, wrapper);
                } else if (arg.hasOwnProperty('click')) {
                    do {
                        var uniq = _.random(0x100000000);
                    } while (scope.func_map.hasOwnProperty(uniq));
                    scope.func_map[uniq] = arg.click;
                    wrapper = '<a style="cursor:pointer" ng-click="func_map[{0}]()">{1}</a>'.format(String(uniq), wrapper)
                }
                if (arg.hasOwnProperty('text')) {
                    return wrapper.format(compile(arg.text));
                }
                return '';
            }
            function recompile (n) {
                scope.func_map = {};
                var html = n.map(function (notification) {
                    return template.format(
                        notification.severity || 'info',
                        compile(notification.message),
                        notification.id
                    )
                }).join('\n');
                var replace_element = $('<div class="abs-alert">{0}</div>'.format(html));
                element.replaceWith(replace_element);
                $compile(replace_element)(scope);
                element = replace_element;
            }
            NotificationService.register(recompile);
        }
    }
})
;
