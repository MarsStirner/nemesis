var LoginCtrl = function ($scope, $http, WMConfig) {
    $scope.login = $("#login").val();
    $scope.role = null;
    $scope.roles = [];
    $scope.get_roles = function () {
        if (!$scope.login){
            return null;
        }
        $http.get(WMConfig.url.nemesis.roles + $scope.login)
        .success(function (data) {
            $scope.roles = data.result;
        })
    };
    if ($scope.login){
        $scope.get_roles();
    }
};

WebMis20.controller('LoginCtrl', ['$scope', '$http', 'WMConfig', LoginCtrl]);