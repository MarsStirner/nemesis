/**
 * Created by mmalkov on 10.06.15.
 */
'use strict';
angular.module('hitsl.ui')
.config([
    '$interpolateProvider', 'datepickerConfig', 'datepickerPopupConfig', 'paginationConfig', '$provide', '$tooltipProvider',
    function ($interpolateProvider, datepickerConfig, datepickerPopupConfig, paginationConfig, $provide, $tooltipProvider) {
        $interpolateProvider.startSymbol('[[');
        $interpolateProvider.endSymbol(']]');
        datepickerConfig.showWeek = false;
        datepickerConfig.startingDay = 1;
        datepickerPopupConfig.currentText = 'Сегодня';
        datepickerPopupConfig.toggleWeeksText = 'Недели';
        datepickerPopupConfig.clearText = 'Убрать';
        datepickerPopupConfig.closeText = 'Готово';
        paginationConfig.firstText = 'Первая';
        paginationConfig.lastText = 'Последняя';
        paginationConfig.previousText = 'Предыдущая';
        paginationConfig.nextText = 'Следующая';
        $tooltipProvider.setTriggers({
            'mouseenter': 'mouseleave',
            'click': 'click',
            'focus': 'blur',
            'never': 'mouseleave',
            'show_popover': 'hide_popover'
        });
        // Workaround for bug #1404
        // https://github.com/angular/angular.js/issues/1404
        // Source: http://plnkr.co/edit/hSMzWC?p=preview
        $provide.decorator('ngModelDirective', ['$delegate', function($delegate) {
            var ngModel = $delegate[0], controller = ngModel.controller;
            ngModel.controller = ['$scope', '$element', '$attrs', '$injector', function(scope, element, attrs, $injector) {
                var $interpolate = $injector.get('$interpolate');
                attrs.$set('name', $interpolate(attrs.name || '')(scope));
                $injector.invoke(controller, this, {
                    '$scope': scope,
                    '$element': element,
                    '$attrs': attrs
                });
            }];
            return $delegate;
        }]);
        $provide.decorator('formDirective', ['$delegate', function($delegate) {
            var form = $delegate[0], controller = form.controller;
            form.controller = ['$scope', '$element', '$attrs', '$injector', function(scope, element, attrs, $injector) {
                var $interpolate = $injector.get('$interpolate');
                attrs.$set('name', $interpolate(attrs.name || attrs.ngForm || '')(scope));
                $injector.invoke(controller, this, {
                    '$scope': scope,
                    '$element': element,
                    '$attrs': attrs
                });
            }];
            return $delegate;
        }]);

        // adminlte theme

        //Collapse icon
        $.AdminLTE.options.boxWidgetOptions.boxWidgetIcons.collapse = 'fa-chevron-down';
        //Open icon
        $.AdminLTE.options.boxWidgetOptions.boxWidgetIcons.open = 'fa-chevron-right';
    }])
;
