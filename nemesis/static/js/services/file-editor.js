'use strict';

angular.module('WebMis20')
.service('FileEditModal', [
    '$modal', '$http', 'WMConfig', 'MessageBox', '$rootScope', 'WMFileAttach', 'NotificationService',
    function ($modal, $http, WMConfig, MessageBox, $rootScope, WMFileAttach, NotificationService) {

    var _getTemplate = function(openMode, attachType) {
        var template = '\
<div class="modal-header">\
    <h3 class="modal-title" ng-bind="getTitleText()"></h3>\
</div>\
<div class="modal-body">\
    <div class="row">\
    <div class="col-md-4 vertical-divider" id="docInfo">\
        <div id="addFileBlock" ng-show="addFileBlockVisible()">{0}</div>\
        <div id="metaInfoBlock" class="modal-scrollable-block2">{1}</div>\
    </div>\
    <div class="col-md-8" id="pageInfo">\
        <div class="row marginal" id="pages">\
            <div class="col-md-8 form-inline">\
                <label class="control-label">Имя файла</label>\
                <input type="text" class="form-control" ng-model="currentFile.name" style="width: inherit;">\
                <button type="button" class="btn btn-sm btn-primary" ng-click="generateFileName(true)" ng-if="canEdit()"\
                    title="Сформировать имя файла">\
                    <span class="glyphicon glyphicon-repeat"></span>\
                </button>\
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
        <div class="row">\
            <div class="col-md-12">\
                <div alert-notify></div>\
                <div id="image_editor" ng-show="imageSelected()">\
                    <div class="modal-scrollable-block">\
                        <wm-image-editor id="image_editor" model-image="currentFile.file.image" read-only="checkImageRO()"></wm-image-editor>\
                    </div>\
                </div>\
                <div ng-show="notImageSelected()"><span>Предпросмотр недоступен. Выбранный файл не является изображением.</span></div>\
            </div>\
        </div>\
    </div>\
    </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-danger pull-left" ng-click="deleteFileAttach()" ng-if="btnDelDocumentVisible()"\
        title="Удалить документ целиком">Удалить документ\
    </button>\
    <button type="button" class="btn btn-success" ng-click="save_image()" ng-if="canEdit()">\
        Сохранить\
    </button>\
    <button type="button" class="btn btn-danger" ng-click="$dismiss()">Закрыть</button>\
</div>';
        var addFileTemplate = '\
<div class="btn-group" ng-show="addFileBlockVisible()">\
    <label class="btn btn-default" ng-model="mode" btn-radio="\'scanning\'">Сканировать</label>\
    <label class="btn btn-default" ng-model="mode" btn-radio="\'select_from_fs\'">Выбрать существующий</label>\
</div>\
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
    <li><h4>Настроить параметры сканирования</h4></li>\
    <label>Качество изображения</label>\
    <select class="form-control" ng-model="selected.scan_options.resolution"\
        ng-options="item.name for item in scan_options.resolutions">\
    </select>\
    <label>Режим сканирования</label>\
    <select class="form-control" ng-model="selected.scan_options.mode"\
        ng-options="item.name for item in scan_options.modes">\
    </select>\
    <li><h4>Начать сканирование</h4></li>\
    <button type="button" class="btn btn-warning btn-sm" ng-click="start_scan()"\
        ng-disabled="!selected.device">\
        Получить изображение\
    </button>\
    </ol>\
</div>\
<div ng-show="mode === \'select_from_fs\'">\
    <ul>\
    <li><h4>Выбрать файл</h4></li>\
    <input type="file" wm-input-file file="currentFile.file" on-change="generateFileName()"\
        accept="image/*,.pdf,.txt,.odt,.doc,.docx,.ods,.xls,.xlsx">\
    </ul>\
</div>\
<hr>';
        var metaInfoTemplate = '\
<legend>Информация о документе</legend>\
<ng-form name="metaInfoForm">\
    <div class="form-group">\
        <label for="docName">Наименование</label>\
        <input type="text" class="form-control" id="docName" ng-model="file_attach.file_document.name"\
            ng-disabled="!canEdit()">\
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
        $scope.mode = modes[0];
        $scope.scan_options = {
            resolutions: [
                {name: 'Лучшее',        value: 600},
                {name: 'Отличное',      value: 300},
                {name: 'Хорошее',       value: 150},
                {name: 'Нормальное',    value: 75}],
            modes: [
                {name: 'Цветное',       value: 'Color'},
                {name: 'Чёрно-белое',   value: 'Gray'}]
        };
        $scope.device_list = [];
        $scope.selected = {
            device: null,
            scan_options: {
                resolution: $scope.scan_options.resolutions[2],
                mode: $scope.scan_options.modes[0]
            },
            currentPage: pageNumber
        };
        $scope.client = client;
        $scope.file_attach = file_attach;
        $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);

        $scope.get_device_list = function () {
            $http.get(WMConfig.url.coldstar.scan_get_device_list).success(function (data) {
                $scope.device_list = data.devices;
            });
        };
        $scope.start_scan = function () {
            function getImage(scanUrl, callback) {
                var scanImage = new Image(),
                    helpCanvas = document.createElement('canvas'),
                    helpCtx = helpCanvas.getContext('2d');
                scanImage.onload = function () {
                    $scope.$apply(function () {
                        helpCanvas.width = scanImage.width;
                        helpCanvas.height = scanImage.height;
                        helpCtx.drawImage(scanImage, 0, 0);

                        callback(helpCanvas.toDataURL());

                        helpCanvas.width = 1;
                        helpCanvas.height = 1;
                        scanImage.src = "";
                    });
                };
                scanImage.crossOrigin = 'anonymous';
                scanImage.src = scanUrl
            }

            var scanUrl = '{0}?name={1}&resolution={2}&mode={3}'.format(
                WMConfig.url.coldstar.scan_process_scan,
                $scope.selected.device.name,
                $scope.selected.scan_options.resolution.value,
                $scope.selected.scan_options.mode.value
            );

            var loaderTextElem = $('#loaderText'),
                oldText = loaderTextElem.text();
            loaderTextElem.text('Идёт сканирование');
            $rootScope.pendingRequests += 1;
            getImage(scanUrl, function (image_b64) {
                $scope.currentFile.file.binary_b64 = null;
                $scope.currentFile.file.image = new Image();
                $scope.currentFile.file.mime = 'image/jpeg';
                $scope.currentFile.file.type = 'image';
                $scope.currentFile.file.image.src = image_b64;
                $scope.generateFileName();

                $rootScope.pendingRequests -= 1;
                loaderTextElem.text(oldText);
            });
        };
        $scope.save_image = function () {
            var validity = $scope.validate();
            if (!validity.result) {
                NotificationService.notify(null,
                    'Невозможно сохранить документ: ' + validity.message,
                    'danger');
                return;
            }
            $http.post(WMConfig.url.api_patient_file_attach, {
                client_id: client_id,
                file_attach: makeAttachFileDocumentInfo($scope.file_attach)
            }).success(function (data) {
                $scope.file_attach.load(data.result.cfa);
                NotificationService.notify(
                    200,
                    'Сохранено',
                    'success'
                );
            }).error(function () {
                alert('Ошибка сохранения');
            });
        };
        $scope.deleteFileAttach = function () {
            MessageBox.question(
                'Удаление документа',
                'Документ будет удален. Продолжить?'
            ).then(function () {
                $http.delete(WMConfig.url.api_patient_file_attach, {
                    params: {
                        cfa_id: $scope.file_attach.id
                    }
                }).success(function () {
                    $scope.$close('deleted');
                }).error(function () {
                    alert('Ошибка удаления');
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
                    $http.delete(WMConfig.url.api_patient_file_attach, {
                        params: {
                            file_meta_id: $scope.currentFile.id
                        }
                    }).success(function () {
                        $scope.file_attach.file_document.removePage($scope.selected.currentPage);
                        setCurPage();
                        NotificationService.notify(
                            200,
                            'Страница удалена',
                            'success'
                        );
                    }).error(function () {
                        alert('Ошибка удаления');
                    });
                });
            } else {
                $scope.file_attach.file_document.removePage($scope.selected.currentPage);
                setCurPage();
            }
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
                    $scope.currentFile.file.load(data.result, true);
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

        $scope.getTitleText = function () {
            var text = '{0}{, |1|}'.formatNonEmpty(
                $scope.file_attach.id ? 'Просмотр копии документа' : 'Добавление копии документа', (
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
                    cfa_id: cfa_id,
                    idx: idx
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
