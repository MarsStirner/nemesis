/**
 * Created by mmalkov on 03.07.15.
 */


angular.module('hitsl.core')
    .service('Simargl', function ($rootScope, WMConfig, $q, ApiCalls) {
        var ready = $q.defer();
        var es = new EventSource(WMConfig.url.simargl.EventSource, {withCredentials: true});
        var map = [];
        es.onmessage = function (event) {
            $rootScope.$apply(function () {
                var message = JSON.parse(event.data);
                console.log(message);
                _.each(map, function (item) {
                    var topic = item[0], cb = item[1];
                    if (topic == message.topic) {
                        cb(message)
                    }
                })
            })
        };
        es.onopen = function () {
            ready.resolve();
        };
        this.subscribe = function (topic, callback) {
            map.push([topic, callback])
        };
        this.when_ready = function (callback) {
            ready.promise.then(callback);
        };
        this.send_msg = function (msg) {
            return ApiCalls.coldstar('POST', WMConfig.url.simargl.RPC, undefined, msg, {withCredentials: true});
        }
    })
    .service('UserMail', function (Simargl, ApiCalls, WMConfig, OneWayEvent, CurrentUser, NotificationService) {
        var event_source = new OneWayEvent(),
            get_mail_url = WMConfig.url.api_user_mail;
        if (!get_mail_url) {
            throw 'ВСЁ ПРОПАЛО!'
        }
        function notify_unread (result) {
            event_source.send('unread', {
                unread: result.unread,
                count: result.index_count
            });
            return result;
        }
        function notify_new (result) {
            event_source.send('new', _.first(result.messages));
            return result
        }
        Simargl.when_ready(function () {
            ApiCalls.wrapper('GET', get_mail_url).then(notify_unread);
            event_source.send('ready');
        });
        Simargl.subscribe('mail', function (msg) {
            ApiCalls.wrapper('GET', get_mail_url, {ids: msg.data.id}).then(notify_unread).then(notify_new)
        });
        this.subscribe = event_source.eventSource.subscribe;
        this.set_mark = function (mark_type, ids, value) {
            var method = "PUT";
            if (! (ids instanceof Array)) ids = [ids];
            if (!value) {method = "DELETE"}
            return ApiCalls.wrapper(method, WMConfig.url.api_user_mail_mark.format(ids.join(':'), mark_type)).then(notify_unread);
        };
        this.mail_move = function (folder, ids) {
            if (! (ids instanceof Array)) ids = [ids];
            return ApiCalls.wrapper('MOVE', WMConfig.url.api_user_mail_move.format(ids.join(':'), folder)).then(notify_unread);
        };
        this.get_mail = function (folder, skip, limit) {
            return ApiCalls.wrapper('GET', get_mail_url, {
                folder: folder,
                skip: skip,
                limit: limit
            }).then(notify_unread)
        };
        this.send_mail = function (recipient, subject, text, parent_id) {
            ApiCalls.coldstar('POST', WMConfig.url.simargl.RPC, undefined, {
                topic: 'mail:new',
                recipient: recipient,
                sender: CurrentUser.id,
                data: { subject: subject, text: text, parent_id: parent_id },
                ctrl: true
            }, {allowCredentials: true}).then(function () {
                NotificationService.notify(undefined, 'Письмо успешно отправлено', 'success', 5000);
                $scope.mode = 0;
            }, function () {
                NotificationService.notify(undefined, 'Не удалось отправить письмо', 'danger', 5000);
            })
        }
    })
;
