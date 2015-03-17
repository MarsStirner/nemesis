'use strict';

angular.module('WebMis20.services.models')
.service('WMProcedureOffices', ['$q', '$http', function ($q, $http) {
    var cache;
    this.get = function () {
        if (cache) {
            var deferred = $q.defer();
            deferred.resolve(cache);
            return deferred.promise;
        }
        return $http.get(url_api_procedure_offices_get, {})
        .then(function (response) {
            return cache = response.data.result;
        });
    };
}]);