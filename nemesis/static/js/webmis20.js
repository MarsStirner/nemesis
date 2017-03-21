/**
 * Created by mmalkov on 10.02.14.
 */
"use strict";
var WebMis20 = angular.module('WebMis20', [
    'hitsl.core',
    'hitsl.ui',
    'WebMis20.services',
    'WebMis20.services.dialogs',
    'WebMis20.services.models',
    'WebMis20.directives',
    'WebMis20.directives.personTree',
    'WebMis20.directives.wysiwyg',
    'WebMis20.directives.ActionTypeTree',
    'WebMis20.directives.goodies',
    'WebMis20.controllers',
    'WebMis20.validators'
])
.filter('asDateTime', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM.YYYY HH:mm');
    }
})
.filter('asDate', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM.YYYY');
    }
})
.filter('asShortDate', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('DD.MM');
    }
})
.filter('asTime', function ($filter) {
    return function (data) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format('HH:mm');
    }
})
.filter('asMomentFormat', function ($filter) {
    return function (data, format) {
        if (!data) return data;
        var result = moment(data);
        if (!result.isValid()) return data;
        return result.format(format);
    }
})
.filter('asAutoFormat', function ($filter) {
    return function (data, key) {
        var value = data[key];
        if (!value) return value;
        var result = moment(value);
        if (key.endswith('Date')) {
            return result.format('DD.MM.YYYY');
        } else if (key.endswith('DateTime')) {
            return result.format('DD.MM.YYYY HH:mm');
        } else if (key.endswith('Time')) {
            return result.format('HH:mm');
        } else {
            if (result.isValid()) {
                return result.toISOString();
            } else {
                return value;
            }
        }
    }
})
.filter('danet', function () {
    return function (data) {
        if (data === true) return 'да';
        if (data === false) return 'нет';
        return data;
    }
})
.filter('danetIfNull', ['$filter', function ($filter) {
    return function (data) {
        var data = $filter('danet')(data);
        if (data === null) return 'нет'; 
        return data;
    }
}])
.filter('format', function () {
    return function (data, format) {
        if (data instanceof Array) {
            return data.map(function (item) {
                return format.replace(/{\s*?(.+?)\s*?}/g, function (str, match) {
                    return item.hasOwnProperty(match) ? item[match] : match
                })
            })
        } else if (data instanceof Object) {
            return format.replace(/{(.+?)}/g, function (str, match) {
                return data.hasOwnProperty(match) ? data[match] : match
            })
        } else {
            return data
        }
    }
})
.filter('escape', function () {
        return function (data) {
            if (data instanceof Array) {
                return data.map(function (item) {
                    if (typeof item === 'string' || item instanceof String) {
                        return item.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;');
                    } else {
                        return item;
                    }
                })
            } else if (typeof data === 'string' || data instanceof String) {
                return data.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;');
            } else {
                return data;
            }
        }
    })
