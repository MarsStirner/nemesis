/**
 * Created by mmalkov on 12.02.15.
 */

angular.module('hitsl.core', [])
.service('CurrentUser', ['$http', function ($http) {
    var self = this;
    $http.get('/api/current-user.json').success(function (data) {
        angular.extend(self, data.result);
    });
    this.get_main_user = function () {
        return this.master || this;
    };
    this.has_right = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.get_user().rights)).length > 0;
    };
    this.has_role = function () {
        return [].clone.call(arguments).filter(aux.func_in(this.roles)).length > 0;
    };
    this.current_role_in = function () {
        return [].clone.call(arguments).has(this.current_role);
    };
}])
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
.service('IdleTimer', ['$http', '$log', '$document', '$window', 'TimeoutCallback', 'WMConfig', 'IdleUserModal',
    function ($http, $log, $document, $window, TimeoutCallback, WMConfig, IdleUserModal) {
        var last_ping_time = null,
            last_activity_time = null,
            token_expire_time = null,
            ping_timeout = get_ping_timeout(),
            user_activity_events = 'mousemove keydown DOMMouseScroll mousewheel mousedown touchstart touchmove scroll',
            ping_timer = new TimeoutCallback(ping_cas, ping_timeout),
            token_life_timer = new TimeoutCallback(check_show_idle_warning, null),
            _onUserAction = function() {
                last_activity_time = get_current_time();
            };

        function get_ping_timeout() {
            var idle_time = WMConfig.settings.user_idle_timeout,
                ping_to;
            if (9 < idle_time && idle_time <= 60) {
                ping_to = 10;
            } else if (60 < idle_time && idle_time <= 60 * 3) {
                ping_to = 20;
            } else if (60 * 3< idle_time && idle_time <= 60 * 5) {
                ping_to = 30;
            } else if (60 * 5 < idle_time && idle_time <= 60 * 10) {
                ping_to = 60;
            } else if (60 * 10 < idle_time) {
                ping_to = 120;
            } else {
                throw 'user_idle_timeout cannot be less than 10 seconds';
            }
            $log.debug('ping_timeout = {0} sec'.format(ping_to));
            return ping_to * 1E3;
        }
        function get_current_token() {
            return document.cookie.replace(/(?:(?:^|.*;\s*)CastielAuthToken\s*\=\s*([^;]*).*$)|^.*$/, "$1");
        }
        function get_current_time() {
            return new Date().getTime();
        }
        function set_token_expire_time(deadline, token_live_time) {
            token_expire_time = deadline;
            $log.debug('new token deadline: {0} / {1}'.format(token_expire_time, new Date(token_expire_time * 1E3)));
            set_warning_timer(token_live_time);
        }
        function process_logout() {
            $window.open(WMConfig.url.logout, '_self');
        }
        function _set_tracking(on) {
            if (on) {
                $document.find('body').on(user_activity_events, _onUserAction);
            } else {
                $document.find('body').off(user_activity_events, _onUserAction);
            }
        }
        function _init_warning_timer() {
            check_token().then(function (result) {
                if (result) {
                    set_token_expire_time(result.data.deadline, result.data.ttl);
                }
            });
        }
        function check_token() {
            // do not prolong
            return $http.post(WMConfig.url.coldstar.cas_check_token, {
                token: get_current_token()
            }, {
                silent: true
            }).then(function (result) {
                if (!result.data.success) {
                    $log.error('Could not check token lifetime ({0}). You should be logged off.'.format(result.data.message));
                    return null;
                }
                return result;
            }, function (result) {
                $log.error('Could not check token lifetime (unknown error). You should be logged off.');
                return null;
            });
        }
        function ping_cas() {
            var cur_time = get_current_time();
            $log.debug('ping about to fire...');
            if ((cur_time - last_activity_time) < ping_timeout) {
                $log.debug('prolonging token (current expire time: {0} / {1})'.format(token_expire_time, new Date(token_expire_time * 1E3)));
                $http.post(WMConfig.url.coldstar.cas_prolong_token, { // TODO: url
                    token: get_current_token()
                }, {
                    silent: true
                }).success(function (result) {
                    if (!result.success) {
                        // TODO: накапливать ошибки и делать логаут?
                        $log.error('Could not prolong token on ping timer ({0})'.format(result.message));
                    } else {
                        last_ping_time = cur_time;
                        set_token_expire_time(result.deadline, result.ttl);
                    }
                }).error(function () {
                    $log.error('Could not prolong token on ping timer (unknown error)');
                });
            }
        }
        function set_warning_timer(token_live_time) {
            token_live_time = Math.floor(token_live_time * 1E3);
            var warning_time = WMConfig.settings.logout_warning_timeout * 1E3,
                to;
            if (token_live_time < 0) {
                $log.error('Token has already expired!');
            } else if (token_live_time < warning_time) {
                $log.warn('Logout warning time is greater than token lifetime.');
            } else {
                to = token_live_time - warning_time;
                $log.info('show warning dialog in (msec): ' + to);
                token_life_timer.start(to);
            }
        }
        function check_show_idle_warning() {
            var cur_time = get_current_time();
            if ((cur_time - last_activity_time) < ping_timeout) {
                $log.debug('fire ping instead of showing warning dialog');
                ping_cas();
            } else {
                check_token().then(function (result) {
                    if (result && result.data.deadline <= token_expire_time) {
                        show_logout_warning();
                    } else {
                        $log.debug('User is active in another system.');
                        set_token_expire_time(result.data.deadline, result.data.ttl);
                    }
                });
            }
        }
        function show_logout_warning() {
            _set_tracking(false);
            ping_timer.kill();
            IdleUserModal.open()
                .then(function cancelIdle (result) {
                    $log.info('User has come back after idle.');
                    _set_tracking(true);
                    last_activity_time = get_current_time();
                    ping_cas();
                    ping_timer.start_interval();
                }, function logoutAfterIdle (result) {
                    check_token().then(function (result) {
                        if (result && token_expire_time <= result.data.deadline) {
                            $log.info('Warning timer has expired, but logout won\'t be processed' +
                            ' because user was active in another system.');
                            _set_tracking(true);
                            ping_timer.start_interval();
                            set_token_expire_time(result.data.deadline, result.data.ttl);
                        } else {
                            $log.info('User is still idle. Logging off.');
                            process_logout();
                        }
                    }, function () {
                        $log.info('Error checking token before logout. Logging off.');
                        process_logout();
                    });
                });
        }

        return {
            start: function () {
                $log.debug('starting idle tracking');
                _set_tracking(true);
                ping_timer.start_interval();
                _init_warning_timer();
            }
        }
    }])
.service('IdleUserModal', ['$modal', 'WMConfig', 'TimeoutCallback', function ($modal, WMConfig, TimeoutCallback) {
    return {
        open: function () {
            var IUController = function ($scope) {
                $scope.countdown = WMConfig.settings.logout_warning_timeout;
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
    'legendDirectives'
])
;