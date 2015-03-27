'use strict';

angular.module('WebMis20')
.directive('wmImageEditor', ['$log', function ($log) {
    return {
        restrict: 'E',
        template: function () {
            var toolbar = '\
<div class="btn-toolbar marginal bg-muted" role="toolbar" aria-label="...">\
    <div class="btn-group btn-group-lg pull-right" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="resetImage()" ng-disabled="!btnResetEnabled()" title="Вернуться к исходному изображению">\
            <span class="fa fa-refresh"></span>\
        </button>\
    </div>\
    <div class="btn-group btn-group-lg rmargin10" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="rotate(\'left\')" ng-disabled="!btnRotateEnabled()" title="Повернуть против часовой стрелки">\
            <span class="fa fa-rotate-left"></span>\
        </button>\
        <button type="button" class="btn btn-default" ng-click="rotate(\'right\')" ng-disabled="!btnRotateEnabled()" title="Повернуть по часовой стрелке">\
            <span class="fa fa-rotate-right"></span>\
        </button>\
    </div>\
    <div class="btn-group btn-group-lg rmargin10" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="zoom(1)" ng-disabled="!btnZoomInEnabled()" title="Увеличить">\
            <span class="fa fa-plus"></span>\
        </button>\
        <label class="label label-default">[[scalePct]] %</label>\
        <button type="button" class="btn btn-default" ng-click="zoom(-1)" ng-disabled="!btnZoomOutEnabled()" title="Уменьшить">\
            <span class="fa fa-minus"></span>\
        </button>\
        <button type="button" class="btn btn-default" ng-click="zoomToFit()" ng-disabled="!btnZoomToFitEnabled()" title="Отобразить по размеру области">\
            <span class="fa fa-arrows-alt"></span>\
        </button>\
    </div>\
    <div class="btn-group btn-group-lg" role="group" aria-label="...">\
        <button type="button" class="btn btn-default" ng-click="cropStart()" ng-disabled="!btnCropStartEnabled()" title="Обрезать изображение">\
            <span class="fa fa-crop"></span>\
        </button>\
        <button type="button" class="btn btn-default btn-success" ng-click="cropApply()" ng-disabled="!btnCropApplyEnabled()" title="Подтвердить">\
            <span class="fa fa-check"></span>\
        </button>\
        <button type="button" class="btn btn-default btn-danger" ng-click="cropCancel()" ng-disabled="!btnCropCancelEnabled()" title="Отменить">\
            <span class="fa fa-times"></span>\
        </button>\
    </div>\
</div>';
            var editor = '<canvas></canvas>';
            return '{0}<div id="imageContainer" style="display: block; height: 100%">{1}</div>'.format(toolbar, editor);
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
;