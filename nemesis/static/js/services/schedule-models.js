'use strict';

angular.module('WebMis20.services.models')
.service('WMProcedureOffices', ['$q', '$http', 'WMConfig', function ($q, $http, WMConfig) {
    var cache;
    this.get = function () {
        if (cache) {
            var deferred = $q.defer();
            deferred.resolve(cache);
            return deferred.promise;
        }
        return $http.get(WMConfig.url.schedule.procedure_offices, {})
        .then(function (response) {
            return cache = response.data.result;
        });
    };
}]);