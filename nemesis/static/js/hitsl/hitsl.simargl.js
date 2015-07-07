/**
 * Created by mmalkov on 03.07.15.
 */


angular.module('hitsl.core')
    .service('Simargl', function ($rootScope, WMConfig, $q) {
        var ready = $q.defer();
        var es = new EventSource('http://127.0.0.1:5002/simargl-es', {withCredentials: true});
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
        }
    })
;
