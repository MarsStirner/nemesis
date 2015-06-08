/**
 * Created by mmalkov on 19.03.15.
 */


angular.module('hitsl.core')
.service('ApiCalls', ['$q','$http', 'NotificationService', 'Deferred', function ($q, $http, NotificationService, Deferred) {
    this.wrapper = function (method, url, params, data) {
        var defer = $q.defer();
        function process(response) {
            if (response.status != 200 || response.data.meta.code != 200) {
                var text = (response.status === 500) ? 'Внутренняя ошибка сервера.<br/>{0}' : 'Ошибка.<br/>{0}';
                NotificationService.notify(
                    response.data.meta.code,
                    text.format(data.meta.name),
                    'danger'
                );
                defer.reject(response.data.meta);
            } else {
                defer.resolve(response.data.result);
            }
            return response;
        }
        $http({
            method: method,
            url: url,
            params: params,
            data: data
        })
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
.service('Deferred', ['$timeout', function ($timeout) {
    this.new = function () {
        var canceller = arguments[0],
            done = false,
            value = undefined,
            resolve_chain = [],
            reject_chain = [],
            notify_chain = [],
            error_chain = [],
            cancel_chain = [],
            chain = null,
            add = function () {
                var args = _.toArray(arguments),
                    chain = args.shift(),
                    callback = args.shift();
                chain.push({
                    cb: callback,
                    args: args,
                    this: this
                });
                if (done) {
                    $timeout(promote)
                }
                return this;
            },
            promote = function () {
                var object;
                while (chain.length > 0) {
                    object = chain.shift();
                    if (object.cb && _.has(object, 'args')) {
                        try {
                            value = object.cb.apply(object.this, [value].concat(object.args))
                        } catch (e) {
                            chain = error_chain;
                            value = e;
                        }
                    }
                }
            },
            notify = function (with_value) {
                _.each(notify_chain, function (object) {
                    object.cb.apply(object.this, [with_value].concat(object.args));
                })
            },
            finish = function (with_chain, with_value) {
                if (done) throw 'Already done!';
                chain = with_chain;
                value = with_value;
                $timeout(promote).then(set_done);
            },
            cancel = function () {
                if (done) throw 'Already done!';
                if (canceller) value = canceller();
                chain = cancel_chain;
                $timeout(promote).then(set_done);
            },
            set_done = function () {
                done = true;
            },
            promise = {
                addResolve: _.partial(add, resolve_chain),
                addReject: _.partial(add, reject_chain),
                addNotify: _.partial(add, notify_chain),
                addError: _.partial(add, error_chain),
                addCancel: _.partial(add, cancel_chain),
                then: function (resolve, reject, error) {
                    if (resolve) add(resolve_chain, resolve);
                    if (reject) add(reject_chain, reject);
                    if (error) add(error_chain, error);
                },
                cancel: cancel
            };
        return {
            promise: promise,
            resolve: _.partial(finish, resolve_chain),
            reject: _.partial(finish, reject_chain),
            notify: notify,
            error: _.partial(finish, error_chain),
            cancel: cancel
        }
    };
    this.resolve = function (value) {
        return this.new().resolve(value).promise;
    };
    this.reject = function (value) {
        return this.new().reject(value).promise;
    };
    this.all = function (promises) {
        var deferred = this.new(),
            counter = 0,
            results = _.isArray(promises) ? [] : {};

        _.each(promises, function(promise, key) {
            counter++;
            promise
                .addResolve(function(value) {
                    results[key] = value;
                    if (!(--counter)) $timeout(_.partial(deferred.resolve, results));
                    return value;
                })
                .addReject(function(reason) {
                    $timeout(_.partial(deferred.reject, reason));
                    return reason;
                })
                .addError(function (error) {
                    $timeout(_.partial(deferred.error, error));
                    return error;
                })
                .addCancel(function (reason) {
                    $timeout(_.partial(deferred.cancel, reason));
                    return reason;
                })
        });

        if (counter === 0) {
            deferred.resolve(results);
        }

        return deferred.promise;
    }

}])
.directive('alertNotify', function (NotificationService, $compile) {
    return {
        restrict: 'AE',
        scope: {},
        link: function (scope, element, attributes) {
            var template =
                '<div class="alert alert-{0}" role="alert" {3}>\
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
