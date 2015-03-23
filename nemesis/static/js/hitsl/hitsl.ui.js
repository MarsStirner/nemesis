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
.service('FileEditModal', ['$modal', '$http', 'WMConfig', 'MessageBox', function ($modal, $http, WMConfig, MessageBox) {
    function _getTemplate(openMode, attachType) {
        var template = '\
<div class="modal-header">\
    <h3 class="modal-title" ng-bind="getTitleText()"></h3>\
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
                    <button type="button" class="btn btn-sm btn-danger pull-right" ng-click="deletePage()">\
                        <span class="glyphicon glyphicon-minus" title="Удалить страницу"></span>\
                    </button>\
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
        <div id="addFileBlock" ng-show="addFileBlockVisible()">{0}</div>\
        <div id="metaInfoBlock" class="modal-scrollable-block2">{1}</div>\
    </div>\
    <div class="col-md-8">\
        <div id="image_editor" ng-show="imageSelected()">\
            <div class="modal-scrollable-block">\
                <wm-image-editor id="image_editor" model-image="currentFile.file.image" read-only="checkImageRO()"></wm-image-editor>\
            </div>\
        </div>\
        <div ng-show="notImageSelected()"><span>Предпросмотр недоступен. Выбранный файл не является изображением.</span></div>\
    </div>\
    </div>\
</div>\
<div class="modal-footer">\
    <button type="button" class="btn btn-danger pull-left" ng-click="deleteFileAttach()" ng-if="btnDelDocumentVisible()"\
        title="Удалить документ целиком">Удалить документ\
    </button>\
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
</ng-form>';

        template = template.format(
            addFileTemplate,
            attachType === 'client' ? (metaInfoTemplate) : ''
        );
        return template;
    }

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
        this.files.filter(function (page, index) {
            return index > idx;
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
                fm_copy = {
                    meta: {
                        id: fileMeta.id,
                        name: fileMeta.name,
                        idx: fileMeta.idx
                    }
                };
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
            }
            cfa_copy.file_document.files[key] = fm_copy;
        });

        return cfa_copy;
    }

    function unspace(text) {
        return text.replace(/ /g, '_');
    }

    var FileEditController = function ($scope, file_attach, client_id, client, pageNumber) {
        $scope.client = client;

        $scope.mode = 'scanning';
        $scope.device_list = [];
        $scope.selected = {
            device: {},
            currentPage: pageNumber
        };
        $scope.file_attach = file_attach;
        $scope.currentFile = $scope.file_attach.file_document.getFile($scope.selected.currentPage);

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
            }).success(function (data) {
                $scope.file_attach.load(data.result.cfa);
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
        $scope.checkImageRO = function () {
            return $scope.currentFile.id;
        };
        $scope.btnDelDocumentVisible = function () {
            return $scope.file_attach.id;
        };
        $scope.addFileBlockVisible = function () {
            return !$scope.currentFile.id;
        };
        $scope.imageSelected = function () {
            return $scope.currentFile.isImage();
        };
        $scope.notImageSelected = function () {
            return $scope.currentFile.isNotImage();
        };
        $scope.correctFileSelected = function () {
            return true || ($scope.file.type === 'image' ? // TODO: провенить, что на всех страницах добавлен файл
                $scope.imageSelected() :
                $scope.notImageSelected());
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
                    }
                }
            });
            return instance.result;
        },
        open: function (cfa_id, params) {
            var idx = params.idx || 0,
                file_attach;
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