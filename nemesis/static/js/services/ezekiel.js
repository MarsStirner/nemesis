/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['ApiCalls', 'WMConfig', 'TimeoutCallback', '$q', function (ApiCalls, WMConfig, TimeoutCallback, $q) {
    var __locks = {};
    // Самая жопа в RPC-имплементации Ezekiel Lock - это то, что мы вполне можем не вызывать release() и тем самым
    // благополучно просрать блокировку. Через минуту она, конечно, освободится, но, блин!
    // А ещё хуже, если мы потеряем объект. Тогда блокировка будет очень долго висеть.
    var EzekielLock = function (name) {
        var self = this;

        function set_null() {
            self.acquired = null;
            self.locker = null;
            self.token = null;
            self.expiration = null;
            self.success = false;
        }

        this.tc = new TimeoutCallback();
        this.tc.callback = acquire;
        this.tc.start_interval(0, 10000);
        this.acquire_defer = $q.defer();

        function acquire() {
            self.acquire_defer.notify();
            ApiCalls.simple(
                'GET',
                WMConfig.url.coldstar.ezekiel_acquire_lock.format(name),
                undefined,
                undefined,
                {
                    withCredentials: true,
                    silent: true
                })
            .then(function (result) {
                self.acquired = result.acquire;
                self.token = result.token;
                self.locker = result.locker;
                self.expiration = result.expiration;
                self.success = true;
                self.tc.kill();
                self.tc.callback = function prolong() {
                    ApiCalls.simple(
                        'GET',
                        WMConfig.url.coldstar.ezekiel_prolong_lock.format(name),
                        { token: self.token },
                        undefined,
                        {
                            withCredentials: true,
                            silent: true
                        }
                    ).catch(function (result) {
                        set_null();
                        return result;
                    })
                };
                self.tc.start_interval(0, (self.expiration - self.acquired) / 2 * 1000);
                self.release = function release_real() {
                    delete self.release;
                    delete __locks[self.token];
                    self.tc.kill();
                    return ApiCalls.simple(
                        'GET',
                        WMConfig.url.coldstar.ezekiel_release_lock.format(name),
                        { token: self.token },
                        undefined,
                        {
                            withCredentials: true,
                            silent: true
                        }
                    )
                };
                self.acquire_defer.resolve();
                self.acquire_defer = null;
                __locks[result.token] = self;
            }, function (result) {
                self.acquired = result.acquire;
                self.locker = result.locker;
                self.token = null;
                self.expiration = null;
                self.success = false;
            })
        }
        set_null();
        acquire();
    };
    EzekielLock.prototype.release = function () {
        this.tc.kill();
        if (this.acquire_defer) {
            this.acquire_defer.reject();
        }
        return $q.resolve();
    };
    EzekielLock.prototype.promise = function () {
        if (this.acquire_defer) {
            return this.acquire_defer.promise
        } else {
            return $q.resolve().promise;
        }
    };
    EzekielLock.release_all = function () {
        return $q.all(_.map(_.values(__locks), function (lock) {
            return lock.release();
        }))
    };
    return EzekielLock;
}])
;
