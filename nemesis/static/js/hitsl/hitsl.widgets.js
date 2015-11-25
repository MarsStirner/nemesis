'use strict';

angular.module('WebMis20')
.directive('wmDate', ['$timeout', '$compile', function ($timeout, $compile) {
    return {
        restrict: 'E',
        require: '^ngModel',
        link: function (original_scope, element, attrs, ngModelCtrl) {
            var scope = original_scope.$new(false);
            scope.popup = { opened: false };
            scope.open_datepicker_popup = function (prev_state) {
                $timeout(function () {
                    scope.popup.opened = !prev_state;
                    if (!ngModelCtrl.$modelValue) {
                        ngModelCtrl.$setViewValue(new Date());
                    }
                });
            };
            var _id = attrs.id,
                name = attrs.name,
                ngDisabled = attrs.ngDisabled,
                ngRequired = attrs.ngRequired,
                ngModel = attrs.ngModel,
                style = attrs.style,
                maxDate = attrs.maxDate,
                autofocus = attrs.autofocus;
            var wmdate = $('<div class="input-group"></div>'),
                date_input = $('\
                    <input type="text" class="form-control" autocomplete="off" datepicker_popup="dd.MM.yyyy"\
                        is-open="popup.opened" manual-date ui-mask="99.99.9999" date-mask />'
                ),
                button = $('\
                    <button type="button" class="btn btn-default" ng-click="open_datepicker_popup(popup.opened)">\
                        <i class="glyphicon glyphicon-calendar"></i>\
                    </button>'
                ),
                button_wrap = $('<span class="input-group-btn"></span>');
            if (_id) date_input.attr('id', _id);
            if (name) date_input.attr('name', name);
            date_input.attr('ng-model', ngModel);
            if (ngDisabled) {
                date_input.attr('ng-disabled', ngDisabled);
                button.attr('ng-disabled', ngDisabled);
            }
            if (autofocus){
                date_input.attr('auto-focus', '');
            }
            if (style) {
                wmdate.attr('style', style);
                element.removeAttr('style');
            }
            if (ngRequired) date_input.attr('ng-required', ngRequired);
            if (maxDate) date_input.attr('max', maxDate);

            button_wrap.append(button);
            wmdate.append(date_input, button_wrap);
            $(element).append(wmdate);
            $compile(wmdate)(scope);
        }
    };
}])
.directive('manualDate', [function() {
    return {
        restrict: 'A',
        require: '^ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(_) {
                var viewValue = ctrl.$viewValue,
                    maxDate = scope.$eval(attrs.max);
                if (!viewValue || viewValue instanceof Date) {
                    return viewValue;
                }
                var d = moment(viewValue.replace('_', ''), "DD.MM.YYYY", true);
                if (moment(d).isValid() && (maxDate ? moment(maxDate).isAfter(d) : true)) {
                    ctrl.$setValidity('date', true);
                    ctrl.$setViewValue(d.toDate());
                    return d;
                } else {
                    ctrl.$setValidity('date', false);
                    return undefined;
                }
            });
        }
    };
}])
.directive('wmTime', ['$document', function ($document) {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            id: '=',
            name: '=',
            ngModel: '=',
            ngRequired: '=',
            ngDisabled: '='
        },
        template:
'<div class="input-group">\
<input type="text" id="[[id]]" name="[[name]]" class="form-control"\
       ng-model="ngModel" autocomplete="off"\
       ng-required="ngRequired" show-time ng-disabled="ngDisabled" />\
<span class="input-group-btn">\
    <button class="btn btn-default" type="button" ng-click="open_timepicker_popup()" ng-disabled="ngDisabled">\
        <i class="glyphicon glyphicon-time"></i>\
    </button>\
    <div class="timepicker_popup" ng-show="isPopupVisible">\
        <div style="display:inline-block;">\
            <timepicker ng-model="ngModel" show-meridian="false"></timepicker>\
        </div>\
    </div>\
</span>\
</div>',
        link: function(scope, element, attr) {
            scope.isPopupVisible = false;
            scope.open_timepicker_popup = function () {
                scope.isPopupVisible = !scope.isPopupVisible;
            };

            $document.bind('click', function(event) {
                var isClickedElementChildOfPopup = element
                  .find(event.target)
                  .length > 0;
                if (isClickedElementChildOfPopup)
                  return;

                scope.isPopupVisible = false;
                scope.$apply();
            });
        }
    };
}])
.directive('showTime', function() {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, element, attrs, ngModel) {
            ngModel.$parsers.unshift(function (value) {
                var oldValue = ngModel.$modelValue;
                if (value && !(value instanceof Date)) {
                    if (/^([01]\d|2[0-3]):([0-5]\d)$/.test(value)) {
                        var parts = value.split(':');
                        oldValue = oldValue || new Date();
                        oldValue.setHours(parts[0]);
                        oldValue.setMinutes(parts[1]);
                    }
                    if (moment(oldValue).isValid()) {
                        ngModel.$setValidity('date', true);
                        ngModel.$setViewValue(oldValue);
                        return oldValue;
                    } else {
                        ngModel.$setValidity('date', false);
                        return undefined;
                    }
                } else {
                    return oldValue;
                }
            });

            function format_time(date) {
                function lead_zero(val) {
                    return String(val).length === 1 ? ('0' + val) : String(val);
                }
                return lead_zero(date.getHours()) + ":" + lead_zero(date.getMinutes());
            }

            if (ngModel) {
                ngModel.$formatters.push(function (value) {
                    if (!(value instanceof Date) && value) {
                        value = new Date(value);
                    }
                    if (value && moment(value).isValid()) {
                        return format_time(value);
                    } else {
                        return undefined;
                    }
                });
            }
        }
    };
})
.directive('wmImageEditor', ['$log', function ($log) {
    return {
        restrict: 'E',
        template: function () {
            var toolbar = '\
<div class="btn-toolbar" role="toolbar" aria-label="...">\
    <div class="btn-group pull-right" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="resetImage()" ng-disabled="!btnResetEnabled()" title="Вернуться к исходному изображению">\
            <span class="fa fa-refresh"></span>\
        </button>\
    </div>\
    <div class="btn-group" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="rotate(\'left\')" ng-disabled="!btnRotateEnabled()" title="Повернуть против часовой стрелки">\
            <span class="fa fa-rotate-left"></span>\
        </button>\
        <button type="button" class="btn btn-default" ng-click="rotate(\'right\')" ng-disabled="!btnRotateEnabled()" title="Повернуть по часовой стрелке">\
            <span class="fa fa-rotate-right"></span>\
        </button>\
    </div>\
    <div class="btn-group" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="zoom(1)" ng-disabled="!btnZoomInEnabled()" title="Увеличить">\
            <span class="fa fa-plus"></span>\
        </button>\
        <!--<label class="label label-default">[[scalePct]] %</label>-->\
        <button type="button" class="btn btn-default" ng-click="zoom(-1)" ng-disabled="!btnZoomOutEnabled()" title="Уменьшить">\
            <span class="fa fa-minus"></span>\
        </button>\
        <button type="button" class="btn btn-default" ng-click="zoomToFit()" ng-disabled="!btnZoomToFitEnabled()" title="Отобразить по размеру области">\
            <span class="fa fa-arrows-alt"></span>\
        </button>\
    </div>\
    <div class="btn-group" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="cropStart()" ng-disabled="!btnCropStartEnabled()" title="Обрезать изображение">\
            <span class="fa fa-crop"></span>\
        </button>\
        <button type="button" class="btn btn-success" ng-click="cropApply()" ng-show="!btnCropStartEnabled()" ng-disabled="!btnCropApplyEnabled()" title="Подтвердить">\
            <span class="fa fa-check"></span>\
        </button>\
        <button type="button" class="btn btn-danger" ng-click="cropCancel()" ng-show="!btnCropStartEnabled()" ng-disabled="!btnCropCancelEnabled()" title="Отменить">\
            <span class="fa fa-times"></span>\
        </button>\
    </div>\
</div>';
            var editor = '<canvas></canvas>';
            return '{0}<div id="imageContainer" class="image_editor">{1}</div>'.format(toolbar, editor);
        },
        scope: {
            modelImage: '=',
            readOnly: '=',
            mimeType: '@?'
        },
        link: function (scope, element, attrs) {
            var viewCanvas = element[0].childNodes[1].childNodes[0],
                viewCtx = viewCanvas.getContext('2d'),
                _originalImage = new Image(), // for backup
                _helpImage = new Image(), // always in non rotated state
                _rotateAngle = 0,
                _scaleFactor = 1.0,
                _jcrop_api,
                _helpCanvasMap = {}; // offscreen canvases
            if (!scope.mimeType) {
                scope.mimeType = 'image/png';
            }

            // toolbar
            var scales = [5, 10, 15, 30, 50, 75, 90, 100, 125, 150, 200, 300, 400, 500];
            scope.scalePct = 100;
            scope.resetImage = function () {
                _rotateAngle = 0;
                _scaleFactor = 1.0;
                _resizeCanvas();
                scope.modelImage.src = _originalImage.src;
                _helpImage.src = scope.modelImage.src;
                renderViewImage();
            };
            scope.btnResetEnabled = function () {
                return !scope.readOnly && !cropInProgress();
            };
            scope.rotate = function (where) {
                var angle = where === 'left' ? -90 : 90;
                _rotateAngle += angle;
                if (_rotateAngle === 360) {
                    _rotateAngle = 0;
                } else if (_rotateAngle > 360) {
                    _rotateAngle -= 360;
                } else if (_rotateAngle < 0)  {
                    _rotateAngle = 360 + _rotateAngle;
                }
                rotateImage();
            };
            scope.btnRotateEnabled = function () {
                return !scope.readOnly && !cropInProgress();
            };
            scope.zoom = function (how) {
                function getClosestIndex(val) {
                    var list = scales,
                        max_idx = list.length - 1,
                        low_idx = 0,
                        high_idx = max_idx,
                        mid_idx, // 1st candidate
                        sibling_idx, // 2nd candidate
                        test_elem;
                    while (low_idx <= high_idx) {
                        mid_idx = Math.floor((high_idx + low_idx) / 2);
                        test_elem = list[mid_idx];
                        if (test_elem < val) {
                            low_idx = mid_idx + 1;
                            sibling_idx = low_idx <= max_idx ? low_idx : mid_idx - 1;
                        } else if (test_elem > val) {
                            high_idx = mid_idx - 1;
                            sibling_idx = high_idx >= 0 ? high_idx : mid_idx + 1;
                        } else {
                            return mid_idx;
                        }
                    }
                    return Math.abs(list[mid_idx] - val) > Math.abs(list[sibling_idx] - val) ? sibling_idx : mid_idx;
                }
                var index = getClosestIndex(scope.scalePct);
                scope.scalePct = scales[index + how];
                _scaleFactor = scope.scalePct / 100;
                scaleImage();
            };
            scope.btnZoomInEnabled = function () {
                return !cropInProgress() && scope.scalePct < scales[scales.length - 1];
            };
            scope.btnZoomOutEnabled = function () {
                return !cropInProgress() && scales.indexOf(scope.scalePct) !== 0;
            };
            scope.zoomToFit = function () {
                setScaleToFit();
                scaleImage();
            };
            scope.btnZoomToFitEnabled = function () {
                return !cropInProgress();
            };
            scope.cropStart = function () {
                var _hc = _getHelpCanvas('crop', true),
                    hCanvas = _hc.canvas,
                    hCtx = _hc.ctx,
                    jqViewCanvas = $(viewCanvas);

                _resizeCanvas(hCanvas, viewCanvas.width, viewCanvas.height);
                hCtx.save();
                hCtx.scale(_scaleFactor, _scaleFactor);
                drawImage(hCtx, scope.modelImage);
                hCtx.restore();
                jqViewCanvas.before(hCanvas);
                jqViewCanvas.hide();
                $(hCanvas).Jcrop({
                }, function () {
                    _jcrop_api = this;
                });
            };
            scope.btnCropStartEnabled = function () {
                return !scope.readOnly && !cropInProgress();
            };
            scope.cropCancel = function () {
                _clearJcrop();
                $(viewCanvas).show();
            };
            scope.btnCropCancelEnabled = function () {
                return !scope.readOnly && cropInProgress();
            };
            function cropInProgress() {
                return _jcrop_api !== undefined;
            }
            function _clearJcrop() {
                _jcrop_api.release();
                _jcrop_api.destroy();
                _jcrop_api = undefined;
            }
            scope.cropApply = function () {
                var _hc = _getHelpCanvas('helpModelImage', true),
                    hCanvas = _hc.canvas,
                    hCtx = _hc.ctx,
                    cropCoords = _jcrop_api.tellSelect(),
                    x = cropCoords.x / _scaleFactor,
                    y = cropCoords.y / _scaleFactor,
                    w = cropCoords.w / _scaleFactor,
                    h = cropCoords.h / _scaleFactor;

                _resizeCanvas(hCanvas, w, h);
                hCtx.drawImage(scope.modelImage, x, y, w, h, 0, 0, w, h);

                _helpImage.src = hCanvas.toDataURL(scope.mimeType, 0.65);
                _rotateAngle = 0;
                scope.modelImage.src = _helpImage.src;

                _clearJcrop();
                $(viewCanvas).show();
                renderViewImage();
            };
            scope.btnCropApplyEnabled = function () {
                if (scope.readOnly) return false;
                var selected = cropInProgress() ? _jcrop_api.tellSelect() : {};
                return selected.w && selected.h;
            };
            // toolbar

            function _initNewImage(image) {
                _originalImage.src = image.src;
                _helpImage.src = image.src;
                _rotateAngle = 0;
                setScaleToFit();
                _resizeCanvas();
            }
            function _resizeCanvas(canvas, width, height) {
                if (canvas === undefined) canvas = viewCanvas;
                if (width === undefined) width = scope.modelImage.width;
                if (height === undefined) height = scope.modelImage.height;
                canvas.width = width;
                canvas.height = height;
            }
            function _getHelpCanvas(name, dontStore) {
                if (_helpCanvasMap.hasOwnProperty(name)) {
                    return _helpCanvasMap[name];
                } else {
                    var canvas = document.createElement('canvas'),
                        ctx = canvas.getContext('2d'),
                        hcObj = {
                            canvas: canvas,
                            ctx: ctx
                        };
                    if (!dontStore) _helpCanvasMap[name] = hcObj;
                    return hcObj;
                }
            }
            function _getNewCanvasSize(width, height, angle) {
                var rads = Math.PI / 180 * angle,
                    c = Math.abs(Math.cos(rads)),
                    s = Math.abs(Math.sin(rads));
                var newWidth = height * s + width * c,
                    newHeight = height * c + width * s;
                return {
                    w: newWidth,
                    h: newHeight
                };
            }

            function drawImage(context, image, x, y) {
                if (context === undefined) context = viewCtx;
                if (image === undefined) image = scope.modelImage;
                if (x === undefined) x = 0;
                if (y === undefined) y = 0;
                context.drawImage(image, x, y);
            }
            function renderViewImage() {
                var image = scope.modelImage,
                    newWidth = image.width * _scaleFactor,
                    newHeight = image.height * _scaleFactor;

                _resizeCanvas(viewCanvas, newWidth, newHeight);
                viewCtx.save();
                viewCtx.scale(_scaleFactor, _scaleFactor);
                drawImage(viewCtx, image);
                viewCtx.restore();
            }

            function rotateImage() {
                var _hc = _getHelpCanvas('helpModelImage'),
                    hCanvas = _hc.canvas,
                    hCtx = _hc.ctx,
                    image = _helpImage,
                    newSizes = _getNewCanvasSize(image.width, image.height, _rotateAngle),
                    newWidth = newSizes.w,
                    newHeight = newSizes.h;

                _resizeCanvas(hCanvas, newWidth, newHeight);
                hCtx.save();
                hCtx.translate(newWidth / 2, newHeight / 2);
                hCtx.rotate(Math.PI / 180 * _rotateAngle);
                drawImage(hCtx, image, -image.width / 2, -image.height / 2);
                hCtx.restore();

                scope.modelImage.src = hCanvas.toDataURL(scope.mimeType, 0.65);

                renderViewImage();
            }
            function scaleImage() {
                var _hc = _getHelpCanvas('helpModelImage'),
                    hCanvas = _hc.canvas,
                    hCtx = _hc.ctx;
                _resizeCanvas(hCanvas, _helpImage.width, _helpImage.height);
                drawImage(hCtx, _helpImage);

                renderViewImage();
            }
            function setScaleToFit() {
                var i_w = scope.modelImage.width,
                    i_h = scope.modelImage.height,
                    container = $(viewCanvas).parent(),
                    v_w = container.width(),
                    v_h = container.height();
                var fit_w = Math.min(i_w, v_w),
                    fit_h = Math.min(i_h, v_h);
                if (i_w <= fit_w && i_h <= fit_h) {
                    _scaleFactor = 1.0;
                } else if (fit_w < fit_h) {
                    _scaleFactor = fit_w / i_w;
                } else {
                    _scaleFactor = fit_h / i_h;
                }
                scope.scalePct = Math.round(_scaleFactor * 100);
            }

            function _clearOldData() {
                angular.forEach(_helpCanvasMap, function (cObj) {
                    cObj.canvas.width = 1;
                    cObj.canvas.height = 1;
                });
                viewCanvas.width = 1;
                viewCanvas.height = 1;
                _originalImage.src = "";
                _helpImage.src = "";
            }

            scope.$watch('modelImage', function (n, o) {
                _clearOldData();
                if (n && n.src) {
                    _initNewImage(n);
                    renderViewImage();
                }
            });
        }
    }
}])
.directive('wmSubscriptionBtn', ['ApiCalls', 'WMConfig', 'NotificationService', function (ApiCalls, WMConfig, NotificationService) {
    return {
        restrict: 'E',
        scope: {
            oid: '@oid'
        },
        replace: true,
        template: '<button class="btn btn-default" ng-click="toggle()"><i class="fa text-yellow" ng-class="{\'fa-star\': subscribed, \'fa-star-o\': !subscribed}"></i></button>',
        link: function (scope) {
            scope.subscribed = false;
            function process (method) {
                return ApiCalls.wrapper(method, WMConfig.url.api_subscription.format(scope.oid))
                    .then(function (result) {
                        scope.subscribed = result;
                        return result
                    });
            }
            scope.$watch('oid', function (n, o) {
                if (!angular.equals(n, o)) {
                    process('GET')
                }
            });
            scope.toggle = function () {
                process((scope.subscribed)?'DELETE':'PUT').then(function (result) {
                    NotificationService.notify(
                        'subs',
                        (result)?'Подписка оформлена':'Подписка отменена',
                        'info',
                        5000
                    )
                });
            };
        }
    }
}])
.directive('wmColorPicker', [function () {
    return {
        restrict: 'E',
        require: 'ngModel',
        scope: {
            ngModel: '='
        },
        template:
'<input type="color" ng-model=ngModel>\
<span class="lmargin20 fa fa-times text-danger" title="Очистить" ng-if="colorSelected()" ng-click="clearColor()"></span>\
',
        link: function (scope, element, attrs, ngModelCtrl) {
            scope.colorSelected = function () {
                return Boolean(ngModelCtrl.$modelValue);
            };
            scope.clearColor = function () {
                ngModelCtrl.$setViewValue(null);
            }
        }
    }
}])
.directive('wmMkbMultiple', [function() {
    return {
        restrict: 'E',
        require: 'ngModel',
        replace: true,
        scope: {
        },
        template: '\
<div>\
<ui-select multiple theme="select2" ref-book="MKB" close-on-select="false">\
    <ui-select-match placeholder="[[placeholder]]"><span title="[[$item.name]]" ng-bind="$item.code"></span></ui-select-match>\
    <ui-select-choices repeat="mkb in $refBook.objects | filter: $select.search | limitTo: 100 | filter:filterMkbChoices track by mkb.id">\
        <div ng-bind-html="mkb.code | highlight: $select.search"></div>\
        <small style="font-style: italic" ng-bind-html="mkb.name"></small>\
    </ui-select-choices>\
</ui-select>\
</div>',
        link: function (scope, elem, attrs, ngModelCtrl) {
            scope.placeholder = attrs.placeholder;

            var used_codes = [];
            scope.$watch(function () { return ngModelCtrl.$modelValue; }, function (n, o) {
                used_codes = n.map(function (mkb) { return mkb.code });
            });
            scope.filterMkbChoices = function (mkb) {
                return !used_codes.has(mkb.code);
            };
        }
    }
}])
.directive('extSelectOrg', [function () {
    return {
        restrict: 'A',
        require: ['uiSelect', 'ngModel'],
        compile: function compile (tElement, tAttrs, transclude) {
            // Add the inner content to the element
            tElement.append(
'<ui-select-match placeholder="[[placeholder]]" ref-book="Organisation">[[ $select.selected.short_name ]]</ui-select-match>\
<ui-select-choices repeat="org in $refBook.objects | filter: {short_name: $select.search} | limitTo:50">\
    <div ng-bind-html="org.short_name | highlight: $select.search"></div>\
</ui-select-choices>');

            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    scope.placeholder = iAttrs.placeholder || 'организация';
                }
            }
        }
    }
}])
.directive('extSelectClientSearch', ['$http', function ($http) {
    return {
        restrict: 'A',
        require: ['uiSelect', 'ngModel'],
        compile: function compile (tElement, tAttrs, transclude) {
            // Add the inner content to the element
            tElement.append(
'<ui-select-match placeholder="[[placeholder]]">[[ $select.selected.full_name ]]</ui-select-match>\
<ui-select-choices repeat="client in clients" refresh="get_clients($select.search)">\
    <div>\
        <small>[[ client.id ]]</small>\
        <span ng-bind-html="client.full_name | highlight: $select.search"></span>\
    </div>\
    <div>\
        <small>[[ client.birth_date | asDate ]], [[ client.sex.name ]]</small>\
    </div>\
</ui-select-choices> ');

            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    scope.placeholder = iAttrs.placeholder || 'ФИО пациента';
                    scope.get_clients = function (query) {
                        if (!query) return;
                        return $http.get(url_client_search, {
                            params: {
                                q: query,
                                short: true,
                                limit: 20
                            }
                        })
                        .then(function (res) {
                            return scope.clients = res.data.result;
                        });
                    };
                }
            }
        }
    }
}])
.directive('extSelectContragentSearch', ['AccountingService', function (AccountingService) {
    return {
        restrict: 'A',
        require: ['uiSelect', 'ngModel'],
        compile: function compile (tElement, tAttrs, transclude) {
            // Add the inner content to the element
            tElement.append(
'<ui-select-match placeholder="[[placeholder]]">[[ $select.selected.short_descr ]]</ui-select-match>\
<ui-select-choices repeat="ca in ca_list" refresh="get_contragents($select.search)">\
    <div><span ng-bind-html="ca.full_descr | highlight: $select.search"></span></div>\
</ui-select-choices> ');

            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    iAttrs.$observe('caTypeCode', function (newVal, oldVal) {
                        scope.ca_type_code = newVal;
                        scope.placeholder = scope.ca_type_code === 'legal' ?
                            'Поиск контрагента, юр. лицо' :
                            'Поиск контрагента, физ. лицо';
                    });
                    scope.get_contragents = function (query) {
                        if (!query) return;
                        return AccountingService.search_contragent(query, scope.ca_type_code)
                            .then(function (ca_list) {
                                scope.ca_list = ca_list;
                            });
                    };
                }
            }
        }
    }
}])
.directive('extSelectContractEvent', [function () {
    return {
        restrict: 'A',
        require: ['uiSelect', 'ngModel'],
        compile: function compile (tElement, tAttrs, transclude) {
            // Add the inner content to the element
            tElement.append(
'<ui-select-match placeholder="[[placeholder]]">[[$select.selected.description.short]]</ui-select-match>\
<ui-select-choices repeat="contract in contract_list | filter: $select.search">\
    <div>\
        <span>№[[ contract.number ]]</span> <span>от [[ contract.date | asDate ]]</span>\
    </div>\
    <div>\
        <small>[[ contract.resolution ]]</small>\
    </div>\
</ui-select-choices>');

            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    scope.contract_list = [];
                    scope.$watch(tAttrs.contractList, function (newVal, oldVal) {
                        scope.contract_list = newVal;
                    });
                    scope.placeholder = 'Выберите подходящий договор или создайте новый';
                }
            }
        }
    }
}])
.directive('extSelectPriceListSearch', ['AccountingService', function (AccountingService) {
    return {
        restrict: 'A',
        require: ['uiSelect', 'ngModel'],
        compile: function compile (tElement, tAttrs, transclude) {
            // Add the inner content to the element
            tElement.append(
'<ui-select-match placeholder="[[placeholder]]">[[ $select.selected.description.short ]]</ui-select-match>\
<ui-select-choices repeat="pl in pl_list">\
    <div>\
        <span>[[ pl.id ]]</span> <span>[[ pl.code ]] [[ pl.name ]] ([[ pl.finance.name ]])</span>\
    </div>\
    <div>\
        <span>с [[ pl.beg_date | asDate ]] по [[ pl.end_date | asDate ]]</span>\
    </div>\
</ui-select-choices> ');

            return {
                pre: function preLink(scope, iElement, iAttrs, controller) {},
                post: function postLink(scope, iElement, iAttrs, controller) {
                    scope.placeholder = iAttrs.placeholder || 'Выбери прайс-лист';
                    var refresh_pricelists = function (finance_id) {
                        return AccountingService.get_pricelists(finance_id)
                            .then(function (pl_list) {
                                scope.pl_list = pl_list;
                            });
                    };
                    scope.$watch(tAttrs.finance, function (newVal, oldVal) {
                        refresh_pricelists(newVal.id);
                    });
                }
            }
        }
    }
}])
;