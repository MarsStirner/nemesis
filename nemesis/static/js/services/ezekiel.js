/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['ApiCalls', 'WMConfig', 'TimeoutCallback', function (ApiCalls, WMConfig, TimeoutCallback) {
    var EzekielLock = function (name) {
        this.name = name;
        this.tc = new TimeoutCallback()
    };
    EzekielLock.acquire = function () {
        var self = this;
        return ApiCalls.wrapper('GET', WMConfig.coldstar.ezekiel_acquire_lock.format(self.name))
        .then(function (result) {
            if (result.success) {
                self.acquired = result.acquire;
                self.token = result.token;
                self.locker = result.locker;
                self.expiration = result.expiration;
                self.success = true;
                self.tc.kill();
                self.tc.callback = function () { self.prolong() };
                self.tc.start_interval((self.expiration - self.acquired) / 2)
            } else {
                self.acquired = result.acquire;
                self.locker = result.locker;
                self.token = null;
                self.expiration = null;
                self.success = false;
                self.tc.kill();
                self.tc.callback = function () { self.acquire() };
                self.tc.start_interval((self.expiration - self.acquired) / 2)
            }
            return result.success;
        })
    };
    EzekielLock.release = function () {
        var self = this;
        self.tc.kill();
        if (self.token) {
            return ApiCalls.wrapper('GET', WMConfig.coldstar.ezekiel_release_lock.format(self.name), {token: token})
        } else {
            throw 'Lock is not acquired'
        }
    };
    EzekielLock.prolong = function () {
        var self = this;
        if (self.token) {
            return ApiCalls.wrapper('GET', WMConfig.coldstar.ezekiel_prolong_lock.format(self.name), {token: token})
        } else {
            self.tc.kill();
            throw 'Lock is not acquired'
        }
    }
}])
;
