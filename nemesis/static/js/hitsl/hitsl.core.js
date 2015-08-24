/**
 * Created by mmalkov on 12.02.15.
 */

angular.module('hitsl.core', [])
.service('MessageBox', ['$modal', function ($modal) {
    return {
        info: function (head, message) {
            var MBController = function ($scope) {
                $scope.head_msg = head;
                $scope.message = message;
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-MessageBox-info.html',
                controller: MBController
            });
            return instance.result;
        },
        error: function (head, message) {
            var MBController = function ($scope) {
                $scope.head_msg = head;
                $scope.message = message;
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-MessageBox-error.html',
                controller: MBController
            });
            return instance.result;
        },
        question: function (head, question) {
            var MBController = function ($scope) {
                $scope.head_msg = head;
                $scope.question = question;
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-MessageBox-question.html',
                controller: MBController
            });
            return instance.result;
        }
    };
}])
.service('WindowCloseHandler', ['$timeout', '$rootScope', '$window', '$q', function ($timeout, $rootScope, $window, $q) {
    var self = this,
        handlers = [],
        user_handlers = [],
        onBeforeUnloadFired = false,
        resetOnBeforeUnload = function () {
            onBeforeUnloadFired = false;
        },
        call = function () {
            var args = _.toArray(arguments), f = args.shift();
            return f.apply(this, args);
        },
        changeStart = function (event) {
            if (onBeforeUnloadFired) return;
            event = event || $window.event;
            onBeforeUnloadFired = true;
            $timeout(resetOnBeforeUnload);
            var userHandlersResults = [];
            if (!self.suppressUserhandlers) {
                userHandlersResults = _.filter(_.map(user_handlers, call));
                if (userHandlersResults.length > 0) {
                    return event.returnValue = userHandlersResults.join('\n');
                }
            }
        },
        changeEnd = function (event) {
            // Здесь могут обработаться только синхронные обработчики. И то, если повезёт.
            event = event || $window.event;
            _.each(handlers, call);
        };
    this.addHandler = function (handler) {
        handlers.push(handler);
    };
    this.addUserHandler = function (handler) {
        user_handlers.push(handler);
    };
    this.suppressUserhandlers = false;
    $window.onbeforeunload = changeStart;
    $window.onunload = changeEnd; // Эта штука не работает на Mozilla'х
}])
.service('Deferred', ['$timeout', function ($timeout) {
    var self = this,
        ensurePromise = function (obj) {
            if (_.has(obj, 'addResolve')) {
                return obj;
            } else if (_.has(obj, 'then')) {
                var wrapper = self.new();
                obj.then(
                    wrapper.resolve,
                    wrapper.reject,
                    wrapper.notify,
                    wrapper.error,
                    wrapper.cancel
                );
                return wrapper.promise;
            } else {
                return self.resolve(obj);
            }
        },
        timed = function (f) {
            return function (result) {
                return ensurePromise(
                    $timeout(function () {
                        return f(result);
                    })
                )
            }
        };
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
                then: function (resolve, reject, notify, error, cancel) {
                    if (resolve) add(resolve_chain, resolve);
                    if (reject) add(reject_chain, reject);
                    if (notify) add(notify_chain, notify);
                    if (error) add(error_chain, error);
                    if (cancel) add(cancel_chain, cancel);
                    return this;
                },
                anyway: function (anyway) {
                    add(resolve_chain, anyway);
                    add(reject_chain, anyway);
                    return this;
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
            ensurePromise(promise)
                .then(
                function(value) {
                    results[key] = value;
                    if (!(--counter)) timed(deferred.resolve)(results);
                    return value;
                },
                timed(deferred.reject),
                timed(deferred.notify),
                timed(deferred.error),
                timed(deferred.cancel)
            )
        });
        if (counter === 0) {
            deferred.resolve(results);
        }
        return deferred.promise;
    };
}])
.factory('OneWayEvent', [function () {
    var OneWayEvent = function () {
        var handlers = {};
        this.send = function () {
            var args = _.toArray(arguments),
                name = args.shift(),
                flist = handlers[name] || [];
            return _.map(flist, function (f) {return f.apply(undefined, args)})
        };
        this.eventSource = {
            subscribe: function (name, handler) {
                var handlers_list = handlers[name] = handlers[name] || [];
                if (!handlers_list.has(handler)) handlers_list.push(handler);
                return this;
            }
        };
    };
    return OneWayEvent;
}])
.service('IdleTimer', ['$window', '$document', 'WMConfig', 'IdleUserModal', 'ApiCalls', 'WindowCloseHandler', function ($window, $document, WMConfig, IdleUserModal, ApiCalls, WindowCloseHandler) {
    var user_activity_events = 'mousemove keydown DOMMouseScroll mousewheel mousedown touchstart touchmove scroll',
        on_user_activity = _.throttle(postpone_everything, 10000),
        debounced_logout_warning = _.debounce(show_logout_warning, WMConfig.settings.user_idle_timeout * 1000),
        token_regex = new RegExp('(?:(?:^|.*;\\s*)' + WMConfig.cas_token_name + '\\s*\\=\\s*([^;]*).*$)|^.*$');
        var token = $window.document.cookie.replace(token_regex, "$1");
    function reload_page() {
        WindowCloseHandler.suppressUserhandlers = true;
        $window.location.reload(true);
    }
    function cas(url) {
        return ApiCalls.coldstar(
            'POST',
            url,
            { token: token },
            undefined,
            { silent: true }
        )
    }
    function prolong_token() {
        return cas(WMConfig.url.coldstar.cas_prolong_token).addReject(reload_page)
    }
    function check_token() {
        return cas(WMConfig.url.coldstar.cas_check_token).addReject(reload_page)
    }
    function logout() {
        return cas(WMConfig.url.coldstar.cas_release_token).then(reload_page, reload_page, reload_page)
    }
    function postpone_everything () {
        debounced_logout_warning();
        prolong_token();
    }
    function show_logout_warning() {
        _set_tracking(false);
        check_token().addReject(reload_page).addResolve(function (cas_result) {
            var time_left = Math.min(cas_result.ttl, WMConfig.settings.logout_warning_timeout),
                deadline = cas_result.ttl - time_left;
            IdleUserModal.open(Math.floor(time_left)).then(
                function () {
                    prolong_token().addResolve(_set_tracking, true).addError(reload_page);
                },
                function () {
                    check_token().addError(reload_page).addResolve(function (result) {
                        if (result.ttl > deadline + 1) {
                            _set_tracking(true);
                            on_user_activity()
                        } else {
                            logout();
                        }
                    });
                });
        })
    }
    function _set_tracking(on) {
        $document.find('body')[(on)?'on':'off'](user_activity_events, on_user_activity)
    }

    return {
        start: function () {
            on_user_activity();
            _set_tracking(true);
        }
    }
}])
.service('IdleUserModal', ['$modal', 'WMConfig', 'TimeoutCallback', function ($modal, WMConfig, TimeoutCallback) {
    return {
        open: function (time_left) {
            var IUController = function ($scope) {
                $scope.countdown = time_left !== undefined ? time_left : WMConfig.settings.logout_warning_timeout;
                $scope.idletime_minute = Math.floor(WMConfig.settings.user_idle_timeout / 60) || 1;
                $scope.timer = new TimeoutCallback(function () {
                    if ($scope.countdown <= 0) {
                        $scope.$dismiss('Так и не вернулся...');
                    } else {
                        $scope.countdown--;
                    }
                }, 1E3);
                $scope.cancel_idle = function () {
                    $scope.timer.kill();
                    $scope.$close('Успел!');
                };

                $scope.timer.start_interval($scope.countdown + 1, 1E3);
            };
            var instance = $modal.open({
                templateUrl: '/WebMis20/modal-IdleUser.html',
                controller: IUController,
                backdrop: 'static',
                windowClass: 'idle-modal'
            });
            return instance.result;
        }
    };
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-IdleUser.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <h3 class="modal-title">Внимание!</h3>\
        </div>\
        <div class="modal-body">\
            <div>\
              <p>Вы неактивны более <b>[[idletime_minute]]</b> минут.<br>\
                Автоматический выход из системы произойдет через:</p>\
                <h1 class="idle-countdown"><span class="label label-danger">[[countdown]]</span><small> секунд</small></h1>\
            </div>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-success btn-lg" ng-click="cancel_idle()">Остаться в системе</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-info.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-error.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$dismiss()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-question.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="question"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
        </div>'
    );
}])
.config(function ($httpProvider) {
    $httpProvider.interceptors.push('requestInterceptor');
})
.factory('requestInterceptor', function ($q, $rootScope) {
    $rootScope.pendingRequests = 0;
    return {
        'request': function (config) {
            if (!config.silent) {
                $rootScope.pendingRequests++;
            }
            return config || $q.when(config);
        },

        'requestError': function(rejection) {
            if (!safe_traverse(rejection, 'silent')) {
                $rootScope.pendingRequests--;
            }
            return $q.reject(rejection);
        },

        'response': function(response) {
            if (!response.config.silent) {
                $rootScope.pendingRequests--;
            }
            return response || $q.when(response);
        },

        'responseError': function(rejection) {
            if (!rejection.config.silent) {
                $rootScope.pendingRequests--;
            }
            return $q.reject(rejection);
        }
    }
})
;

angular.module('hitsl.ui', [
    'ui.bootstrap',          // /static/angular.js/ui-bootstrap-tpls.js
    'ui.select',             // /static/angular-ui-select/select.js
    'ngSanitize',            // /static/js/angular-sanitize.js
    'sf.treeRepeat',         // /static/angular.js/angular-tree-repeat.js
    'ui.mask',               // /static/angular-ui-utils/mask_edited.js
    'formstamp',             // /static/angular-formstamp/formstamp.js
    'mgcrea.ngStrap.affix',  // /static/js/angular-strap.js
    'duScroll',              // /static/angular-scroll/angular-scroll.js
    'rcWizard',
    'nvd3ChartDirectives',
    'legendDirectives',
    'ui.calendar'
])
;