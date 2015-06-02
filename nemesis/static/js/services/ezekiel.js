/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['ApiCalls', 'WMConfig', 'TimeoutCallback', '$q', function (ApiCalls, WMConfig, TimeoutCallback, $q) {
    // Самая жопа в RPC-имплементации Ezekiel Lock - это то, что мы вполне можем не вызывать release() и тем самым
    // благополучно просрать блокировку. Через минуту она, конечно, освободится, но, блин!
    // А ещё хуже, если мы потеряем объект. Тогда блокировка будет очень долго висеть.
    var EzekielLock = function (name) {
        var self = this;
        this.tc = new TimeoutCallback();
        this.acquire_defer = $q.defer();

        function acquire() {
            self.acquire_defer.notify();
            delete self.release;
            ApiCalls.simple('GET', WMConfig.url.coldstar.ezekiel_acquire_lock.format(name))
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
                        {token: self.token}
                    )
                };
                self.tc.start_interval((self.expiration - self.acquired) / 2);
                self.release = function release_real() {
                    self.tc.kill();
                    ApiCalls.simple(
                        'GET',
                        WMConfig.url.coldstar.ezekiel_release_lock.format(name),
                        {token: self.token}
                    )
                };
                self.acquire_defer.resolve();
                self.acquire_defer = null;
            }, function (result) {
                self.acquired = result.acquire;
                self.locker = result.locker;
                self.token = null;
                self.expiration = null;
                self.success = false;
                self.tc.kill();
                self.tc.callback = _.bind(self, acquire);
                self.tc.start_interval((self.expiration - self.acquired) / 2);
            })
        }
        acquire();
    };
    EzekielLock.prototype.release = function () {
        this.tc.kill();
        if (this.acquire_defer) {
            this.acquire_defer.reject();
        }
    };
    EzekielLock.prototype.promise = function () {
        if (this.acquire_defer) {
            return this.acquire_defer.promise
        } else {
            return $q.reject().promise;
        }
    };
    return EzekielLock;
}])
;
