/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('EzekielLock', ['$rootScope', 'ApiCalls', 'WMConfig', 'OneWayEvent', function ($rootScope, ApiCalls, WMConfig, OneWayEvent) {
    function jped (event) {return JSON.parse(event.data)}

    return function (name) {
        var self = this,
            owe = new OneWayEvent(),
            eventSource = new EventSource(WMConfig.url.ezekiel.EventSource.format(name), {withCredentials: true});

        eventSource.addEventListener('acquired', _.compose(_.bind($rootScope.$apply, $rootScope), lock_acquired, jped));
        eventSource.addEventListener('rejected', _.compose(_.bind($rootScope.$apply, $rootScope), lock_rejected, jped));
        eventSource.addEventListener('prolonged', _.compose(_.bind($rootScope.$apply, $rootScope), lock_prolonged, jped));
        eventSource.addEventListener('exception', _.compose(_.bind($rootScope.$apply, $rootScope), lock_lost, jped));
        eventSource.onerror = _.compose(_.bind($rootScope.$apply, $rootScope), lock_lost);

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

            owe.send('acquired');
            return lock;
        }
        function lock_prolonged (lock) {
            self.acquired = lock.acquire;
            self.token = lock.token;
            self.locker = lock.locker;
            self.expiration = lock.expiration;
            self.success = true;

            owe.send('prolonged');
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
}])
;
