/**
 * Created by mmalkov on 13.02.15.
 */

// AUX

var aux = {
    getQueryParams: function (qs) {
        qs = qs.split("+").join(" ");

        var params = {}, tokens,
            re = /[?&]?([^=]+)=([^&]*)/g;

        while (tokens = re.exec(qs)) {
            params[decodeURIComponent(tokens[1])] = decodeURIComponent(tokens[2]);
        }

        return params;
    },
    range: function (start, end) {
        if (arguments.length < 2) {
            end = start;
            start = 0;
        }
        if (start >= end) {
            return [];
        }
        var res = [],
            cur = end - start;
        end--;
        while (cur--) {
            res[cur] = end--;
        }
        return res;
    },
    moment: moment,
    months: [
        {name: 'Январь', value: 0},
        {name: 'Февраль', value: 1},
        {name: 'Март', value: 2},
        {name: 'Апрель', value: 3},
        {name: 'Май', value: 4},
        {name: 'Июнь', value: 5},
        {name: 'Июль', value: 6},
        {name: 'Август', value: 7},
        {name: 'Сентябрь', value: 8},
        {name: 'Октябрь', value: 9},
        {name: 'Ноябрь', value: 10},
        {name: 'Декабрь', value: 11}
    ],
    func_in: function (against) {
        return function (item) {
            return against.indexOf(item) !== -1;
        }
    },
    func_not_in: function (against) {
        return function (item) {
            return against.indexOf(item) === -1;
        }
    },
    any_in: function (what, where) {
        for (var i = what.length-1; i >= 0; i--) {
            for (var j = where.length-1; j >= 0; j--) {
                if (what[i] == where[j]) {
                    return true;
                }
            }
        }
        return false;
    },
    safe_date: function (val) {
        if (!val) {
            return null;
        }
        var date = moment(val);
        return date.isValid() ? date.toDate() : null;
    },
    format_date: function (val) {
        if (!val) {
            return null;
        }
        var date = moment(val);
        return date.isValid() ? date.format('YYYY-MM-DD') : null;
    },
    make_tree: function (array, masterField) {
        /**
         * @param array: Исходный массив данных
         * @param masterField: Наименование поля указателя на родительский элемент
         * @param idField: наименование поля идентификатора. (default: 'id')
         * @param childrenField: наименование поля со списком детей (default: 'children')
         * @param make_object: Функция, возвращающая элемент дерева по элементу массива function(item)
         * @param filter_function: Функция, фильтрующая элементы массива function(item, lookup_dict)
         * @rtype {*}
         */
        var idField = arguments[2] || 'id',
            childrenField = arguments[3] || 'children',
            filter_function = arguments[5] || function () {return true;},
            make_object = arguments[4] || function (item) {
                    if (item === null) {
                        var result = {};
                        result[masterField] = null;
                        result[idField] = 'root';
                        result[childrenField] = [];
                        return result
                    }
                    return item
                };
        var idDict = new dict({
            root: null
        });
        var masterDict = new dict({
            root: []
        });
        array.forEach(function (item) {
            var id = item[idField];
            idDict[id] = item;
        });
        var filtered = array.filter(function (item) {
            return filter_function(item, idDict)
        });
        filtered.forEach(function (item) {
            do {
                var master = item[masterField] || 'root';
                if (masterDict[master] === undefined) masterDict[master] = [];
                if (masterDict[master].has(item[idField])) return;
                masterDict[master].push(item[idField]);
                item = idDict[master];
            } while (item)
        });
        function recurse(id) {
            var childrenObject = {};
            var children_list = masterDict[id] || [];
            childrenObject[childrenField] = children_list.map(recurse);
            return angular.extend({}, make_object(idDict[id]), childrenObject);
        }
        return {
            root: recurse('root'),
            idDict: idDict,
            masterDict: masterDict
        };
    }
};

// Convenience

function safe_traverse(object, attrs) {
    var o = object,
        attr,
        default_val = arguments[2];
    for (var i = 0; i < attrs.length; ++i) {
        attr = attrs[i];
        o = o[attr];
        if (o === undefined || (o === null && i < attrs.length - 1)) {
            return default_val;
        }
    }
    return o;
}

