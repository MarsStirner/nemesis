/**
 * Created by mmalkov on 12.02.15.
 */

angular.module('hitsl.ui')
.directive("wmMultiselect", ['$window', '$templateCache', function($window, $templateCache) {
    return {
        restrict: "A",
        scope: {
            items: '=',
            disabled: '=ngDisabled',
            freetext: '@',
            "class": '@',
            limit: '@'
        },
        require: '?ngModel',
        replace: true,
        template: function(el, attributes) {
            var defaultItemTpl, itemTpl;
            defaultItemTpl = "{{ item }}";
            itemTpl = el.html() || defaultItemTpl;
            return $templateCache.get('templates/fs/multiselect.html').replace(/::item-template/g, itemTpl);
        },
        controller: function($scope, $element, $attrs, $filter) {
            if ($attrs.freetext != null) {
                $scope.dynamicItems = function() {
                    if ($scope.search) {
                        return [$scope.search];
                    } else {
                        return [];
                    }
                };
            } else {
                $scope.dynamicItems = function() {
                    return [];
                };
            }
            $scope.updateDropdownItems = function() {
                var allItems, excludeFilter, searchFilter, limitFilter;
                searchFilter = $filter('filter');
                excludeFilter = $filter('exclude');
                limitFilter = $filter('limitTo');
                allItems = ($scope.items || []).concat($scope.dynamicItems());
                return $scope.dropdownItems = limitFilter(searchFilter(excludeFilter(allItems, $scope.selectedItems), $scope.search), $scope.limit);
            };
            $scope.selectItem = function(item) {
                if ((item != null) && _.indexOf($scope.selectedItems, item) === -1) {
                    $scope.selectedItems = $scope.selectedItems.concat([item]);
                }
                return $scope.search = '';
            };
            $scope.unselectItem = function(item) {
                var index;
                index = _.indexOf($scope.selectedItems, item);
                if (index > -1) {
                    return $scope.selectedItems.splice(index, 1);
                }
            };
            $scope.onBlur = function() {
                $scope.active = false;
                return $scope.search = '';
            };
            $scope.onEnter = function() {
                return $scope.selectItem($scope.dropdownItems.length > 0 ? $scope.listInterface.selectedItem : null);
            };
            $scope.listInterface = {
                onSelect: function(selectedItem) {
                    return $scope.selectItem(selectedItem);
                },
                move: function() {
                    return console.log("not-implemented listInterface.move() function");
                }
            };
            $scope.dropdownItems = [];
            $scope.active = false;
            $scope.$watchCollection('selectedItems', function() {
                return $scope.updateDropdownItems();
            });
            $scope.$watchCollection('items', function() {
                return $scope.updateDropdownItems();
            });
            $scope.$watch('search', function() {
                return $scope.updateDropdownItems();
            });
            return $scope.updateDropdownItems();
        },
        link: function($scope, element, attrs, ngModelCtrl, transcludeFn) {
            var setViewValue;
            if (ngModelCtrl) {
                setViewValue = function(newValue, oldValue) {
                    if (!angular.equals(newValue, oldValue)) {
                        return ngModelCtrl.$setViewValue(newValue);
                    }
                };
                $scope.$watch('selectedItems', setViewValue, true);
                return ngModelCtrl.$render = function() {
                    return $scope.selectedItems = ngModelCtrl.$modelValue || [];
                };
            }
        }
    };
}])
.service('FileEditModal', ['$modal', '$http', 'WMConfig', function ($modal, $http, WMConfig) {
    function _getTemplate(openMode, attachType) {
        var template = '\
<div class="modal-header">\
    <h3 class="modal-title">Добавление документа</h3>\
</div>\
<div class="modal-body">\
    <div class="row">\
        <div class="col-md-4">\
            <div class="btn-group">\
                <label class="btn btn-default" ng-model="mode" btn-radio="\'scanning\'">Сканировать</label>\
                <label class="btn btn-default" ng-model="mode" btn-radio="\'select_existing\'">Выбрать файл</label>\
            </div>\
        </div>\
        <div id="pages" class="col-md-8">\
            <div class="row">\
                <div class="col-md-8 form-inline">\
                    <label class="control-label">Имя файла</label>\
                    <input type="text" class="form-control" ng-model="currentFile.name" style="width: inherit;">\
                    <button type="button" class="btn btn-sm btn-primary" ng-click="generateFileName(true)" title="Сформировать имя файла">\
                        <span class="glyphicon glyphicon-repeat"></span>\
                    </button>\
                </div>\
                <div class="col-md-4">\
                    <button type="button" class="btn btn-sm btn-success pull-right" ng-click="addPage()">\
                        <span class="glyphicon glyphicon-plus" title="Добавить страницу"></span>\
                    </button>\
                    <pagination total-items="file_attach.file_document.totalPages()" items-per-page="1" ng-model="selected.currentPage" ng-change="pageChanged()"\
                        previous-text="&lsaquo;" next-text="&rsaquo;" class="pagination-nomargin pull-right"></pagination>\
                </div>\
            </div>\
        </div>\
    </div>\
    <hr>\
    <div class="row">\
    <div class="col-md-4">\
        {0}\
        {1}\
    </div>\
    <div class="col-md-8">\
        <div id="image_editor" ng-show="imageSelected()">\
        <div class="btn-toolbar marginal bg-muted" role="toolbar" aria-label="...">\
            <div class="btn-group btn-group-lg pull-right" role="group" aria-label="...">\
                <button type="button" class="btn btn-default" ng-click="reset_image()" title="Вернуться к исходному изображению">\
                    <span class="fa fa-refresh"></span>\
                </button>\
                <button type="button" class="btn btn-default" ng-click="clear_image()" title="Очистить область изображения">\
                    <span class="fa fa-times"></span>\
                </button>\
            </div>\
            <div class="btn-group btn-group-lg rmargin10" role="group" aria-label="...">\
                <button type="button" class="btn btn-default" ng-click="rotate(\'left\')" title="Повернуть против часовой стрелки">\
                    <span class="fa fa-rotate-left"></span>\
                </button>\
                <button type="button" class="btn btn-default" ng-click="rotate(\'right\')" title="Повернуть по часовой стрелке">\
                    <span class="fa fa-rotate-right"></span>\
                </button>\
            </div>\
            <div class="btn-group btn-group-lg rmargin10" role="group" aria-label="...">\
                <button type="button" class="btn btn-default" ng-click="zoom(1)" title="Увеличить">\
                    <span class="fa fa-plus"></span>\
                </button>\
                <label class="label label-default">[[scalePct]] %</label>\
                <button type="button" class="btn btn-default" ng-click="zoom(-1)" title="Уменьшить">\
                    <span class="fa fa-minus"></span>\
                </button>\
            </div>\
            <div class="btn-group btn-group-lg" role="group" aria-label="...">\
                <button type="button" class="btn btn-default" ng-click="crop(\'Start\')" title="Обрезать изображение">\
                    <span class="fa fa-crop"></span>\
                </button>\
                <button type="button" class="btn btn-default btn-success" ng-click="crop(\'Apply\')" title="Подтвердить">\
                    <span class="fa fa-check"></span>\
                </button>\
                <button type="button" class="btn btn-default btn-danger" ng-click="crop(\'Cancel\')" title="Отменить">\
                    <span class="fa fa-times"></span>\
                </button>\
            </div>\
        </div>\
        <div class="modal-scrollable-block">\
            <wm-image-editor id="image_editor" model-image="currentFile.file.image"></wm-image-editor>\
        </div>\
        </div>\
        <div ng-show="notImageSelected()"><span>Предпросмотр недоступен. Выбранный файл не является изображением.</span></div>\
    </div>\
    </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-success" ng-click="save_image()" ng-disabled="!correctFileSelected()">\
        Сохранить\
    </button>\
    <button type="button" class="btn btn-danger" ng-click="$dismiss()">Закрыть</button>\
</div>';
        var addFileTemplate = '\
<div ng-show="mode === \'scanning\'">\
    <ol>\
    <li><h4>Выбрать устройство</h4></li>\
    <button type="button" class="btn btn-primary btn-sm" ng-click="get_device_list()">\
        Получить список доступных устройств\
    </button>\
    <div class="radio" ng-repeat="dev in device_list">\
        <label>\
            <input type="radio" id="dev[[$index]]" ng-model="selected.device"\
                ng-value="dev">[[dev.model]]\
        </label>\
    </div>\
    <hr>\
    <li><h4>Настроить параметры сканирования</h4></li>\
    <label>Качество изображения</label>\
    <select><option>Хорошее</option></select>\
    <label>Режим сканирования</label>\
    <select><option>Цветной</option></select>\
    <hr>\
    <li><h4>Начать сканирование</h4></li>\
    <button type="button" class="btn btn-warning btn-sm" ng-click="start_scan()"\
        ng-disabled="!selected.device">\
        Получить изображение\
    </button>\
    </ol>\
</div>\
<div ng-show="mode === \'select_existing\'">\
    <input type="file" wm-input-file file="currentFile.file" on-change="generateFileName()"\
        accept="image/*,.pdf,.txt,.odt,.doc,.docx,.ods,.xls,.xlsx">\
</div>\
<hr>';
        var metaInfoTemplate = '\
<div id="metaInfoBlock" class="modal-scrollable-block2">\
    <legend>Информация о документе</legend>\
    <ng-form name="metaInfoForm">\
        <div class="form-group">\
            <label for="docName">Наименование</label>\
            <input type="text" class="form-control" id="docName" ng-model="file_attach.file_document.name">\
        </div>\
        <div class="form-group">\
            <label for="documentType">Тип документа</label>\
            <rb-select id="documentType" ng-model="file_attach.doc_type" ref-book="rbDocumentType"\
                placeholder="Тип документа" ng-change="generateFileDocumentName()">\
            </rb-select>\
        </div>\
        <label class="radio-inline">\
            <input type="radio" id="relType" ng-model="file_attach.rel_type" ng-value="\'own\'" ng>Документ пациента\
        </label>\
        <label class="radio-inline">\
            <input type="radio" id="relType" ng-model="file_attach.rel_type" ng-value="\'relative\'">Документ родственника\
        </label>\
        <div class="form-group" ng-show="file_attach.rel_type === \'relative\'">\
            <label for="relativeType">Родство с пациентом</label>\
            <wm-relation-type-rb id="relativeType" class="form-control" name="relativeType"\
                client="client.info" direct="false" ng-model="file_attach.relation_type"\
                ng-change="generateFileDocumentName()" ng-required="relativeRequired()">\
            </wm-relation-type-rb>\
        </div>\
        <div class="form-group" ng-show="file_attach.rel_type === \'own\'">\
            <label for="relDocType">Связанный документ</label>\
            <span id="conDoc"></span>\
        </div>\
    </ng-form>\
</div>';

        template = template.format(
            openMode === 'new' ? (addFileTemplate) : '',
            attachType === 'client' ? (metaInfoTemplate) : ''
        );
        return template;
    }

    var WMFile = function (source) {
        if (!source) {
            this.mime = null;
            this.size = null;
            this.name = null;
            this.type = null;
            this.image = null;
            this.binary_b64 = null;
        } else {
            this.load(source);
        }
    };
    WMFile.prototype.load = function (source) {
        this.mime = source.mime;
        this.size = source.size;
        this.name = source.name;
        if (this.mime === null || this.mime === undefined) {
            this.type = this.image = this.binary_b64 = null;
        } else if (/image/.test(this.mime)) {
            this.type = 'image';
            this.image = new Image();
            this.image.src = "data:{0};base64,".format(this.mime) + source.data;
            this.binary_b64 = null;
        } else {
            this.type = 'other';
            this.binary_b64 = source.data;
            this.image = null;
        }
    };

    var WMFileMeta = function (source, idx, id) {
        if (!source) {
            this.id = id || null;
            this.name = null;
            this.idx = idx || null;
            this.setFile();
        } else {
            angular.extend(this, source);
            this.file = new WMFile(source); // TODO
        }
    };
    WMFileMeta.prototype.setFile = function (file) {
        this.file = new WMFile(file);
    };
    WMFileMeta.prototype.isImage = function () {
        return this.file.type === 'image' && this.file.image.src;
    };
    WMFileMeta.prototype.isNotImage = function () {
        return this.file.type === 'other' && this.file.binary_b64;
    };
    WMFileMeta.prototype.isLoaded = function () {
        return this.file.type === 'image' ? Boolean(this.file.image.src) : Boolean(this.file.binary_b64);
    };

    var WMFileDocument = function (source) {
        if (!source) {
            this.id = null;
            this.name = null;
            this.files = [];
        } else {
            angular.extend(this, source);
            this.files = [];
            angular.forEach(source.files, function (file) {
                this.files[file.idx] = new WMFileMeta(file);
            }, this);
        }
    };
    WMFileDocument.prototype.addPage = function () {
        this.files.push(new WMFileMeta(null, this.files.length));
    };
    WMFileDocument.prototype.getFile = function (pageNum) {
        return this.files[pageNum - 1];
    };
    WMFileDocument.prototype.totalPages = function () {
        return this.files.length;
    };
    WMFileDocument.prototype.setPages = function (pages) {
        angular.forEach(pages, function (fm) {
            if (!this.files.hasOwnProperty(fm[1])) {
                this.files[fm[1]] = new WMFileMeta(null, fm[1], fm[0]);
            }
        }, this);
    };

    var WMFileAttach = function (source) {
        if (!source) {
            this.id = null;
            this.attach_date = null;
            this.doc_type = null;
            this.relation_type = null;
            this.file_document = new WMFileDocument();
        } else {
            angular.extend(this, source);
            this.file_document = new WMFileDocument(source.file_document);
        }
        this.rel_type = this.relation_type ? 'relative': 'own';
    };

    function makeAttachFileDocumentInfo(fileAttach) {
        angular.forEach(fileAttach.file_document.files, function (fileMeta, key) {
            var fileinfo = fileMeta.file,
                data = fileinfo.type === 'image' ? fileinfo.image.src : fileinfo.binary_b64;

            fileAttach.file_document.files[key] = {
                meta: {
                    id: fileMeta.id,
                    name: fileMeta.name,
                    idx: fileMeta.idx
                },
                file: {
                    mime: fileinfo.mime,
                    data: data
                }
            };
        });
        return fileAttach;
    }

    function capitalize(text) {
        return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
    }
    function unspace(text) {
        return text.replace(/ /g, '_');
    }

    var FileEditController = function ($scope, file_attach, client_id, client) {
        $scope.client = client;
        $scope.mode = 'scanning';
        $scope.device_list = [];
        $scope.selected = {
            device: {},
            currentPage: 1
        };
        $scope.file_attach = file_attach;
        $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);
        var scales = [5, 10, 15, 30, 50, 75, 90, 100, 125, 150, 200, 300, 400, 500];
        $scope.scalePct = 100;

        $scope.get_device_list = function () {
            $http.get(WMConfig.url.scanserver.list).success(function (data) {
                $scope.device_list = data.devices;
            });
        };
        $scope.start_scan = function () {
            $http.post(WMConfig.url.scanserver.scan, {
                name: $scope.selected.device.name
            }).success(function (data) {
                $scope.image = new Image();
                $scope.image.src = 'data:image/png;base64,' + data.image;
                $scope.file.encoded = $scope.image;
            });
        };
        $scope.save_image = function () {
            $http.post(WMConfig.url.api_patient_file_attach, {
                client_id: client_id,
                file_attach: makeAttachFileDocumentInfo($scope.file_attach)
            }).success(function () {
                alert('Сохранено');
            }).error(function () {
                alert('Ошибка сохранения');
            });
        };
        $scope.clear_image = function () {
            $scope.file.image = null;
            $scope.image = null;
        };
        $scope.reset_image = function () {
            $scope.$broadcast('resetImage');
        };
        $scope.rotate = function (w) {
            var angle = w === 'left' ? -15 : 15;
            $scope.$broadcast('rotateImage', {
                angle: angle
            });
        };
        $scope.zoom = function (how) {
            $scope.scalePct = scales[scales.indexOf($scope.scalePct) + how];
            $scope.$broadcast('zoomImage', {
                scalePct: $scope.scalePct
            });
        };
        $scope.crop = function (action) {
            $scope.$broadcast('cropImage' + action);
        };

        $scope.addPage = function () {
            $scope.file_attach.file_document.addPage();
            $scope.selected.currentPage = $scope.file_attach.file_document.totalPages();
            $scope.pageChanged();
        };
        $scope.pageChanged = function () {
            $scope.currentFile.file.selected = false;
            $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);
            if ($scope.currentFile.id && !$scope.currentFile.isLoaded()) {
                $http.get(WMConfig.url.api_patient_file_attach, {
                    params: {
                        file_meta_id: $scope.currentFile.id
                    }
                }).success(function (data) {
                    $scope.currentFile.file.load(data.result);
                }).error(function () {
                    alert('Ошибка открытия файла. Файл был удален.');
                });
            }
        };
        $scope.generateFileName = function (force) {
            if ($scope.currentFile.name && !force) {
                return
            }
            var docFileName = $scope.file_attach.file_document.name,
                name = '{0}{_(|1|)}_Лист_№{2}'.formatNonEmpty(
                    unspace(docFileName ? docFileName :
                            safe_traverse($scope.file_attach, ['doc_type', 'name'], 'Файл')
                    ),
                    docFileName ? '' : safe_traverse($scope.file_attach, ['relation_type', 'leftName'], ''),
                    $scope.currentFile.idx + 1
                );
            $scope.currentFile.name = name;
        };
        $scope.generateFileDocumentName = function () {
            var name = '{0}{ (|1|)}'.formatNonEmpty(
                safe_traverse($scope.file_attach, ['doc_type', 'name'], 'Документ'),
                safe_traverse($scope.file_attach, ['relation_type', 'leftName'], '')
            );
            $scope.file_attach.file_document.name = name;
        };
        $scope.$watch('file_attach.rel_type', function (n, o) {
            if (n !== 'relative') {
                $scope.file_attach.relation_type = null;
                $scope.generateFileDocumentName();
            }
        });

        $scope.imageSelected = function () {
            return $scope.currentFile.isImage();
        };
        $scope.notImageSelected = function () {
            return $scope.currentFile.isNotImage();
        };
        $scope.correctFileSelected = function () {
            return true || $scope.file.type === 'image' ? // TODO
                $scope.imageSelected() :
                $scope.notImageSelected();
        };
    };
    return {
        addNew: function (client_id, params) {
            var file_attach = new WMFileAttach();
            file_attach.file_document.addPage();
            var instance = $modal.open({
                template: _getTemplate('new', params.attachType),
                controller: FileEditController,
                backdrop: 'static',
                size: 'lg',
                windowClass: 'modal-full-screen',
                resolve: {
                    file_attach: function () {
                        return file_attach;
                    },
                    client_id: function () {
                        return client_id;
                    },
                    client: function () {
                        return params.client;
                    }
                }
            });
            return instance.result;
        },
        open: function (cfa_id, params) {
            var idx = params.idx,
                file_attach;
            return $http.get(WMConfig.url.api_patient_file_attach, {
                params: {
                    cfa_id: cfa_id,
                    idx: idx
                }
            }).success(function (data) {
                file_attach = new WMFileAttach(data.result.cfa);
                file_attach.file_document.setPages(data.result.other_pages);
                return open_modal();
            }).error(function () {
                alert('Ошибка открытия файла. Файл был удален.');
            });

            function open_modal() {
                var instance = $modal.open({
                    template: _getTemplate('open', params.attachType),
                    controller: FileEditController,
                    backdrop: 'static',
                    size: 'lg',
                    windowClass: 'modal-full-screen',
                    resolve: {
                        file_attach: function () {
                            return file_attach;
                        },
                        client_id: function () {
                            return params.client.client_id;
                        },
                        client: function () {
                            return params.client;
                        }
                    }
                });
                return instance.result;
            }
        }
    };
}])
.run(['$templateCache', function ($templateCache) {
    $templateCache.put('/WebMis20/modal-MessageBox-info.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-success" ng-click="$close()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-error.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="message"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$dismiss()">Ок</button>\
        </div>'
    );
    $templateCache.put('/WebMis20/modal-MessageBox-question.html',
        '<div class="modal-header" xmlns="http://www.w3.org/1999/html">\
            <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
            <h4 class="modal-title">[[head_msg]]</h4>\
        </div>\
        <div class="modal-body">\
            <p ng-bind-html="question"></p>\
        </div>\
        <div class="modal-footer">\
            <button type="button" class="btn btn-danger" ng-click="$close(true)">Да</button>\
            <button type="button" class="btn btn-default" ng-click="$dismiss()">Отмена</button>\
        </div>'
    );
}]);