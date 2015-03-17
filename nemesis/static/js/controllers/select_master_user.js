var SelectMasterUserCtrl = function ($scope, $http, $window) {
    $scope.user = {};
    $scope.get_users = function () {
        $http.get(url_api_doctors_to_assist)
        .success(function (data) {
            $scope.users = data.result;
        });
    };
    $scope.select_user_and_go = function (user) {
        $scope.user.selected_id = user.id;
        $scope.user.selected_prof_id = user.profile.id;
        $scope.submit();
    };
    $scope.user_selected = function (user) {
        if (user === undefined) {
            return $scope.user.selected_id && $scope.user.selected_prof_id;
        }
        return $scope.user.selected_id === user.id && $scope.user.selected_prof_id === user.profile.id;
    };
    $scope.submit = function () {
        if ($scope.user.selected_id && $scope.user.selected_prof_id) {
            $http.post(url_doctor_to_assist, {
                user_id: $scope.user.selected_id,
                profile_id: $scope.user.selected_prof_id
            }, {
                params: {
                    next: aux.getQueryParams(document.location.search).next
                }
            }).success(function (data) {
                $window.open(data.result.redirect_url, '_self');
            });
        }
    };

    $scope.get_users();
};

WebMis20.controller('SelectMasterUserCtrl', ['$scope', '$http', '$window', SelectMasterUserCtrl]);