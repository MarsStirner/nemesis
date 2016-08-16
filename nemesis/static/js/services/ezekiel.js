/**
 * Created by mmalkov on 27.04.15.
 */

angular.module('WebMis20')
.factory('WebSocketFactory', ['$rootScope', 'OneWayEvent', function ($rootScope, OneWayEvent) {
    var $apply = _.bind($rootScope.$apply, $rootScope);
    function jped (event) {return JSON.parse(event.data)}
    return function (url) {
        var self = this,
            ws = new WebSocket(url),
            owe = new OneWayEvent();
        this.subscribe = owe.eventSource.subscribe;
        this.close = function () {
            ws.close();
        };
        this.send = function (data) {
            ws.send(JSON.stringify(data))
        };
        ws.onclose = _.compose($apply, _.partial(owe.send, 'closed'));
        ws.onopen = _.compose($apply, function () {
            owe.send('opened');
            self.connected = true;
        });
        ws.onerror = _.compose($apply, _.partial(owe.send, 'error'));
        ws.onmessage = _.compose($apply, _.partial(owe.send, 'message'), jped);
        this.connected = false;
    }
}])
.factory('EzekielLock', ['$rootScope', '$timeout', 'ApiCalls', 'WMConfig', 'OneWayEvent', 'WebSocketFactory', function ($rootScope, $timeout, ApiCalls, WMConfig, OneWayEvent, WebSocketFactory) {
    function jped (event) {return JSON.parse(event.data)}
    var ws = null;

    return function (name) {
        var self = this,
            owe = new OneWayEvent(),
            setup_es = function () {
                var eventSource = new EventSource(WMConfig.url.ezekiel.EventSource.format(name), {withCredentials: true});
                eventSource.addEventListener('acquired', _.compose(_.bind($rootScope.$apply, $rootScope), lock_acquired, jped));
                eventSource.addEventListener('rejected', _.compose(_.bind($rootScope.$apply, $rootScope), lock_rejected, jped));
                eventSource.addEventListener('prolonged', _.compose(_.bind($rootScope.$apply, $rootScope), lock_prolonged, jped));
                eventSource.addEventListener('exception', _.compose(_.bind($rootScope.$apply, $rootScope), lock_lost, jped));
                eventSource.onerror = _.compose(_.bind($rootScope.$apply, $rootScope), lock_lost);

                self.release = function () {
                    eventSource.close();
                    set_null();
                    owe.send('released');
                };
                self.close = function () {
                    eventSource.close();
                };

            },
            setup_ws = function () {
                console.log(WMConfig.url.ezekiel.WebSocket);
                if (!ws) {ws = new WebSocketFactory(WMConfig.url.ezekiel.WebSocket)}
                ws.subscribe('message', function (message) {
                    var event = message.event;
                    if (event == 'ping') {
                        console.log('ping: {0}'.format(message.data));
                        return;
                    }
                    var object_id = safe_traverse(message, ['data', 'object_id']);
                    if (object_id === self.object_id) {
                        if (event == 'acquired') {
                            lock_acquired(message.data)
                        } else if (event == 'released') {
                            lock_rejected(message.data)
                        } else if (event == 'prolonged') {
                            lock_prolonged(message.data)
                        } else if (event == 'rejected') {
                            lock_rejected(message.data)
                        } else {
                            ws.close();
                            ws = null;
                            lock_lost(message.data);
                        }
                    }
                });
                ws.subscribe('closed', lock_lost);
                ws.subscribe('error', lock_lost);
                ws.subscribe('closed', function () {
                    if (ws) {
                        try {
                            ws.close()
                        } catch (e) {}
                        ws = null;

                    }
                    console.log('setting up ws...');
                    $timeout(setup_ws, 5000)
                });
                if (ws.connected) {
                    make_acquire()
                } else {
                    ws.subscribe('opened', make_acquire)
                }
                function make_acquire() {
                    ws.send({
                        command: 'acquire',
                        object_id: name
                    })
                }

            };

        this.subscribe = owe.eventSource.subscribe;
        this.object_id = name;

        setup_ws();

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
            self.acquired = lock.acquire;
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
