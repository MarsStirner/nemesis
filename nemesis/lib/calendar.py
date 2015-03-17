# -*- coding: utf-8 -*-


class Calendar(object):
    u"""Список всех отклонений календаря"""
    def __init__(self):
        self.holiday_list = []
        self.changeday_list = []

    def clear(self):
        self.holiday_list = []
        self.changeday_list = []

    def load(self):
        pass

    def getCount(self):
        return len(self.holiday_list) + len(self.changeday_list)

    def getHolidayCount(self):
        return len(self.holiday_list)

    def getChangedayCount(self):
        return len(self.changeday_list)

    def getHolidayList(self):
        return self.holiday_list

    def getChangedayList(self):
        return self.changeday_list

    def getList(self):
        return self.holiday_list + self.changeday_list


calendar = Calendar()
calendar.load()