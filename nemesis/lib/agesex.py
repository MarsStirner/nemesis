# -*- coding: utf-8 -*-
import re
import datetime

__author__ = 'mmalkov'


class AgeSex(object):
    # TODO: Здесь надо парсить age и прочую ерунду. Пока так.
    def __init__(self, obj):
        self.obj = obj

    def __json__(self):
        result = {}
        if hasattr(self.obj, 'age'):
            result['age'] = self.obj.age
        if hasattr(self.obj, 'sex'):
            result['sex'] = self.obj.sex
        return result


def recordAcceptableEx(clientSex, clientAge, recordSex, recordAge):
    """
    @type clientSex: str | unicode
    @type clientAge: tuple
    @type recordSex: str | unicode
    @type recordAge: str | unicode | list
    """
    return not (recordSex and recordSex != clientSex) and \
           not (clientAge and not checkAgeSelector(parseAgeSelector(recordAge), clientAge))


def checkAgeSelector((begUnit, begCount, endUnit, endCount), ageTuple):
    """
    @type begUnit: int
    @type begCount: int
    @type endUnit: int
    @type endCount: int
    @type ageTuple: tuple
    """
    return not (begUnit != 0 and ageTuple[begUnit - 1] < begCount or endUnit != 0 and ageTuple[endUnit - 1] > endCount)


def parseAgeSelector(val):
    """
    @type val: str | unicode | list
    """
    if isinstance(val, list):
        return val
    try:
        return parseAgeSelectorInt(val)
    except:
        return 0, 0, 0, 0


def parseAgeSelectorInt(val):
    u""" selector syntax: "{NNN{д|н|м|г}-{MMM{д|н|м|г}}" -
    с NNN дней/недель/месяцев/лет по MMM дней/недель/месяцев/лет;
    пустая нижняя или верхняя граница - нет ограничения снизу или сверху
    @type val: str | unicode
    @rtype: tuple
    """
    parts = val.split('-')
    if len(parts) == 2:
        begUnit, begCount = parseAgeSelectorPart(parts[0].strip())
        endUnit, endCount = parseAgeSelectorPart(parts[1].strip())
        return begUnit, begCount, endUnit, endCount
    elif len(parts) == 1:
        if parts[0]:
            begUnit, begCount = parseAgeSelectorPart(parts[0].strip())
        else:
            begUnit, begCount = 0, 0
        return begUnit, begCount, 0, 0
    raise ValueError(u'Недопустимый синтаксис селектора возраста "%s"' % val)


AgeSelectorUnits = u'днмг'
re_age_selector = re.compile(r'^(\d+)\s*([^\d\s]+)$')


def parseAgeSelectorPart(val):
    if val:
        matchObject = re_age_selector.match(val)
        if matchObject:
            strCount, strUnit = matchObject.groups()
            count = int(strCount) if strCount else 0
            unit = AgeSelectorUnits.find(strUnit.lower()) + 1
            if unit == 0:
                raise ValueError(u'Неизвестная единица измерения "%s"' % strUnit)
            return unit, count
        raise ValueError(u'Недопустимый синтаксис части селектора возраста "%s"' % val)
    return 0, 0


def calcAgeTuple(birthDay, today):
    d = calcAgeInDays(birthDay, today)
    if d >= 0:
        return (
            d,
            d / 7,
            calcAgeInMonths(birthDay, today),
            calcAgeInYears(birthDay, today)
        )
    return None


def calcAgeInMonths(birthDay, today):
    assert isinstance(birthDay, datetime.date)
    assert isinstance(today, datetime.date)

    bYear = birthDay.year
    bMonth = birthDay.month
    bDay = birthDay.day

    tYear = today.year
    tMonth = today.month
    tDay = today.day

    result = (tYear - bYear) * 12 + (tMonth - bMonth)
    if bDay > tDay:
        result -= 1
    return result


def calcAgeInYears(birthDay, today):
    assert isinstance(birthDay, datetime.date)
    assert isinstance(today, datetime.date)

    bYear = birthDay.year
    bMonth = birthDay.month
    bDay = birthDay.day

    tYear = today.year
    tMonth = today.month
    tDay = today.day

    result = tYear - bYear
    if bMonth > tMonth or (bMonth == tMonth and bDay > tDay):
        result -= 1
    return result


def calcAgeInDays(birthDay, today):
    assert isinstance(birthDay, datetime.date)
    assert isinstance(today, datetime.date)
    return (today - birthDay).days


def agreeNumberAndWord(num, words):
    u"""
        Согласовать число и слово:
        num - число, слово = (один, два, много)
        agreeNumberAndWord(12, (u'год', u'года', u'лет'))
    """
    if num < 0:
        num = -num
    if (num/10) % 10 != 1:
        if num % 10 == 1:
            return words[0]
        elif 1 < num % 10 < 5:
            return words[1]
    return words[-1]


def formatYears(years):
    return '%d %s' % (years, agreeNumberAndWord(years, (u'год', u'года', u'лет')))


def formatMonths(months):
    return '%d %s' % (months, agreeNumberAndWord(months, (u'месяц', u'месяца', u'месяцев')))


def formatWeeks(weeks):
    return '%d %s' % (weeks, agreeNumberAndWord(weeks, (u'неделя', u'недели', u'недель')))


def formatDays(days):
    return '%d %s' % (days, agreeNumberAndWord(days, (u'день', u'дня', u'дней')))


def formatYearsMonths(years, months):
    if years == 0:
        return formatMonths(months)
    elif months == 0:
        return formatYears(years)
    else:
        return formatYears(years) + ' ' + formatMonths(months)


def formatMonthsWeeks(months, weeks):
    if months == 0:
        return formatWeeks(weeks)
    elif weeks == 0:
        return formatMonths(months)
    else:
        return formatMonths(months) + ' ' + formatWeeks(weeks)