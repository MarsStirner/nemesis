/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['ApiCalls', 'WMConfig', 'TimeoutCallback', 'Deferred', 'WindowCloseHandler', 'OneWayEvent', function (ApiCalls, WMConfig, TimeoutCallback, Deferred, WindowCloseHandler, OneWayEvent) {
    var __locks = {};
    var EzekielLock = function (name) {
        var self = this,
            owe = new OneWayEvent(),
            eventSource = new EventSource(WMConfig.url.ezekiel.EventSource.format(name), {withCredentials: true});

        function jped (event) {return JSON.parse(event.data)}

        eventSource.addEventListener('acquired', _.compose(lock_acquired, jped));
        eventSource.addEventListener('rejected', _.compose(lock_rejected, jped));
        eventSource.addEventListener('exception', _.compose(lock_lost, jped));

        this.subscribe = owe.eventSource.subscribe;
        this.release = function () {
            eventSource.close();
            set_null();
            owe.send('released');
        };

        function set_null () {
            self.acquired = null;
            self.locker = null;
            self.token = null;
            self.expiration = null;
            self.success = false;
        }
        // Реактивные функции
        function lock_acquired (lock) {
            self.acquired = lock.acquire;
            self.token = lock.token;
            self.locker = lock.locker;
            self.expiration = lock.expiration;
            self.success = true;

            __locks[lock.token] = self;
            owe.send('acquired');
            return lock;
        }
        function lock_rejected (lock) {
            self.acquired = lock.acquire_lock;
            self.locker = lock.locker;
            self.token = null;
            self.expiration = null;
            self.success = false;

            owe.send('rejected');
            return lock;
        }
        function lock_lost (lock) {
            set_null();
            owe.send('lost');
            return lock;
        }
    };
    EzekielLock.prototype.release = function () {
        return Deferred.resolve();
    };
    return EzekielLock;
}])
;
