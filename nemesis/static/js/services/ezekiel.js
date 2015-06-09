/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['ApiCalls', 'WMConfig', 'TimeoutCallback', 'Deferred', 'WindowCloseHandler', function (ApiCalls, WMConfig, TimeoutCallback, Deferred, WindowCloseHandler) {
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

        this.tc = new TimeoutCallback(acquire, 10000).start();
        this.acquire_defer = Deferred.new();

        function call_ez(url, token) {
            return ApiCalls.coldstar('GET', url, {token: token}, undefined, {withCredentials: true, silent: true})
        }

        function acquire() {
            self.acquire_defer.notify();
            call_ez(WMConfig.url.coldstar.ezekiel_acquire_lock.format(name))
                .addResolve(function (result) {
                    self.acquired = result.acquire;
                    self.token = result.token;
                    self.locker = result.locker;
                    self.expiration = result.expiration;
                    self.success = true;
                    self.tc.kill();
                    self.tc.callback = function prolong() {
                        call_ez(WMConfig.url.coldstar.ezekiel_prolong_lock.format(name), self.token)
                            .addError(set_null);
                    };
                    self.tc.start_interval(0, 30);
                    self.release = function release_real() {
                        delete self.release;
                        delete __locks[self.token];
                        self.tc.kill();
                        return call_ez(WMConfig.url.coldstar.ezekiel_release_lock.format(name), self.token)
                    };
                    self.acquire_defer.resolve();
                    self.acquire_defer = null;
                    __locks[result.token] = self;
                })
                .addReject(function (result) {
                    self.acquired = result.acquire;
                    self.locker = result.locker;
                    self.token = null;
                    self.expiration = null;
                    self.success = false;
                })
                .addError(function (response) {
                    console.log(JSON.stringify(response))
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
        return Deferred.resolve();
    };
    EzekielLock.prototype.promise = function () {
        if (this.acquire_defer) {
            return this.acquire_defer.promise
        } else {
            return Deferred.resolve();
        }
    };
    WindowCloseHandler.addHandler(function () {
        return Deferred.all(__locks, function (lock) {
            return lock.release();
        })
    });
    return EzekielLock;
}])
;
