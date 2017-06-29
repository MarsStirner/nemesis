/**
 * Created by mmalkov on 19.03.15.
 */


angular.module('hitsl.core')
.service('ApiCalls', ['$q','$http', 'NotificationService', 'Deferred', function ($q, $http, NotificationService, Deferred) {
    this.wrapper = function (method, url, params, data, options) {
        if (options === undefined) options = {};
        var defer = $q.defer();
        function process(response) {
            var data_meta_status = safe_traverse(response.data, ['meta', 'code'], response.status),
                data_meta_name = safe_traverse(response.data, ['meta', 'name'], 'Внутренняя ошибка сервера'),
                data_meta = safe_traverse(response.data, ['meta'], {code: data_meta_status, name: data_meta_name});
            if (!_.has(response.data, 'meta')) {
                console.log('Strange response');
                console.log([method, url, params, data, options]);
                console.log(response);
            }
            if (response.status != 200 || data_meta_status != 200) {
                if (!options.wo_notify) {
                    NotificationService.notify(
                        data_meta_status,
                        'Ошибка.<br/>{0}'.format(data_meta_name),
                        'danger'
                    );
                }
                defer.reject(data_meta);
            } else {
                defer.resolve(response.data.result);
            }
            return response;
        }
        if (!angular.isString(url)) { throw 'Неверное значение URL запроса: {0}'.format(url) }
        $http(angular.extend({}, options, {
            method: method,
            url: url,
            params: params,
            data: data,
            headers: {
                'X-Requested-With' :'XMLHttpRequest'
            }
        }))
        .then(process, process);
        return defer.promise;
    };
    this.coldstar = function (method, url, params, data, options) {
        var defer = Deferred.new();
        function process(response) {
            var data = response.data;
            if (response.status < 100 || !response.data) {
                NotificationService.notify(
                    response.status,
                    'Неизвестная ошибка<br/><strong>{0}</strong>'.format(response.status),
                    'danger',
                    true
                );
                return defer.error(response);
            }
            if (_.has(data, 'exception')) {
                NotificationService.notify(
                    data.exception,
                    'Ошибка сервера<br/><strong>{0}</strong><br/>{1}'.format(data.exception, data.message),
                    'danger',
                    true
                )
            }
            if (data.success) {
                defer.resolve(data);
            } else {
                defer.reject(data);
            }
            return response;
        }
        $http(angular.extend({}, options, {
            method: method,
            url: url,
            params: params,
            data: data
        })).then(process, process);
        return defer.promise;
    }
}])
.service('NotificationService', ['TimeoutCallback', function (TimeoutCallback) {
    var self = this;
    var recompilers = [];
    this.notifications = [];
    this.timeouts = {};
    this.notify = function (code, message, severity, to) {
        if (to === true) to = 3000;
        else if (!angular.isNumber(to)) to = undefined;
        var id = Math.floor(Math.random() * 65536);
        self.notifications.unshift({
            id: id,
            code: code,
            message: message,
            severity: severity,
            to: to
        });
        if (to) {
            this.timeouts[id] = new TimeoutCallback(_.partial(this.dismiss, id), to);
            this.timeouts[id].start();
        }
        notify_recompilers();
        return id;
    };
    this.dismiss = function (id) {
        self.notifications = self.notifications.filter(function (notification) {
            return notification.id != id;
        });
        notify_recompilers();
    };
    this.cancelTO = function (id) {
        this.timeouts[id].kill();
    };
    this.register = function (recompile_function) {
        recompilers.push(recompile_function);
    };
    var notify_recompilers = function () {
        recompilers.forEach(function (recompile) {
            recompile(self.notifications);
        });
    }
}])
.directive('alertNotify', function (NotificationService, $compile) {
    return {
        restrict: 'AE',
        scope: {},
        link: function (scope, element, attributes) {
            var template =
                '<div class="alert alert-{0} novmargin" role="alert" {3}>\
                    <button type="button" class="close" ng-click="$dismiss({2})">\
                        <span aria-hidden="true">&times;</span>\
                        <span class="sr-only">Close</span>\
                    </button>\
                    <span style="margin-right: 10px">{1}</span>\
                </div>';
            scope.$dismiss = function (id) {
                NotificationService.dismiss(id);
            };
            function compile (arg) {
                var _arg = _(arg);
                if (_.isArray(arg)) {
                    return arg.map(compile).join('');
                } else if (typeof arg === 'string') {
                    return arg;
                } else if (typeof arg !== 'object') {
                    return '';
                }
                var wrapper = '{0}';
                if (_arg.has('bold') && arg.bold) {
                    wrapper = '<b>{0}</b>'.format(wrapper)
                }
                if (_arg.has('italic') && arg.bold) {
                    wrapper = '<i>{0}</i>'.format(wrapper)
                }
                if (_arg.has('underline') && arg.bold) {
                    wrapper = '<u>{0}</u>'.format(wrapper)
                }
                if (_arg.has('link')) {
                    //noinspection HtmlUnknownTarget
                    wrapper = '<a href="{0}">{1}</a>'.format(arg.link, wrapper);
                } else if (_arg.has('click')) {
                    do {
                        var uniq = _.random(0x100000000);
                    } while (scope.func_map.hasOwnProperty(uniq));
                    scope.func_map[uniq] = arg.click;
                    wrapper = '<a style="cursor:pointer" ng-click="func_map[{0}]()">{1}</a>'.format(String(uniq), wrapper)
                }
                if (_arg.has('text')) {
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
                        notification.id,
                        notification.to ? 'ng-mouseover="onMouseOver({0})"'.format(notification.id): ''
                    )
                }).join('\n');
                var replace_element = $('<div class="abs-alert">{0}</div>'.format(html));
                element.replaceWith(replace_element);
                $compile(replace_element)(scope);
                element = replace_element;
            }
            NotificationService.register(recompile);
            scope.onMouseOver = function (id) {
                NotificationService.cancelTO(id);
            };
        }
    }
})
;
