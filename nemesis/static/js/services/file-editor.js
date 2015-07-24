'use strict';

angular.module('WebMis20')
.service('ScannerService', function ($rootScope, $q, $window, $timeout, $http, WMConfig) {
    this.getImage = function (name, format, resolution) {
        var scanUrl = '{0}?name={1}&format={2}&resolution={3}'.format(
            WMConfig.url.coldstar.scan_process_scan, name, format, resolution);
        var scanImage = new $window.Image(),
            helpCanvas = $window.document.createElement('canvas'),
            helpCtx = helpCanvas.getContext('2d'),
            deferred = $q.defer();

        scanImage.onload = function () {
            helpCanvas.width = scanImage.width;
            helpCanvas.height = scanImage.height;
            helpCtx.drawImage(scanImage, 0, 0);
            $rootScope.$apply(function () {
                deferred.resolve(helpCanvas.toDataURL('image/' + format, 0.65));
            });
            helpCanvas.width = 1;
            helpCanvas.height = 1;
            scanImage.src = "";
        };
        scanImage.onerror = function () {
            $rootScope.$apply(function () {
                deferred.reject()
            });
        };
        scanImage.crossOrigin = 'anonymous';
        $timeout(function () {
            scanImage.src = scanUrl;
        }, 0);
        return deferred.promise;
    };
    this.getDeviceList = function () {
        return $http.get(WMConfig.url.coldstar.scan_get_device_list).then(function (response) {
            return response.data.devices;
        });
    };
})
.service('FileEditModal', [
    '$modal', '$http', 'WMConfig', 'MessageBox', '$rootScope', 'WMFileAttach', 'NotificationService', 'ScannerService',
    function ($modal, $http, WMConfig, MessageBox, $rootScope, WMFileAttach, NotificationService, ScannerService) {

    var _getTemplate = function(openMode, attachType) {
        var template = '\
<div class="modal-header">\
    <button aria-label="Закрыть" ng-click="$dismiss()" class="close" type="button"><span aria-hidden="true">×</span></button>\
    <h3 class="modal-title" ng-bind-html="getTitleText()"></h3>\
</div>\
<div class="modal-body">\
    <div class="row">\
    <div class="col-md-4 vertical-divider" id="docInfo">\
        <div id="addFileBlock" ng-show="addFileBlockVisible()">{0}</div>\
        <div id="metaInfoBlock" class="modal-scrollable-block2">{1}</div>\
    </div>\
    <div class="col-md-8" id="pageInfo">\
        <div class="row">\
            <div class="col-md-12">\
                <div id="image_editor" ng-show="imageSelected()">\
                    <div style="height: 600px">\
                        <wm-image-editor id="image_editor" model-image="currentFile.file.image" mime-type="[[currentFile.file.mime]]"\
                            read-only="checkImageRO()"></wm-image-editor>\
                    </div>\
                </div>\
                <div ng-show="notImageSelected()"><span>Предпросмотр недоступен. Выбранный файл не является изображением.</span></div>\
            </div>\
        </div>\
        <div class="row vmargin10" id="pages">\
            <div class="col-md-8 form-inline">\
                <label class="control-label">Имя файла</label>\
                <input type="text" class="form-control" ng-model="currentFile.name" style="width: inherit;">\
                <!--<button type="button" class="btn btn-sm btn-primary" ng-click="generateFileName(true)" ng-if="canEdit()"\
                    title="Сформировать имя файла">\
                    <span class="glyphicon glyphicon-repeat"></span>\
                </button>-->\
            </div>\
            <div class="col-md-4">\
                <button type="button" class="btn btn-sm btn-danger pull-right" ng-click="deletePage()" ng-if="canEdit()">\
                    <span class="glyphicon glyphicon-minus" title="Удалить страницу"></span>\
                </button>\
                <button type="button" class="btn btn-sm btn-success pull-right" ng-click="addPage()" ng-if="canEdit()">\
                    <span class="glyphicon glyphicon-plus" title="Добавить страницу"></span>\
                </button>\
                <pagination total-items="file_attach.file_document.totalPages()" items-per-page="1"\
                    ng-model="selected.currentPage" ng-change="pageChanged()" previous-text="&lsaquo;"\
                    next-text="&rsaquo;" class="pagination-nomargin pull-right">\
                </pagination>\
            </div>\
        </div>\
    </div>\
    </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-danger pull-left btn-lg" ng-click="deleteFileAttach()" ng-if="btnDelDocumentVisible()"\
        title="Удалить документ целиком">Удалить документ\
    </button>\
    <button type="button" class="btn btn-default btn-lg" ng-click="$dismiss()">Закрыть</button>\
    <button type="button" class="btn btn-success btn-lg" ng-click="save_image()" ng-if="canEdit()">\
        Сохранить\
    </button>\
</div>';
        var addFileTemplate = '\
<div class="nav-tabs-custom" style="box-shadow: none" ng-show="addFileBlockVisible()">\
    <ul class="nav nav-tabs">\
    <li ng-class="{\'active\': mode === \'scanning\'}"><a href="#scanning" ng-model="mode" btn-radio="\'scanning\'">Сканировать</a></li>\
    <li ng-class="{\'active\': mode === \'select_from_fs\'}"><a href="#select_from_fs" ng-model="mode" btn-radio="\'select_from_fs\'">Выбрать существующий</a></li>\
    </ul>\
    <div class="tab-content nohpadding">\
    <div ng-show="mode === \'scanning\'">\
        <ul class="list-unstyled">\
        <li>\
        <a href="javascript:;" class="btn btn-link nohpadding" ng-click="get_device_list()">\
            Получить список доступных устройств\
        </a>\
        <div class="radio" ng-repeat="dev in device_list">\
            <label>\
                <input type="radio" id="dev[[$index]]" ng-model="selected.device" ng-value="dev">\
                [[ dev.vendor ]] [[dev.model]]\
            </label>\
        </div>\
        </li>\
        <li>\
        <label>Качество изображения</label>\
        <select class="form-control" ng-model="selected.scan_options.resolution"\
            ng-options="item.name for item in scan_options.resolutions">\
        </select>\
        </li>\
        <li>\
        <button type="button" class="btn btn-primary tmargin10 btn-lg btn-block" ng-click="start_scan()"\
            ng-disabled="!selected.device">\
            Получить изображение\
        </button>\
        </li>\
        </ul>\
    </div>\
    <div ng-show="mode === \'select_from_fs\'">\
        <ul class="list-unstyled">\
        <li><h4>Выбрать файл</h4></li>\
        <input type="file" wm-input-file file="currentFile.file" on-change="generateFileName(true)"\
            accept="image/*,.pdf,.txt,.odt,.doc,.docx,.ods,.xls,.xlsx">\
        </ul>\
    </div>\
    </div>\
</div>';
        var metaInfoTemplate = '\
<legend>Информация о документе</legend>\
<ng-form name="metaInfoForm">\
    <div class="form-group">\
        <label for="docName">Наименование</label>\
        <input type="text" class="form-control" id="docName" ng-model="file_attach.file_document.name"\
            ng-disabled="!canEdit()" ng-change="generateFileName(true)">\
    </div>\
    <div class="form-group">\
        <label for="documentType">Тип документа</label>\
        <rb-select id="documentType" ng-model="file_attach.doc_type" ref-book="rbDocumentType" ng-disabled="!canEdit()"\
            placeholder="Тип документа" ng-change="generateFileDocumentName()">\
        </rb-select>\
    </div>\
    <label class="radio-inline">\
        <input type="radio" id="relType" ng-model="file_attach.rel_type" ng-value="\'own\'"\
            ng-disabled="!canEdit()">Документ пациента\
    </label>\
    <label class="radio-inline">\
        <input type="radio" id="relType" ng-model="file_attach.rel_type" ng-value="\'relative\'"\
            ng-disabled="!canEdit()">Документ родственника\
    </label>\
    <div class="form-group" ng-show="file_attach.rel_type === \'relative\'">\
        <label for="relativeType">Родство с пациентом</label>\
        <wm-relation-type-rb id="relativeType" class="form-control" name="relativeType"\
            client="client.info" direct="false" ng-model="file_attach.relation_type"\
            ng-change="generateFileDocumentName()" ng-disabled="!canEdit()">\
        </wm-relation-type-rb>\
    </div>\
</ng-form>';

        template = template.format(
            addFileTemplate,
            attachType === 'client' ? (metaInfoTemplate) : ''
        );
        return template;
    };

    function makeAttachFileDocumentInfo(fileAttach) {
        var cfa_copy = _.omit(fileAttach, function (value, key, obj) {
            return key === 'file_document' || !obj.hasOwnProperty(key);
        });
        cfa_copy.file_document = _.omit(fileAttach.file_document, function (value, key, obj) {
            return key === 'files' || !obj.hasOwnProperty(key);
        });
        cfa_copy.file_document.files = [];
        angular.forEach(fileAttach.file_document.files, function (fileMeta, key) {
            var fm_copy,
                fileinfo,
                data;
            if (fileMeta.id) {
                if (fileMeta.isLoaded()) {
                    fm_copy = {
                        meta: {
                            id: fileMeta.id,
                            name: fileMeta.name,
                            idx: fileMeta.idx
                        }
                    };
                    cfa_copy.file_document.files.push(fm_copy);
                }
            } else {
                fileinfo = fileMeta.file;
                data = fileinfo.type === 'image' ? fileinfo.image.src : fileinfo.binary_b64;
                fm_copy = {
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
                cfa_copy.file_document.files.push(fm_copy);
            }
        });

        return cfa_copy;
    }

    function unspace(text) {
        return text.replace(/ /g, '_');
    }

    var FileEditController = function ($scope, file_attach, client_id, client, pageNumber, readOnly) {
        var modes = ['scanning', 'select_from_fs'];
        var scan_image_format = 'jpeg';
        $scope.mode = modes[0];
        $scope.scan_options = {
            resolutions: [
                {name: 'Лучшее (600 dpi)',  value: 600},
                {name: 'Отличное (300 dpi)',value: 300},
                {name: 'Хорошее (150 dpi)', value: 150},
                {name: 'Среднее (75 dpi)',   value: 75}]
        };
        var scanner = null,
            resolution = 2;
        try {
            scanner = JSON.parse(localStorage.getItem('selected_scanner'));
        } catch (e) {}
        try {
            resolution = parseInt(localStorage.getItem('selected_scanner_resolution')) || 2
        } catch (e) {}
        $scope.device_list = (scanner !== null)?[scanner]:[];
        $scope.selected = {
            device: scanner,
            scan_options: {
                resolution: $scope.scan_options.resolutions[resolution]
            },
            currentPage: pageNumber
        };
        $scope.client = client;
        $scope.file_attach = file_attach;

        $scope.get_device_list = function () {
            ScannerService.getDeviceList().then(function (devices) {
                $scope.device_list = devices;
            });
        };
        $scope.$watch('selected.device', function (n, o) {
            if (!angular.equals(n, o)) {
                localStorage.setItem('selected_scanner', JSON.stringify(n));
            }
        });
        $scope.$watch('selected.scan_options.resolution', function (n, o) {
            if (!angular.equals(n, o)) {
                localStorage.setItem('selected_scanner_resolution', _.indexOf($scope.scan_options.resolutions, n));
            }
        });
        $scope.start_scan = function () {
            var loaderTextElem = $('#loaderText'),
                oldText = loaderTextElem.text();
            function before_request() {
                loaderTextElem.text('Идёт сканирование');
                $rootScope.pendingRequests += 1;
            }
            function finalize_request() {
                $rootScope.pendingRequests -= 1;
                loaderTextElem.text(oldText);
            }
            before_request();
            ScannerService.getImage(
                $scope.selected.device.name,
                scan_image_format,
                $scope.selected.scan_options.resolution.value
            ).then(function (image_b64) {
                $scope.currentFile.file.binary_b64 = null;
                $scope.currentFile.file.image = new Image();
                $scope.currentFile.file.mime = 'image/' + scan_image_format;
                $scope.currentFile.file.type = 'image';
                $scope.currentFile.file.image.src = image_b64;
                $scope.generateFileName();

                finalize_request();
            }, function () {
                NotificationService.notify(null,
                    'Загрузка изображения не удалась. Повторите попытку позже',
                    'danger'
                );
                finalize_request();
            });
        };
        $scope.save_image = function () {
            var validity = $scope.validate();
            if (!validity.result) {
                NotificationService.notify(null,
                    'Невозможно сохранить документ: ' + validity.message,
                    'danger',
                    true
                );
                return;
            }
            $http.post(WMConfig.url.api_patient_file_attach_save, {
                client_id: client_id,
                file_attach: makeAttachFileDocumentInfo($scope.file_attach)
            }).success(function (data, status) {
                $scope.file_attach.load(data.result.cfa);
                NotificationService.notify(
                    status,
                    'Сохранено',
                    'success',
                    true
                );
            }).error(function (data, status) {
                NotificationService.notify(
                    status,
                    'Ошибка сохранения',
                    'danger'
                );
            });
        };
        $scope.deleteFileAttach = function () {
            MessageBox.question(
                'Удаление документа',
                'Документ будет удален. Продолжить?'
            ).then(function () {
                $http.delete(WMConfig.url.api_patient_file_attach_delete, {
                    params: {
                        cfa_id: $scope.file_attach.id
                    }
                }).success(function () {
                    $scope.$close('deleted');
                }).error(function (data, status) {
                    NotificationService.notify(
                        status,
                        'Ошибка удаления документа',
                        'danger'
                    );
                });
            });
        };

        $scope.addPage = function () {
            $scope.file_attach.file_document.addPage();
            $scope.selected.currentPage = $scope.file_attach.file_document.totalPages();
            $scope.pageChanged();
        };
        $scope.deletePage = function () {
            function setCurPage() {
                if (!$scope.file_attach.file_document.totalPages()) {
                    $scope.file_attach.file_document.addPage();
                }
                if ($scope.selected.currentPage > $scope.file_attach.file_document.totalPages()) {
                    $scope.selected.currentPage = $scope.selected.currentPage - 1
                }
                $scope.pageChanged();
            }

            if ($scope.currentFile.id) {
                MessageBox.question(
                    'Удаление страницы документа',
                    'Текущая страница документа будет удалена. Продолжить?'
                ).then(function () {
                    $http.delete(WMConfig.url.api_patient_file_attach_delete, {
                        params: {
                            file_meta_id: $scope.currentFile.id
                        }
                    }).success(function (data, status) {
                        $scope.file_attach.file_document.removePage($scope.selected.currentPage);
                        setCurPage();
                        NotificationService.notify(
                            status,
                            'Страница удалена',
                            'success',
                            true
                        );
                    }).error(function (data, status) {
                        NotificationService.notify(
                            status,
                            'Ошибка удаления страницы',
                            'danger'
                        );
                    });
                });
            } else {
                $scope.file_attach.file_document.removePage($scope.selected.currentPage);
                setCurPage();
            }
        };
        $scope.pageChanged = function () {
            if ($scope.currentFile) {
                $scope.currentFile.file.selected = false;
            }
            $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);
            if ($scope.currentFile.id && !$scope.currentFile.isLoaded()) {
                $http.get(WMConfig.url.api_patient_file_attach, {
                    params: {
                        file_meta_id: $scope.currentFile.id
                    }
                }).success(function (data) {
                    $scope.currentFile.load(data.result, true);
                }).error(function (data, status) {
                    NotificationService.notify(
                        status,
                        data.meta.name,
                        'danger'
                    );
                });
            }
        };
        $scope.generateFileName = function (force) {
            if ($scope.currentFile.name && !force) {
                return
            }
            var docFileName = $scope.file_attach.file_document.name,
                name = '{0}{_(|1|)}_лист_{2}'.formatNonEmpty(
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
            $scope.generateFileName(true);
        };
        $scope.$watch('file_attach.rel_type', function (n, o) {
            if (n !== 'relative') {
                $scope.file_attach.relation_type = null;
                $scope.generateFileDocumentName();
            }
        });

        $scope.getTitleText = function () {
            var text = '{0}<small>{, |1|}</small>'.formatNonEmpty(
                $scope.file_attach.id ? 'Просмотр копии' : 'Добавление копии', (
                    safe_traverse($scope.file_attach, ['document_info', 'doc_text']) ||
                    safe_traverse($scope.file_attach, ['policy_info', 'policy_text'])
                )
            );
            return text;
        };
        $scope.canEdit = function () {
            return !readOnly;
        };
        $scope.checkImageRO = function () {
            return !$scope.canEdit || $scope.currentFile.id;
        };
        $scope.btnDelDocumentVisible = function () {
            return $scope.canEdit() && $scope.file_attach.id;
        };
        $scope.addFileBlockVisible = function () {
            return $scope.canEdit() && !$scope.currentFile.id;
        };
        $scope.imageSelected = function () {
            return $scope.currentFile.isImage();
        };
        $scope.notImageSelected = function () {
            return $scope.currentFile.isNotImage();
        };
        $scope.validate = function () {
            var validity = {
                result: true,
                message: 'ok'
            },
                files = $scope.file_attach.file_document.files,
                curFile;
            for (var idx in files) {
                if (files.hasOwnProperty(idx)) {
                    curFile = files[idx];
                    if (!curFile.id && !curFile.isLoaded()) {
                        validity.result = false;
                        validity.message = 'Не выбран файл на {0} странице документа'.format(curFile.idx + 1);
                        break;
                    }
                }
            }
            return validity;
        };

        $scope.pageChanged();
    };

    return {
        addNew: function (client_id, params) {
            var file_attach = new WMFileAttach(),
                documentInfo = params.documentInfo,
                policyInfo = params.policyInfo;
            file_attach.file_document.addPage();
            if (documentInfo) {
                file_attach.setDocumentInfo(documentInfo);
            } else if (policyInfo) {
                file_attach.setPolicyInfo(policyInfo);
            }
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
                    },
                    pageNumber: function () {
                        return 1;
                    },
                    readOnly: function () {
                        return false;
                    }
                }
            });
            return instance.result;
        },
        open: function (cfa_id, params) {
            var idx = params.idx || 0,
                file_attach,
                readOnly = !params.editMode;
            return $http.get(WMConfig.url.api_patient_file_attach, {
                params: {
                    cfa_id: cfa_id
                }
            }).then(function (response) {
                var pages = response.data.result.file_pages;
                file_attach = new WMFileAttach(response.data.result.cfa);
                if (pages.length) {
                    file_attach.file_document.setPages(pages);
                } else {
                    file_attach.file_document.addPage();
                }
                return open_modal();
            }, function () {
                alert('Ошибка открытия документа');
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
                        },
                        pageNumber: function () {
                            return idx + 1;
                        },
                        readOnly: function () {
                            return readOnly;
                        }
                    }
                });
                return instance.result;
            }
        }
    };
}])
.factory('WMFile', [function () {
    var WMFile = function (source, refreshFileData) {
        if (!source) {
            this.mime = null;
            this.size = null;
            this.name = null;
            this.type = null;
            this.image = null;
            this.binary_b64 = null;
        } else {
            this.load(source, refreshFileData);
        }
    };
    WMFile.prototype.load = function (source, refreshData) {
        this.mime = source.mime;
        this.size = source.size;
        this.name = source.name;
        if (refreshData) {
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
        }
    };
    return WMFile;
}])
.factory('WMFileMeta', ['WMFile', function (WMFile) {
    var WMFileMeta = function (source) {
        if (!source) {
            this.id = null;
            this.name = null;
            this.idx = null;
            this.file = new WMFile();
        } else {
            this.load(source, true);
        }
    };
    WMFileMeta.prototype.load = function (source, refreshFileData) {
        this.id = source.id;
        this.name = source.name;
        this.idx = source.idx;
        if (!this.file) {
            this.file = new WMFile(source, refreshFileData);
        } else {
            this.file.load(source, refreshFileData);
        }
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
    return WMFileMeta;
}])
.factory('WMFileDocument', ['WMFileMeta', function (WMFileMeta) {
    var WMFileDocument = function (source) {
        if (!source) {
            this.id = null;
            this.name = null;
            this.files = [];
        } else {
            this.load(source);
        }
    };
    WMFileDocument.prototype.load = function (source) {
        this.id = source.id;
        this.name = source.name;
        if (!this.files) {
            this.files = [];
        }
        angular.forEach(source.files, function (file_meta) {
            if (!this.files.hasOwnProperty(file_meta.idx)) {
                this.files[file_meta.idx] = new WMFileMeta(file_meta);
            } else {
                this.files[file_meta.idx].load(file_meta);
            }
        }, this);
    };
    WMFileDocument.prototype.setPages = function (pages) {
        angular.forEach(pages, function (page) {
            if (!this.files.hasOwnProperty(page.idx)) {
                this.files[page.idx] = new WMFileMeta({
                    id: page.id,
                    idx: page.idx
                });
            }
        }, this);
    };
    WMFileDocument.prototype.removePage = function (page) {
        var idx = page - 1;
        this.files.splice(idx, 1);
        this.files.filter(function (page) {
            return page.idx > idx;
        }).forEach(function (page) {
            page.idx -= 1;
        });
    };
    WMFileDocument.prototype.addPage = function () {
        this.files.push(new WMFileMeta({
            idx: this.totalPages()
        }));
    };
    WMFileDocument.prototype.getFile = function (pageNum) {
        return this.files[pageNum - 1];
    };
    WMFileDocument.prototype.totalPages = function () {
        return this.files.length;
    };
    return WMFileDocument;
}])
.factory('WMFileAttach', ['WMFileDocument', function (WMFileDocument) {
    var WMFileAttach = function (source) {
        if (!source) {
            this.id = null;
            this.attach_date = null;
            this.doc_type = null;
            this.relation_type = null;
            this.document_info = null;
            this.policy_info = null;
            this.file_document = new WMFileDocument();
        } else {
            this.load(source);
        }
        this.rel_type = this.relation_type ? 'relative': 'own';
    };
    WMFileAttach.prototype.load = function (source) {
        this.id = source.id;
        this.attach_date = source.attach_date;
        this.doc_type = source.doc_type;
        this.relation_type = source.relation_type;
        this.document_info = source.document_info;
        this.policy_info = source.policy_info;
        if (!this.file_document) {
            this.file_document = new WMFileDocument(source.file_document);
        } else {
            this.file_document.load(source.file_document);
        }
    };
    WMFileAttach.prototype.setDocumentInfo = function (document) {
        this.document_info = document;
        this.doc_type = document.doc_type;
    };
    WMFileAttach.prototype.setPolicyInfo = function (policy) {
        this.policy_info = policy;
        // todo: set doc_type based on policy type
    };
    return WMFileAttach;
}])
;