function indexOf(array, elem) {
  var index, _i, _ref;
  for (index = _i = 0, _ref = array.length - 1; 0 <= _ref ? _i <= _ref : _i >= _ref; index = 0 <= _ref ? ++_i : --_i) {
    if (angular.equals(array[index], elem)) {
      return index;
    }
  }
  return -1;
}
if (!HTMLElement.prototype.hasOwnProperty('getOffsetRect')) {
    HTMLElement.prototype.getOffsetRect = function () {
        // (1)
        var box = this.getBoundingClientRect();
        // (2)
        var body = document.body;
        var docElem = document.documentElement;
        // (3)
        var scrollTop = window.pageYOffset || docElem.scrollTop || body.scrollTop;
        var scrollLeft = window.pageXOffset || docElem.scrollLeft || body.scrollLeft;
        // (4)
        var clientTop = docElem.clientTop || body.clientTop || 0;
        var clientLeft = docElem.clientLeft || body.clientLeft || 0;
        // (5)
        var top  = box.top +  scrollTop - clientTop;
        var left = box.left + scrollLeft - clientLeft;
        return { top: Math.round(top), left: Math.round(left) }
    }
}

// String.prototype

if (!String.prototype.format) {
    String.prototype.format = function() {
        var args = arguments;
        return this.replace(/{(\d+)}/g, function(match, number) {
            return typeof args[number] != 'undefined'
                ? args[number]
                : match
                ;
        });
    };
}
if (!String.prototype.formatNonEmpty) {
    String.prototype.formatNonEmpty = function() {
        var args = arguments;
        return this.replace(/{([\w\u0400-\u04FF\s\.,</>()]*)\|?(\d+)\|?([\w\u0400-\u04FF\s\.,</>()]*)}/g, function(match, prefix, number, suffix) {
            return typeof args[number] != 'undefined'
                ? (args[number] ? (prefix + args[number] + suffix): '')
                : ''
                ;
        });
    };
}
if (!String.prototype.startswith) {
    String.prototype.startswith = function (prefix) {
        return this.indexOf(prefix) === 0;
    }
}
if (!String.prototype.endswith) {
    String.prototype.endswith = function (suffix) {
        return this.indexOf(suffix, this.length - suffix.length) !== -1;
    }
}
if (!String.prototype.contains) {
    String.prototype.contains = function (infix) {
        return this.indexOf(infix) !== -1;
    }
}

// Array.prototype

if (!Array.prototype.clone) {
    Array.prototype.clone = function () {
        var b = [];
        var i = this.length;
        while (i--) {b[i] = this[i]}
        return b;
    }
}
if (!Array.prototype.has) {
    Array.prototype.has = function (item) {
        return this.indexOf(item) !== -1
    }
}
if (!Array.prototype.remove) {
    Array.prototype.remove = function (item) {
        var index = this.indexOf(item);
        if (index !== -1) {
            return this.splice(index, 1)
        } else {
            if (arguments[1]) {
                throw Error('Array doesn\'t have element')
            } else {
                return undefined
            }
        }
    }
}
if (!Array.range) {
    Array.range = function (num) {
        return Array.apply(null, new Array(num)).map(function(_, i) {return i;})
    }
}

// Underscore

_.mixin({
    findCmp: function (array, item, cmpFunction) {
        return _.find(array, _.partial(cmpFunction, item));
    },
    distinct: function (array) {
        var attr = arguments[1];
        var cmp;
        if (_.isUndefined(attr)) {
            cmp = function (a, b) {return a == b;}
        } else {
            cmp = function (a, b) {return a[attr] == b[attr];}
        }
        var result = [];
        _.each(array, function (item) {
            if (_.isUndefined(_.findCmp(result, item, cmp))) result.push(item);
        });
        return result;
    },
    deepCopy: function (obj) {
        if (_.isArray(obj)) {
            return obj.map(_.deepCopy);
        } else if (_.isObject(obj)) {
            return _.mapObject(obj, _.deepCopy);
        } else {
            return obj;
        }
    }
});