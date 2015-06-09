/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['ApiCalls', 'WMConfig', 'TimeoutCallback', 'Deferred', 'WindowCloseHandler', 'OneWayEvent', function (ApiCalls, WMConfig, TimeoutCallback, Deferred, WindowCloseHandler, OneWayEvent) {
    var __locks = {};
    // Самая жопа в RPC-имплементации Ezekiel Lock - это то, что мы вполне можем не вызывать release() и тем самым
    // благополучно просрать блокировку. Через минуту она, конечно, освободится, но, блин!
    // А ещё хуже, если мы потеряем объект. Тогда блокировка будет очень долго висеть.
    var EzekielLock = function (name) {
        var self = this,
            events = OneWayEvent.new();

        this.tc = new TimeoutCallback();
        this.eventSource = events.eventSource;

        function call_ez(url, token) {
            return ApiCalls.coldstar('GET', url, {token: token}, undefined, {withCredentials: true, silent: true})
        }
        function set_null () {
            self.acquired = null;
            self.locker = null;
            self.token = null;
            self.expiration = null;
            self.success = false;
        }
        // Активные функции
        function acquire_lock() {
            if (self.acquired) {
                self.release().anyway(acquire_lock);
                return
            }
            set_null();
            self.tc.kill();
            self.tc.callback = acquire_lock;
            self.tc.start(10000);
            call_ez(WMConfig.url.coldstar.ezekiel_acquire_lock.format(name))
                .addResolve(lock_acquired)
                .addReject(lock_rejected)
                .addError(lock_lost)
        }
        function prolong_lock() {
            call_ez(WMConfig.url.coldstar.ezekiel_prolong_lock.format(name), self.token)
                .addResolve(lock_prolonged)
                .addReject(lock_lost)
                .addError(lock_lost);
        }
        function release_lock() {
            delete self.release;
            delete __locks[self.token];
            self.tc.kill();
            return call_ez(WMConfig.url.coldstar.ezekiel_release_lock.format(name), self.token)
                .addResolve(lock_released);
        }
        // Реактивные функции
        function lock_acquired (lock) {
            self.acquired = lock.acquire;
            self.token = lock.token;
            self.locker = lock.locker;
            self.expiration = lock.expiration;
            self.success = true;

            self.tc.kill();
            self.tc.callback = prolong_lock;
            self.tc.start(10000);
            self.release = release_lock;
            __locks[lock.token] = self;
            events.send('acquired');
            return lock;
        }
        function lock_rejected (lock) {
            self.acquired = lock.acquire_lock;
            self.locker = lock.locker;
            self.token = null;
            self.expiration = null;
            self.success = false;

            self.tc.kill();
            self.tc.callback = acquire_lock;
            self.tc.start(10000);
            events.send('rejected');
            return lock;
        }
        function lock_lost (lock) {
            set_null();
            self.tc.kill();
            self.tc.callback = acquire_lock;
            self.tc.start(10000);
            events.send('lost');
            return lock;
        }
        function lock_released (lock) {
            set_null();
            events.send('released');
            return lock;
        }
        function lock_prolonged (lock) {
            events.send('prolonged');
            self.tc.start(10000);
            return lock;
        }
        acquire_lock();
    };
    EzekielLock.prototype.release = function () {
        this.tc.kill();
        return Deferred.resolve();
    };
    WindowCloseHandler.addHandler(function () {
        return Deferred.all(_.mapObject(__locks, function (lock) {
            return lock.release();
        }));
    });
    return EzekielLock;
}])
;