.filter('join', function ($filter) {
    return function (data, char) {
        if (data instanceof Array)
            return data.join(char);
        return data
    }
})
.filter('split', function ($filter) {
    return function (data, splitChar) {
        if (typeof data === "string")
            return data.split(splitChar);
        return data
    }
})
.filter('applyFilter', function ($filter) {
    return function (array, filter_name) {
        var filter;
        if (_.isFunction(filter_name)) {
            filter = filter_name;
        } else if (typeof filter_name === 'string') {
            filter = $filter(filter_name);
        } else {
            return array;
        }
        if (_.isArray(array)) {
            return _.map(array, filter);
        } else {
            return array;
        }
    }
})
.filter('attribute', function ($filter) {
    return function (array, attribute) {
        var value = arguments[2];
        var func = arguments[3];
        var attrs = attribute.split('.');
        var item_attribute;
        if (func === undefined) {
            item_attribute = function (item) {
                return safe_traverse(item, attrs)
            }
        } else if (typeof(func) == 'function') {
            item_attribute = function (item) {
                return func(safe_traverse(item, attrs))
            }
        } else {
            throw 'Ну что это за ерунда?'
        }
        if (array instanceof Array) {
            if (value === undefined) {
                return array.filter(function (item) {
                    return Boolean(item_attribute(item));
                })
            } else if (value instanceof Array) {
                return array.filter(function (item) {
                    return value.has(item_attribute(item));
                })
            } else {
                return array.filter(function (item) {
                    return item_attribute(item) == value;
                })
            }
        } else {
            return array;
        }
    }
})
.filter('pluck', function () {
    return function (array, attribute) {
        return _.pluck(array, attribute)
    }
})
.filter('count', function () {
    return function (array) {
        if (_.isArray(array)) {
            return array.length
        } else {
            return 0;
        }
    }
})
.filter('negate', function () {
    return function (arg) {
        return !arg
    }
})
.filter('contains', function () {
    return function (array, against) {
        if (_.isArray(array)) {
            if (_.isArray(against)) {
                return _.any(against, _.partial(_.contains, array))
            } else {
                return _.contains(array, against)
            }
        } else {
            return false;
        }
    }
}).filter('intersects', function () {
    return function (array, against) {
        return _.intersection(array, against).length > 0
    }
})
.filter('deep_filter', function () {
    return function (array, object) {
        var arg_chain = _.map(object, function (check_value, key) {
            return [key.split('.'), check_value]
        });
        var filter_function = function (item) {
            return _.every(arg_chain, function (arg) {
                return safe_traverse(item, arg[0]) == arg[1];
            });
        };
        return _.filter(array, filter_function);
    }
})
.filter('event_type_filter', function() {
    return function(items, props) {
        var out = [];
        if (angular.isArray(items) && props) {
            items.forEach(function(item) {
                var itemMatches = false;
                var keys = Object.keys(props);
                for (var i = 0; i < keys.length; i++) {
                    var prop = keys[i];
                    var prop_id = props[prop]['id'];
                    if (item.id === prop_id) {
                        itemMatches = true;
                        break;
                    }
                }
                if (itemMatches) {
                    out.push(item);
                }
            });
        } else {
            // Let the output be the input untouched
            out = items;
        }
        return out;
    }
})
.filter('highlight', function() {
    return function (input, query) {
        if (input) {
            var query_array = query.replace(/\s+/g, ' ').split(' ');
            input = input.toString();
            for (var i = 0; i < query_array.length; i++) {
                input = input.replace(new RegExp('('+ query_array[i] + ')', 'gi'), '<mark>$1</mark>');
            }
        }
        return input;
    }
})
.filter('flt_not_deleted', function() {
    return function(items) {
        var out = [];
        if (items && items instanceof Array) {
            items.forEach(function(item){
                if (!item.hasOwnProperty('deleted') ||
                    (item.hasOwnProperty('deleted') && item.deleted === 0)) {
                    out.push(item);
                }
            });
        }
        return out;
    };
})
.filter('rb_result_filter', function() {
    return function(items, event_purpose_id) {
        var out = [];
        if(items){
            items.forEach(function(item){
                if (item.eventPurpose_id == event_purpose_id){
                    out.push(item);
                }
            })
        }
        return out;
    };
})
.filter('formatSnils', function () {
    return function (snils) {
        return snils && snils.length === 11 ?
            [snils.substr(0, 3), '-',
             snils.substr(3, 3), '-',
             snils.substr(6, 3), ' ', snils.substr(9, 2)].join('') :
            '';
    }
})
.filter('trustHtml', function ($sce) {
    return $sce.trustAsHtml;
})
.filter('organisation_filter', function() {
    return function(items) {
        var out = [];
        if(items) {
            items.forEach(function(item){
                if (!item.hasOwnProperty('is_lpu') ||
                    (item.hasOwnProperty('is_lpu') && item.is_lpu)) {
                    out.push(item);
                }
            });
        }
        return out;
    };
})
.filter('moneyCut', ['$filter', function ($filter) {
    return function (value) {
        return /\.00$/.test(value) ? value.substring(0, value.length - 3) : value;
    }
}])
.filter('flattenNested', function () {
    function traverse (item, subAttrName, out, level, idx, rootIdx) {
        if (!item.hasOwnProperty('ui_attrs')) item.ui_attrs = {};

        var is_expandable = Boolean(item[subAttrName].length);
        angular.extend(
            item.ui_attrs,
            {
                level: level,
                is_expandable: is_expandable,
                expanded: item.ui_attrs.expanded !== undefined ? item.ui_attrs.expanded : true,
                visible: item.ui_attrs.visible !== undefined ? item.ui_attrs.visible : true,
                idx: idx,
                root_idx: rootIdx
            }
        );
        out.push(item);
        if (is_expandable) {
            for (var i = 0; i < item[subAttrName].length; i++) {
                traverse(item[subAttrName][i], subAttrName, out, level + 1, idx, idx);
            }
        }
    }
    return function (item_list, subAttrName) {
        var flatten = [],
            curLevel = 0,
            idx = -1;

        if (!item_list) return item_list;

        for (var i = 0; i < item_list.length; i++) {
            curLevel = 0;
            idx += 1;
            var item = item_list[i];
            traverse(item, subAttrName, flatten, curLevel, idx, idx);
        }
        return flatten;
    }
})
.filter('collapse_diagnoses', [function () {
    return function (diag_list, kind) {
        var types = arguments[2];
        if (_.isUndefined(types)) {
            return _.filter(diag_list, function (diagnosis) {
                return _.any(diagnosis.diagnosis_types, function (value, key) {
                    return value.code == kind;
                });
            })
        } else {
            return _.filter(diag_list, function (diagnosis) {
                return _.any(diagnosis.diagnosis_types, function (value, key) {
                    return value.code == kind && [].has.apply(types, [key]);
                });
            })
        }
    }
}])
// Services
.factory('RefBook', ['$http', '$rootScope', function ($http, $rootScope) {
    var RefBook = function (name) {
        this.name = name;
        this.objects = [];
        this.load();
    };
    RefBook.prototype.load = function () {
        var t = this;
        this.loading = $http.get(rb_root + this.name)
        .success(function (data) {
            t.objects = data.result;
            $rootScope.$broadcast('rb_load_success_'+ t.name, {
                text: 'Загружен справочник ' + t.name
            });
        })
        .error(function (data, status) {
            $rootScope.$broadcast('load_error', {
                text: 'Ошибка при загрузке справочника ' + t.name,
                code: status,
                data: data,
                type: 'danger'
            });
        });
        return this;
    };
    RefBook.prototype.get = function (id) {
        var i = this.objects.length;
        while (i--) {
            if (this.objects[i].id == id) return this.objects[i];
        }
        return null;
    };
    RefBook.prototype.get_by_code = function (code) {
        var i = this.objects.length;
        while (i--) {
            if (this.objects[i].code == code) return this.objects[i];
        }
        return null;
    };
    RefBook.prototype.get_by_code_async = function (code) {
        var self = this;
        return this.loading.then(function () {
            return self.get_by_code(code);
        });
    };
    return RefBook;
}])
.service('RefBookService', ['RefBook', function (RefBook) {
    var cache = {};
    this.get = function (name) {
        if (cache.hasOwnProperty(name)) {
            return cache[name];
        } else {
            return cache[name] = new RefBook(name);
        }
    }
}])
.service('Settings', ['RefBookService', '$rootScope', function(RefBookService, $rootScope) {
    var self = this;
    self.rb_dict = {};
    self.rb = RefBookService.get('Setting');
    if (self.rb.objects.length) {
        self.init();
    }
    $rootScope.$on('rb_load_success_Setting', function() {
        self.init();
    });

    self.init = function() {
        var d = this.rb && this.rb.objects || [];
        for (var i=0; i < d.length; i++) {
            this.rb_dict[d[i].path] = d[i].value;
        }
    };

    self.get_string = function(val, def) {
        if ($.isEmptyObject(this.rb_dict)) return null;
        var default_val = '';
        if (arguments.length > 1) {
            default_val = def;
        }
        return this.rb_dict[val] || default_val;
    };
}])
.factory('PrintingService', ['$window', '$http', '$rootScope', '$timeout', 'CurrentUser', 'WMConfig',
        function ($window, $http, $rootScope, $timeout, CurrentUser, WMConfig) {
    var PrintingService = function (context_type) {
        if (arguments.length >= 3) {
            this.target = arguments[2]
        } else {
            this.target = '_blank'
        }
        this.context_type = context_type;
        this.context = null;
        this.templates = [];
    };
    PrintingService.prototype.set_context = function (context) {
        if (context === this.context) return;
        this.context = context;
        var t = this;
        return $http.get(url_print_templates + context + '.json')
        .success(function (data) {
            t.templates = data.result.sort(function (left, right) {
                return (left.code < right.code) ? -1 : (left.code > right.code ? 1 : 0)
            });
            t.loaded = true;
        })
        .error(function (data, status) {
            if (data === '' && status === 0) {
                t.not_available = true;
            }
            t.loaded = false;
        });
    };
    PrintingService.prototype.is_available = function () {
        return this.loaded !== undefined ? Boolean(this.context) && !this.not_available : true;
    };
    PrintingService.prototype.is_loaded = function () {
        return Boolean(this.context) && this.loaded;
    };
    PrintingService.prototype.print_template = function(template_data_list, separated) { // [ {template_id, context}, ... ]
        var self = this;
        var send_data = {
            separate: separated,
            documents: template_data_list.map(function (item) {
                return {
                    id: item.template_id,
                    context_type: self.context_type,
                    context: angular.extend(
                        {}, item.context, {
                            'currentOrgStructure': "",
                            'currentOrganisation': WMConfig.local_config.default_org_id,
                            'currentPerson': CurrentUser.get_main_user().id
                        }
                    )
                }
            }
        )};
        return $http.post(url_print_template, send_data)
        .success(function (data) {
            var w = $window.open();
            w.document.open();
            w.document.write(data);
            w.document.close();
            // timeout to fix chrome (36) behaviour - empty print preview https://code.google.com/p/chromium/issues/detail?id=396667
            $timeout(w.print, 300);
        })
        .error(function (data, status) {
            var result = data.result,
                info = (data === '' && status === 0) ?
                    {
                        text: 'Ошибка соединения с сервером печати',
                        code: status,
                        data: null,
                        type: 'danger'
                    } :
                    {
                        text: result.name,
                        code: status,
                        data: result.data,
                        type: 'danger'
                    };
            $rootScope.$broadcast('printing_error', info);
        });
    };
    return PrintingService;
}])
.factory('JasperPrintingService', ['$window', '$http', '$rootScope', '$timeout', 'CurrentUser', 'WMConfig',
        function ($window, $http, $rootScope, $timeout, CurrentUser, WMConfig) {
    var JasperPrintingService = function (context_type) {
        if (arguments.length >= 3) {
            this.target = arguments[2]
        } else {
            this.target = '_blank'
        }
        this.context_type = context_type;
        this.context = null;
        this.templates = [];
    };
    JasperPrintingService.prototype.set_context = function (context) {
        if (context === this.context) return;
        this.context = context;
        var t = this;
        return $http.get(url_jr_print_templates + '?folder=' + context)
        .success(function (data) {
            t.templates = data.result;
            t.loaded = true;
        })
        .error(function (data, status) {
            if (data === '' && status === 0) {
                t.not_available = true;
            }
            t.loaded = false;
        });
    };
    JasperPrintingService.prototype.set_template_meta = function (template, callback) {
        if (template === this.template) return callback();
        this.template = template;
        var t = this;
        return $http.get(url_jr_print_template_meta + '?template_id=' + template.id)
        .success(function (data) {
            t.template.meta = data.result;
            return callback();
        })
        .error(function (data, status) {
            if (data === '' && status === 0) {
                t.not_available = true;
            }
        });
    };
    JasperPrintingService.prototype.is_available = function () {
        return this.loaded !== undefined ? Boolean(this.context) && !this.not_available : true;
    };
    JasperPrintingService.prototype.is_loaded = function () {
        return Boolean(this.context) && this.loaded;
    };
    JasperPrintingService.prototype.file_get = function (verb, url, data, target, on_error) {
        var form = document.createElement("form");
        form.id = 'myForm';
        form.action = url;
        form.method = verb;
        form.target = target || "_blank";
        if (data) {
            var json = angular.toJson(data);
            var input = document.createElement("textarea");
            input.name = 'json';
            input.value = json;
            form.appendChild(input);
        }
        form.style.display = 'none';
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        // todo: найти способ отправки post запроса с параметрами, ответ
        // todo: которого по выборку пользователя открывается в соответствующем
        // todo: типу файла приложении или сохраняется на диск и при этом иметь
        // todo: возможность реагировать на успех и ошибку ответа
        // ajax_form.submit(function(){
        //     $.ajax({
        //         url: ajax_form.attr('action'),
        //         type: 'post',
        //         data: ajax_form.serialize(),
        //         dataType: 'text',
        //         success: function (res) {
        //             var w = $window.open();
        //         },
        //         error: function (res, err_code) {
        //         }
        //     });
        //     return false;
        // });
        // ajax_form.submit();

        // вместо promise
        return {then: function(onsuccess, onerror) {
            return onsuccess();
        }}
    };
    JasperPrintingService.prototype.print_template = function(template_data_list, separated, response_type) { // [ {template_id, context}, ... ]
        var self = this;
        var send_data = {
            response_type: response_type,
            separate: separated,
            documents: template_data_list.map(function (item) {
                return {
                    id: item.template_id,
                    code: item.code,
                    context_type: self.context_type,
                    context: angular.extend(
                        {}, item.context, {
                            'currentOrgStructure': "",
                            'currentOrganisation': WMConfig.local_config.default_org_id,
                            'currentPerson': CurrentUser.get_main_user().id
                        }
                    )
                }
            }
        )};
        return self.file_get('POST', url_jr_print_template, send_data, undefined, function (data, status) {
            var result = data.result,
            info = (data === '' && status === 0) ?
                {
                    text: 'Ошибка соединения с сервером печати',
                    code: status,
                    data: null,
                    type: 'danger'
                } :
                {
                    text: result.name,
                    code: status,
                    data: result.data,
                    type: 'danger'
                };
            $rootScope.$broadcast('printing_error', info);
        });
    };
    return JasperPrintingService;
}])
.factory('EventType', ['RefBook', 'AgeSex', function (RefBook, AgeSex) {
    var EventType = function () {
        RefBook.call(this, 'EventType');
    };

    EventType.prototype = new RefBook('EventType');
    EventType.prototype.initialize = function (client) {
        var self = this;
        return self.loading.then(function () {
            self.objects = self.objects.filter(function (item) {
                return AgeSex.sex_acceptable(client.info, item.sex) &&
                    AgeSex.age_acceptable(client.info, item.age_tuple);
            });
        });
    };
    EventType.prototype.get_finances_by_rt = function(rt_id) {
        return this.get_filtered_by_rt(rt_id).map(function(el) {
            return el.finance;
        }).filter(function(el) {
            return el !== undefined && el != null;
        }).sort(function (a, b) {
            return a.id - b.id;
        });
    };
    EventType.prototype.get_filtered_by_rt = function(rt_id) {
        return this.objects.filter(function(el) {
            return el.request_type && el.request_type.id === rt_id;
        });
    };
    EventType.prototype.get_filtered_by_rtf = function(rt_id, fin_id) {
        return this.objects.filter(function(el) {
            return el.request_type && el.finance &&
                el.request_type.id === rt_id && el.finance.id === fin_id;
        });
    };
    EventType.prototype.get_available_et = function (event_type) {
        return this.objects.some(function (o) {
            return angular.equals(o, event_type);
        }) ? event_type : undefined;
    };
    return EventType;
}])
.factory('SelectAll', function () {
    var SelectAll = function (source) {
        this._source = source;
        this._selected = source.clone();
    };
    SelectAll.prototype.setSource = function (source) {
        this._source = source;
        this._selected = source.clone();
    };
    SelectAll.prototype.selected = function () {
        var item = arguments[0];
        if (item === undefined) {
            return this._selected;
        } else {
            return this._selected.has(item);
        }
    };
    SelectAll.prototype.selectAll = function () {
        this._selected = this._source.clone();
    };
    SelectAll.prototype.selectNone = function () {
        this._selected = [];
    };
    SelectAll.prototype.select = function (item) {
        var checked = arguments[1];
        if (checked === false) {
            this._selected.remove(item);
        } else {
            if (!this._selected.has(item)) {
                this._selected.push(item);
            }
        }
    };
    SelectAll.prototype.toggle = function (item) {
        var index = this._selected.indexOf(item);
        if (index === -1) {
            this._selected.push(item);
        } else {
            this._selected.splice(index, 1);
        }
    };
    SelectAll.prototype.toggle_all = function () {
        if (this.all()) {
            this.selectNone()
        } else {
            this.selectAll()
        }
    };
    SelectAll.prototype.all = function () {
        return this._source.length == this._selected.length;
    };
    return SelectAll
})
.directive('wmCheckbox', ['$compile', function ($compile) {
    return {
        restrict: 'E',
        scope: {
            selectAll: '=',
            key: '='
        },
        link: function (scope, element, attributes) {
            // Создаём элементы
            var inputElement = $('<input type="checkbox" class="rmargin10"></input>');
            var replace = $('<label></label>');
            // Формируем элеменент для замены
            replace.append(inputElement);
            replace.append(element.html());

            // 2-way binding
            function select() {
                scope.$apply(angular.bind(this, function () {
                    scope.selectAll.select(scope.key, this.checked);
                }));
//                scope.$root.$digest(); // Это может негативно влиять на производительность, но оно нужно.
            }
            scope.$watch('selectAll._selected', function (n, o) {
                inputElement[0].checked = scope.selectAll.selected(scope.key);
                return n;
            });

            $(element).replaceWith(replace); // Заменяем исходный элемент
            inputElement.change(select); // Цепляем хендл. Не могу сказать, как jQuery поступит при дестрое элемента
            $compile(replace)(scope); // Компилируем
        }
    }
}])
// end services
.directive('uiMkb', function ($timeout, RefBookService) {
    return {
        restrict: 'E',
        require: '?ngModel',
        template:
            '<a ng-disabled="ngDisabled" style="overflow:hidden;" class="btn btn-default btn-block [[ngRequired && !$model.$modelValue ? \'error-border\' : \'\']]" ng-click="to_show()">' +
                '<span class="mkb-button col-md-12">[[ $model.$modelValue.code ]] [[$model.$modelValue.name]]</span>' +
                '<span class="caret" ng-if="!$model.$modelValue"></span>' +
            '</a>' +
            '<div class="well well-sm popupable" ng-show="shown" ng-mouseleave="to_hide_delay()" ng-mouseenter="to_hide_cancel()">' +
                '<input type="text" ng-model="query" class="form-control" />' +
                '<table class="table table-condensed table-clickable">' +
                    '<thead><tr><th>Код</th><th>Наименование</th></tr></thead>' +
                    '<tbody>' +
                        '<tr ng-repeat="row in $RefBook.objects | filter:query | limitTo:100" ng-click="onClick(row)"' +
                            'ng-class="{\'bg-primary\': is_selected(row.code)}">' +
                            '<td ng-bind="row.code"></td><td ng-bind="row.name"></td>' +
                        '</tr>' +
                    '</tbody>' +
                '</table>' +
            '</div>',
        scope: {
            ngRequired: '=',
            ngDisabled: '='
        },
        link: function (scope, element, attributes, ngModel) {
            scope.$model = ngModel;
            scope.$RefBook = RefBookService.get('MKB');
            var div_elem = $(element[0].childNodes[1]);
            var btn_elem = $(element[0].childNodes[0]);
            var timeout = null;
            scope.shown = false;
            scope.query='';
            scope.to_show = function () {
                if (ngModel.$modelValue) {
                    scope.query = ngModel.$modelValue.code;
                } else {
                    scope.query = '';
                }
                var btn_width = btn_elem.width();
                div_elem.width(Math.max(btn_width, 500));
                scope.shown = true;
            };
            scope.to_hide_delay = function () {
                if (!timeout) {
                    timeout = $timeout(to_hide, 600)
                }
            };
            scope.to_hide_cancel = function () {
                if (timeout) {
                    $timeout.cancel(timeout);
                    timeout = null;
                }
            };
            scope.onClick = function (row) {
                ngModel.$setViewValue(row);
                to_hide();
            };
            scope.search = function (actual, expected) {
                return actual.split(' ').filter(function (part) {
                    return part.startswith(expected)
                }).length > 0;
            };
            scope.is_selected = function (mkb_code) {
                return scope.$model.$modelValue && scope.$model.$modelValue.code === mkb_code;
            };
            function to_hide () {
                timeout = null;
                scope.shown = false;
            }
        }
    };
})
.directive('uiScheduleTicket', ['$compile', function ($compile) {
    return {
        restrict: 'A',
        scope: {
            day: '=day',
            showName: '=showName',
            prevTicket: '=prevTicket',
            ticket: '=uiScheduleTicket'
        },
        link: function (scope, element, attributes) {
            var elem = $(element);
            var now = moment();
            elem.addClass('btn btn-block text-left');
            scope.$watch('ticket.status', function (n, o) {
                if (!scope.ticket) {
                    if (scope.prevTicket) {
                        if(moment(scope.day.date) < now.startOf('day')){
                            elem.addClass('disabled');
                        }
                        scope.ticket = {
                            'schedule_id': scope.prevTicket.schedule_id,
                            'reserve_type': scope.prevTicket.reserve_type,
                            'attendance_type': {'code': 'extra'}
                        }
                    } else {
                        elem.addClass('disabled');
                        elem.html('&nbsp');
                        return
                    }
                }
                var text = '';
                switch (scope.ticket.attendance_type.code) {
                    case 'planned':
                        if(scope.ticket.appointment_permitted == '1') {
                            text = moment(scope.ticket.begDateTime).format('HH:mm');
                        } else {
                            text = scope.ticket.reserve_type && scope.ticket.reserve_type.name || 'Undefined';
                        }
                        break;
                    case 'CITO': text = 'CITO'; break;
                    case 'extra': text = 'Сверх плана'; break;
                }
                if (n == 'busy') {
                    elem.removeClass('btn-success btn-warning btn-gray disabled');
                    elem.addClass('btn-primary');
                    if (scope.showName) {
                        text += ' - ' + scope.ticket.client;
                    }
                } else {
                    elem.removeClass('btn-danger');
                    switch (scope.ticket.attendance_type.code) {
                        case 'planned': elem.addClass('btn-success'); break;
                        case 'CITO': elem.addClass('btn-warning'); break;
                        case 'extra': elem.addClass('btn-gray'); break;
                    }
                    scope.ticket.disabled = scope.day.roa || scope.ticket.appointment_permitted == '0' ||
                        scope.ticket.begDateTime && (moment(scope.ticket.begDateTime) < now) ||
                                                     moment(scope.day.date) < now.startOf('day');
                    if (scope.ticket.disabled) {
                        elem.addClass('disabled');
                    }
                }
                elem.text(text);
            });

        }
    };
}])
.directive('wmPageHeaderButtonBox', function () {
    return {
        restrict: 'C',
        link: function (scope, element, attributes) {
            var $element = $(element);
            $element.addClass('pull-right');
            if (window.opener) {
                $element.append('<button class="btn btn-sm btn-danger" onclick="window.opener.focus();window.close();" title="Закрыть"><span class="glyphicon glyphicon-remove"></span></button>');
            }
        }
    }
})
.directive("freeInputSelect", [
    '$timeout', function($timeout) {
      return {
        restrict: "A",
        scope: {
          items: '=',
          disabled: '=ngDisabled',
          freetext: '@',
          builder: '=',
          "class": '@'
        },
        require: '?ngModel',
        replace: true,
        template: function(el) {
          var itemTpl, template;
          itemTpl = el.html();
          return template = "<div class='fs-select fs-widget-root'>\n  <div ng-hide=\"active\" class=\"fs-select-sel\" ng-class=\"{'btn-group': item}\">\n      <a class=\"btn btn-default fs-select-active\"\n         ng-class='{\"btn-danger\": invalid}'\n         href=\"javascript:void(0)\"\n         ng-click=\"active = true\"\n         ng-disabled=\"disabled\">\n           <span ng-show='item'>" + itemTpl + "</span>\n           <span ng-hide='item'>none</span>\n      </a>\n      <button type=\"button\"\n              class=\"btn btn-default fs-select-clear-btn\"\n              aria-hidden=\"true\"\n              ng-show='item'\n              ng-disabled=\"disabled\"\n              ng-click='unselectItem()'>&times;</button>\n    </div>\n  <div class=\"open\" ng-show=\"active\">\n    <input class=\"form-control\"\n           fs-input\n           fs-focus-when='active'\n           fs-blur-when='!active'\n           fs-on-focus='active = true'\n           fs-on-blur='onBlur()'\n           fs-hold-focus\n           fs-down='move(1)'\n           fs-up='move(-1)'\n           fs-pg-up='move(-11)'\n           fs-pg-down='move(11)'\n           fs-enter='onEnter($event)'\n           fs-esc='active = false'\n           type=\"text\"\n           placeholder='Search'\n           ng-model=\"search\"\n           fs-null-form />\n\n    <div ng-if=\"active && dropdownItems.length > 0\">\n      <div fs-list items=\"dropdownItems\">\n       " + itemTpl + "\n      </div>\n    </div>\n  </div>\n</div>";
        },
        controller: function($scope, $element, $attrs, $filter, $timeout) {
          var updateDropdown;
          $scope.active = false;
          if ($attrs.freetext != null) {
            $scope.dynamicItems = function() {
              if ($scope.search) {
                var free_input = $scope.builder($scope.search);
                return [free_input];
              } else {
                return [];
              }
            };
          } else {
            $scope.dynamicItems = function() {
              return [];
            };
          }
          updateDropdown = function() {
            return $scope.dropdownItems = $filter('filter')($scope.items, $scope.search).concat($scope.dynamicItems());
          };
          $scope.$watch('active', function(q) {
            return updateDropdown();
          });
          $scope.$watch('search', function(q) {
            return updateDropdown();
          });
          $scope.selectItem = function(item) {
            $scope.item = item;
            $scope.search = "";
            return $scope.active = false;
          };
          $scope.unselectItem = function(item) {
            return $scope.item = null;
          };
          $scope.onBlur = function() {
            return $timeout(function() {
              $scope.active = false;
              return $scope.search = '';
            }, 0, true);
          };
          $scope.move = function(d) {
            return $scope.listInterface.move && $scope.listInterface.move(d);
          };
          $scope.onEnter = function(event) {
            if ($scope.dropdownItems.length > 0) {
              return $scope.selectItem($scope.listInterface.selectedItem);
            } else {
              return $scope.selectItem(null);
            }
          };
          return $scope.listInterface = {
            onSelect: function(selectedItem) {
              return $scope.selectItem(selectedItem);
            },
            move: function() {
              return console.log("not-implemented listInterface.move() function");
            }
          };
        },
        link: function(scope, element, attrs, ngModelCtrl, transcludeFn) {
          if (ngModelCtrl) {
            scope.$watch('item', function(newValue, oldValue) {
              if (newValue !== oldValue) {
                return ngModelCtrl.$setViewValue(scope.item);
              }
            });
            return ngModelCtrl.$render = function() {
              return scope.item = ngModelCtrl.$viewValue;
            };
          }
        }
      };
    }
  ])
.run(['IdleTimer', function (IdleTimer) {
    IdleTimer.start();
}]);

angular.module('WebMis20.services.models', []);

