/* http://github.com/mindmup/bootstrap-wysiwyg */
/*global jQuery, $, FileReader*/
/*jslint browser:true*/
'use strict';
angular.module('WebMis20.directives.wysiwyg', ['WebMis20.directives.goodies'])
.service('ThesaurusService', ['$http', '$q', 'FlatTree','WMConfig', function ($http, $q, FlatTree, WMConfig) {
    var cache = {};
    function convert(item) {
        return {
            id: item[0],
            parent_id: item[1],
            code: item[2],
            name: item[3],
            template: item[4]
        }
    }
    function makeObject(item) {
        if (!item) {
            return {
                id: null,
                parent_id: null,
                code: null,
                name: null,
                template: ''
            }
        } else {
            return item
        }
    }
    var Thesaurus = function (data) {
        var list = data.map(convert);
        var tree = new FlatTree('parent_id').set_array(list).filter().render(makeObject);
        this.tree = tree.root;
        this.dict = tree.idDict;
    };
    this.getThesaurus = function (code) {
        var defer = $q.defer();
        if (cache.hasOwnProperty(code)) {
            defer.resolve(cache[code]);
        } else {
            $http.get(WMConfig.url.nemesis.rbThesaurus_root + code)
            .success(function (data) {
                var result = cache[code] = new Thesaurus(data.result);
                defer.resolve(result)
            });
        }
        return defer.promise;
    }
}])
.service('AsideThesaurus', ['ThesaurusService', '$modal', '$templateCache', function (ThesaurusService, $modal, $templateCache) {
    // Рендер вида
    function buildList(list) {
        return '<ul>{0}</ul>'.format(list.map(buildNode).join(''));
    }
    function buildNode(node) {
        if (!node.children.length) {
            return '<li><a ng-click="select(\'{0}\')"><i class="fa fa-angle-double-right">&nbsp;</i>{1}</a></li>'.format(node.id, node.name);
        } else {
            return '<li><a ng-click="select(\'{0}\')"><i class="fa fa-angle-double-right">&nbsp;</i>{1}</a>{2}</li>'.format(node.id, node.name, buildList(node.children));
        }
    }
    function buildView(thesaurus_tree_nodes) {
        var tree = buildList(thesaurus_tree_nodes),
            editor = '<wysiwyg ng-model="model.text" get-wysiwyg-api="getWysiwygApi(api)" />';
        return editor + '<hr>' + '<div class="thesaurus-tree ui-treeview">' + tree + '</div>';
    }
    this.openThesaurus = function (code, editor_model, close_promise) {
        var myAside;
        return ThesaurusService.getThesaurus(code).then(function (thesaurus) {
            myAside = $modal.open({
                windowTemplateUrl: '/WebMis20/aside-thesaurus.html',
                template: $templateCache.get('/WebMis20/aside-thesaurus/tree.html').format(buildView(thesaurus.tree.children)),
                backdrop: true,
                controller: function ($scope) {
                    function renderThesaurusTemplate(node_id) {
                        var node = thesaurus.dict[node_id];
                        if (!node) { return ''; }
                        var template = node.template;
                        if (template.indexOf('%s') > -1) {
                            return template.replace('%s', renderThesaurusTemplate(node.parent_id));
                        } else {
                            return template;
                        }
                    }
                    $scope.model = {
                        text: editor_model
                    };
                    $scope.getWysiwygApi = function (api) {
                        $scope.wysiwygApi = api;
                    };
                    $scope.select = function (node_id) {
                        var text = renderThesaurusTemplate(node_id).replace('%n', '\n') + ' ';
                        $scope.wysiwygApi.insertText(text);
                    };
                    $scope.$on('$destroy', function () {
                        close_promise.resolve($scope.model.text);
                    });
                }
            });

            return close_promise.promise.then(function (edited_text) {
                return edited_text;
            });
        });
    };
}])
.directive('wysiwygOpenThesaurus', ['AsideThesaurus', '$q', function (AsideThesaurus, $q) {
    return {
        restrict: 'A',
        link: function (scope, element, attributes) {
            var jqElement = $(element);
            jqElement.click(function (event) {
                event.preventDefault();
                var code = scope.$eval(attributes.wysiwygOpenThesaurus);
                var close = $q.defer();
                AsideThesaurus.openThesaurus(
                    code, scope.$model.$modelValue, close
                ).then(function (result) {
                    scope.replaceContent(result);
                });
            })
        }
    }
}])
.directive('wysiwyg', ['$q', '$compile', '$templateCache', 'HtmlCleaner',
        function ($q, $compile, $templateCache, HtmlCleaner) {
    var regexp_cleanHtml = new RegExp('(<br>|<div><br><\/div>|&nbsp;)', 'g'),
        regexp_emptyHtml = new RegExp('(<br>|\\s|<div><br><\/div>|&nbsp;)', 'g');
    var readFileIntoDataUrl = function (fileInfo) {
        var loader = $q.defer(),
            fReader = new FileReader();
        fReader.onload = function (e) {
            loader.resolve(e.target.result);
        };
        fReader.onerror = loader.reject;
        fReader.onprogress = loader.notify;
        fReader.readAsDataURL(fileInfo);
        return loader.promise;
    };
    var cleanHtml = function (html) {
        return html && html.replace(regexp_cleanHtml, '');
    },
        isEmptyHtml = function (html) {
            return !Boolean(html && html.replace(regexp_emptyHtml, ''));
        };
    var defaults = {
        toolbarSelector: '[data-role=editor-toolbar]',
        commandRole: 'edit',
        activeToolbarClass: 'btn-info',
        selectionMarker: 'edit-focus-marker',
        selectionColor: 'darkgrey',
        dragAndDropImages: true,
        fileUploadError: function (reason, detail) {
            console.log("File upload error", reason, detail);
        }
    };
    return {
        restrict: 'E',
        scope: {
            contenteditable: '=',
            userOptions: '=',
            thesaurusCode: '@',
            complainsCode: '@',
            getWysiwygApi: '&?'
        },
        require: '^ngModel',
        link: function (scope, element, attributes, ngModel) {
            scope.$model = ngModel;
            var toolbar = $($templateCache.get('/WebMis20/wysiwyg-toolbar.html'));
            var editor = $('<div style="padding: 10px; overflow: auto; min-height: 40px; max-height: 500px" class="wysiwyg-panel long-words" contenteditable="[[contenteditable]]"></div>');
            if (attributes.id) {
                editor.attr('id', attributes.id);
            }
            var replace = $('<div class="panel panel-default" style="padding: 0"></div>');
            toolbar.find('.dropdown-menu input')
                .click(function() {return false;})
                .change(function () {$(this).parent('.dropdown-menu').siblings('.dropdown-toggle').dropdown('toggle');})
                .keydown('esc', function () {this.value='';$(this).change();});
            var selectedRange,
                options,
                toolbarBtnSelector,
                updateToolbar = function () {
                    if (options.activeToolbarClass) {
                        toolbar.find(toolbarBtnSelector).each(function () {
                            var command = $(this).data(options.commandRole);
                            if (document.queryCommandState(command)) {
                                $(this).addClass(options.activeToolbarClass);
                            } else {
                                $(this).removeClass(options.activeToolbarClass);
                            }
                        });
                    }
                },
                execCommand = function (commandWithArgs, valueArg) {
                    var commandArr = commandWithArgs.split(' '),
                        command = commandArr.shift(),
                        args = commandArr.join(' ') + (valueArg || '');
                    document.execCommand(command, 0, args);
                    updateToolbar();
                },
                getCurrentRange = function () {
                    var sel = window.getSelection();
                    if (sel.getRangeAt && sel.rangeCount) {
                        return sel.getRangeAt(0);
                    }
                },
                saveSelection = function () {
                    selectedRange = getCurrentRange();
                },
                restoreSelection = function () {
                    var selection = window.getSelection();
                    if (selectedRange) {
                        try {
                            selection.removeAllRanges();
                        } catch (ex) {
                            document.body.createTextRange().select();
                            document.selection.empty();
                        }
                        selection.addRange(selectedRange);
                    }
                },
                insertFiles = function (files) {
                    editor.focus();
                    $.each(files, function (idx, fileInfo) {
                        if (/^image\//.test(fileInfo.type)) {
                            readFileIntoDataUrl(fileInfo).then(
                                function (dataUrl) {execCommand('insertimage', dataUrl);},
                                function (e) {options.fileUploadError("file-reader", e);}
                            );
                        } else {
                            options.fileUploadError("unsupported-file-type", fileInfo.type);
                        }
                    });
                },
                markSelection = function (input, color) {
                    restoreSelection();
                    if (document.queryCommandSupported('hiliteColor')) {
                        document.execCommand('hiliteColor', 0, color || 'transparent');
                    }
                    saveSelection();
                    input.data(options.selectionMarker, color);
                },
                bindToolbar = function (toolbar, options) {
                    toolbar.find(toolbarBtnSelector).click(function () {
                        restoreSelection();
                        editor.focus();
                        execCommand($(this).data(options.commandRole));
                        saveSelection();
                    });
                    toolbar.find('[data-toggle=dropdown]').click(restoreSelection);

                    toolbar.find('input[type=text][data-{0}]'.format(options.commandRole)).on('webkitspeechchange change', function () {
                        var newValue = this.value;
                        /* ugly but prevents fake double-calls due to selection restoration */
                        this.value = '';
                        restoreSelection();
                        if (newValue) {
                            editor.focus();
                            execCommand($(this).data(options.commandRole), newValue);
                        }
                        saveSelection();
                    }).on('focus', function () {
                        var input = $(this);
                        if (!input.data(options.selectionMarker)) {
                            markSelection(input, options.selectionColor);
                            input.focus();
                        }
                    }).on('blur', function () {
                        var input = $(this);
                        if (input.data(options.selectionMarker)) {
                            markSelection(input, false);
                        }
                    });
                    toolbar.find('input[type=file][data-{0}]'.format(options.commandRole)).change(function () {
                        restoreSelection();
                        if (this.type === 'file' && this.files && this.files.length > 0) {
                            insertFiles(this.files);
                        }
                        saveSelection();
                        this.value = '';
                    });
                },
                initFileDrops = function () {
                    editor.on('dragenter dragover', false)
                        .on('drop', function (e) {
                            var dataTransfer = e.originalEvent.dataTransfer;
                            e.stopPropagation();
                            e.preventDefault();
                            if (dataTransfer && dataTransfer.files && dataTransfer.files.length > 0) {
                                insertFiles(dataTransfer.files);
                            }
                        });
                };
            options = angular.extend({}, defaults, scope.userOptions);
            toolbarBtnSelector = 'a[data-{0}],button[data-{0}],input[type=button][data-{0}]'.format(options.commandRole);
            if (options.dragAndDropImages) {
                initFileDrops();
            }
            bindToolbar(toolbar, options);

            var updateModelLock = false; // Этот костыль предотвращает нежелательный апдейт вида данными модели
            function updateModel() {
                updateModelLock = true;
                var view_value = !isEmptyHtml(editor.html())
                    ? cleanHtml(editor.html())
                    : '';
                ngModel.$setViewValue(view_value);
                ngModel.$render();
            }

            editor.on('mouseup keyup mouseout', function () {
                scope.$apply(function () {
                    if (editor.is(':focus')) {
                        saveSelection();
                        updateToolbar();
                        updateModel();
                    }
                });
            });

            editor.on('blur', function () {
                scope.$apply(function () {
                    updateModel();
                });
            });

            function handlePaste (e) {
                // http://stackoverflow.com/a/6804718
                var types, pastedData, savedContent;
                var _editor = editor[0];

                // Browsers that support the 'text/html' type in the Clipboard API (Chrome, Firefox 22+)
                var clipboardData = e && (e.originalEvent || e).clipboardData;
                if (clipboardData && clipboardData.types && clipboardData.getData) {
                    // Check for 'text/html' in types list. DOMStringList bit is needed by FF.
                    // We cannot fall back to 'text/plain' as Safari/Edge don't advertise HTML
                    // data even if it is available
                    types = clipboardData.types;
                    if (((types instanceof DOMStringList) && types.contains("text/html")) ||
                        (types.indexOf && types.indexOf('text/html') !== -1)) {

                        // Extract data and pass it to callback
                        pastedData = clipboardData.getData('text/html');
                        processPaste(pastedData);

                        // Stop the data from actually being pasted
                        e.stopPropagation();
                        e.preventDefault();
                        return false;
                    }
                }

                // Everything else: Move existing element contents to a DocumentFragment for safekeeping
                savedContent = document.createDocumentFragment();
                while (_editor.childNodes.length > 0) {
                    savedContent.appendChild(_editor.childNodes[0]);
                }
                // Then wait for browser to paste content into it and cleanup
                waitForPastedData(_editor, savedContent);
                return true;
            }
            function waitForPastedData (elem, savedContent) {
                // If data has been processes by browser, process it
                if (elem.childNodes && elem.childNodes.length > 0) {
                    // Retrieve pasted content via innerHTML
                    // (Alternatively loop through elem.childNodes or elem.getElementsByTagName here)
                    var pastedData = elem.innerHTML;
                    // Restore saved content
                    elem.innerHTML = "";
                    elem.appendChild(savedContent);
                    processPaste(pastedData);
                }
                // Else wait 20ms and try again
                else {
                    setTimeout(function () {
                        waitForPastedData(elem, savedContent)
                    }, 20);
                }
            }
            function processPaste (pastedData) {
                var cleaned = HtmlCleaner.clean(pastedData);
                editor.focus();
                restoreSelection();
                execCommand('insertHTML', cleaned);
                saveSelection();
                updateModel();
            }

            editor.on('paste', handlePaste);

            scope.insertText = function (myValue) {
                editor.focus();
                restoreSelection();
                execCommand('insertText', myValue);
                saveSelection();
                updateModel();
            };
            scope.replaceContent = function (text) {
                editor.focus();
                document.execCommand('selectAll');
                execCommand('insertHTML', text);
                saveSelection();
                updateModel();
            };
            if (angular.isDefined(scope.getWysiwygApi)) {
                scope.getWysiwygApi({
                    api: {
                        insertText: scope.insertText
                    }
                });
            }

            scope.$watch('$model.$modelValue', function (n, o) {
                if (updateModelLock) {
                    updateModelLock = false
                } else {
                    editor.html(n);
                }
                return n;
            });

            scope.$on('$destroy', function () {
                editor.unbind();
                toolbar.find().each(function () {$(this).unbind()})
            });

            $(window).bind('touchend', function (e) {
                var isInside = (editor.is(e.target) || editor.has(e.target).length > 0),
                    currentRange = getCurrentRange(),
                    clear = currentRange && (currentRange.startContainer === currentRange.endContainer && currentRange.startOffset === currentRange.endOffset);
                if (!clear || isInside) {
                    saveSelection();
                    updateToolbar();
                }
            });

            replace.append(toolbar);
            replace.append(editor);
            $(element).replaceWith(replace);
            $compile(replace)(scope);
        }
    };
}])
.service('HtmlCleaner', [function () {
    this.clean = function (val) {
        return cleanPaste(val);
    };

    // from https://github.com/yabwe/medium-editor : src/js/extensions/paste.js : version 5.22.1
    var _replacements = [
        // Remove anything but the contents within the BODY element
        [new RegExp(/^[\s\S]*<body[^>]*>\s*|\s*<\/body[^>]*>[\s\S]*$/g), ''],

        // cleanup comments added by Chrome when pasting html
        [new RegExp(/<!--StartFragment-->|<!--EndFragment-->/g), ''],

        // Trailing BR elements
        [new RegExp(/<br>$/i), ''],

        // replace two bogus tags that begin pastes from google docs
        [new RegExp(/<[^>]*docs-internal-guid[^>]*>/gi), ''],
        [new RegExp(/<\/b>(<br[^>]*>)?$/gi), ''],

         // un-html spaces and newlines inserted by OS X
        [new RegExp(/<span class="Apple-converted-space">\s*<\/span>/gi), ' '],
        [new RegExp(/<span class="Apple-converted-space"><span style=""><\/span><\/span>/gi), ' '],
        [new RegExp(/<br class="Apple-interchange-newline">/g), '<br>'],

        // replace google docs italics+bold with a span to be replaced once the html is inserted
        [new RegExp(/<span[^>]*(font-style:italic;font-weight:(bold|700)|font-weight:(bold|700);font-style:italic)[^>]*>/gi), '<span class="replace-with italic bold">'],

        // replace google docs italics with a span to be replaced once the html is inserted
        [new RegExp(/<span[^>]*font-style:italic[^>]*>/gi), '<span class="replace-with italic">'],

        //[replace google docs bolds with a span to be replaced once the html is inserted
        [new RegExp(/<span[^>]*font-weight:(bold|700)[^>]*>/gi), '<span class="replace-with bold">'],

         // replace manually entered b/i/a tags with real ones
        [new RegExp(/&lt;(\/?)(i|b|a)&gt;/gi), '<$1$2>'],

         // replace manually a tags with real ones, converting smart-quotes from google docs
        [new RegExp(/&lt;a(?:(?!href).)+href=(?:&quot;|&rdquo;|&ldquo;|"|“|”)(((?!&quot;|&rdquo;|&ldquo;|"|“|”).)*)(?:&quot;|&rdquo;|&ldquo;|"|“|”)(?:(?!&gt;).)*&gt;/gi), '<a href="$1">'],

        // Newlines between paragraphs in html have no syntactic value,
        // but then have a tendency to accidentally become additional paragraphs down the line
        [new RegExp(/<\/p>\n+/gi), '</p>'],
        [new RegExp(/\n+<p/gi), '<p'],

        // Microsoft Word makes these odd tags, like <o:p></o:p>
        [new RegExp(/<\/?o:[a-z]*>/gi), ''],

        // Microsoft Word adds some special elements around list items
        [new RegExp(/<!\[if !supportLists\]>(((?!<!).)*)<!\[endif]\>/gi), '$1']
    ];
    var cleanPaste = function (text) {
        var i, elList, tmp, workEl,
            multiline = /<p|<br|<div/.test(text),
            replacements = _replacements;
        var html_text;

        for (i = 0; i < replacements.length; i += 1) {
            text = text.replace(replacements[i][0], replacements[i][1]);
        }

        if (multiline) {
            // create a temporary div to cleanup block elements
            tmp = document.createElement('div');

            // double br's aren't converted to p tags, but we want paragraphs.
            tmp.innerHTML = '<p>' + text.split('<br><br>').join('</p><p>') + '</p>';

            // block element cleanup
            elList = tmp.querySelectorAll('a,p,div,br');
            for (i = 0; i < elList.length; i += 1) {
                workEl = elList[i];

                // Microsoft Word replaces some spaces with newlines.
                // While newlines between block elements are meaningless, newlines within
                // elements are sometimes actually spaces.
                workEl.innerHTML = workEl.innerHTML.replace(/\n/gi, ' ');

                switch (workEl.nodeName.toLowerCase()) {
                    case 'p':
                    case 'div':
                        filterCommonBlocks(workEl);
                        break;
                    //case 'br':
                    //    this.filterLineBreak(workEl);
                    //    break;
                }
            }
            html_text = tmp.innerHTML;
        } else {
            html_text = text;
        }
        html_text = html_text.replace(/&nbsp;/g, ' ');
        return html_text;
    };
    var filterCommonBlocks = function (el) {
        if (/^\s*$/.test(el.textContent) && el.parentNode) {
            el.parentNode.removeChild(el);
        }
    };
}])
.run(['$templateCache', function ($templateCache) {
    var fonts = ['Serif', 'Sans', 'Arial', 'Arial Black', 'Courier', 'Courier New', 'Comic Sans MS', 'Helvetica', 'Impact', 'Lucida Grande', 'Lucida Sans', 'Tahoma', 'Times', 'Times New Roman', 'Verdana'];
    var makeFontSelector = function (fontName) {
        return '<li><a data-edit="fontName {0}" style="font-family:\'{0}\'">{0}</a></li>'.format(fontName)
    };
    $templateCache.put('/WebMis20/wysiwyg-toolbar.html',
        '<div class="btn-toolbar" data-role="editor-toolbar" data-target="#editor">\
            <div class="btn-group">\
                <a class="btn" wysiwyg-open-thesaurus="thesaurusCode" ng-if="thesaurusCode"><i class="fa">Тезаурус <i class="fa fa-list-alt"></i></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn dropdown-toggle" data-toggle="dropdown" title="Font"><i class="fa fa-font"></i><b class="caret"></b></a>\
                <ul class="dropdown-menu">{0}</ul>\
            </div>\
            <div class="btn-group">\
                <a class="btn dropdown-toggle" data-toggle="dropdown" title="Font Size"><i class="fa fa-text-height"></i>&nbsp;<b class="caret"></b></a>\
                <ul class="dropdown-menu">\
                    <li><a data-edit="fontSize 4"><font size="4">Крупный</font></a></li>\
                    <li><a data-edit="fontSize 3"><font size="3">Нормальный</font></a></li>\
                    <li><a data-edit="fontSize 2"><font size="2">Мелкий</font></a></li>\
                </ul>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="bold" title="Bold (Ctrl/Cmd+B)"><i class="fa fa-bold"></i></a>\
                <a class="btn" data-edit="italic" title="Italic (Ctrl/Cmd+I)"><i class="fa fa-italic"></i></a>\
                <a class="btn" data-edit="strikethrough" title="Strikethrough"><i class="fa fa-strikethrough"></i></a>\
                <a class="btn" data-edit="underline" title="Underline (Ctrl/Cmd+U)"><i class="fa fa-underline"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="insertunorderedlist" title="Bullet list"><i class="fa fa-list-ul"></i></a>\
                <a class="btn" data-edit="insertorderedlist" title="Number list"><i class="fa fa-list-ol"></i></a>\
                <a class="btn" data-edit="indent" title="Indent (Tab)"><i class="fa fa-indent"></i></a>\
                <a class="btn" data-edit="outdent" title="Reduce indent (Shift+Tab)"><i class="fa fa-outdent"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="justifyleft" title="Align Left (Ctrl/Cmd+L)"><i class="fa fa-align-left"></i></a>\
                <a class="btn" data-edit="justifycenter" title="Center (Ctrl/Cmd+E)"><i class="fa fa-align-center"></i></a>\
                <a class="btn" data-edit="justifyright" title="Align Right (Ctrl/Cmd+R)"><i class="fa fa-align-right"></i></a>\
                <a class="btn" data-edit="justifyfull" title="Justify (Ctrl/Cmd+J)"><i class="fa fa-align-justify"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn dropdown-toggle" data-toggle="dropdown" title="Hyperlink"><i class="fa fa-link"></i></a>\
                <div class="dropdown-menu input-append">\
                    <input class="form-control" placeholder="URL" type="text" data-edit="createLink"/>\
                    <button class="btn" type="button">Add</button>\
                </div>\
                <a class="btn" data-edit="unlink" title="Remove Hyperlink"><i class="fa fa-cut"></i></a>\
            </div>\
            <div class="btn-group">\
                <a class="btn" data-edit="undo" title="Undo (Ctrl/Cmd+Z)"><i class="fa fa-undo"></i></a>\
                <a class="btn" data-edit="redo" title="Redo (Ctrl/Cmd+Y)"><i class="fa fa-repeat"></i></a>\
            </div>\
        </div>'.format(fonts.map(makeFontSelector).join('')));
    $templateCache.put('/WebMis20/aside-thesaurus/tree.html',
'<div class="aside-header">\
    <button type="button" class="close" ng-click="$dismiss()">&times;</button>\
    <h4 class="aside-title">Тезаурус</h4>\
</div>\
<div class="aside-body full-height modal-scrollable">{0}</div>'
    );
    $templateCache.put('/WebMis20/aside-thesaurus/custom.html',
"<div tabindex=\"-1\" role=\"dialog\" class=\"modal fade\" ng-class=\"{in: animate}\" ng-style=\"{'z-index': 1050 + index*10, display: 'block'}\" ng-click=\"close($event)\">\
    <div class=\"modal-dialog\" ng-class=\"{'modal-sm': size == 'sm', 'modal-lg': size == 'lg'}\"><div class=\"modal-content\" ng-transclude></div></div>\n\
</div>"
    );
    $templateCache.put('/WebMis20/aside-thesaurus.html',
'<div tabindex="-1" role="dialog" class="modal fade full-height" ng-class="{in: animate}" ng-style="{\'z-index\': 1050 + index*10, display: \'block\'}" ng-click="close($event)">\
    <div class="aside right full-height">\
        <div class="aside-dialog full-height">\
            <div class="aside-content full-height">\
                <div class="full-height" ng-transclude></div>\
            </div>\
        </div>\
    </div>\
</div>'
    );
}])
;


