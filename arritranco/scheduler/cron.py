#! /usr/bin/env python
# -*- coding: iso-8859-1 -*
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02110-1301, USA.
#
# Crontab-like string parse. Inspired on crontab.py of the
# gnome-schedule-1.1.0 package.

import re
import datetime
from calendar import monthrange

class SimpleCrontabEntry(object):
    """Contrab-like parser.

    Only deals with the first 5 fields of a normal crontab
    entry."""

    def __init__(self, entry, expiration = 0):
        self.__setup_timespec()
        self.set_value(entry)
        self.set_expiration(expiration)

    def set_expiration(self, val):
        self.expiration = datetime.timedelta(minutes=val)

    def set_value(self, entry):
        self.data = entry
        fields = re.findall("\S+", self.data)
        if len(fields) != 5 :
            raise ValueError("Crontab entry needs 5 fields")
        self.fields = {
            "minute" : fields[0],
            "hour"   : fields[1],
            "day"    : fields[2],
            "month"  : fields[3],
            "weekday": fields[4],
            }
        if not self._is_valid():
            raise ValueError("Bad Entry: %s" % entry)

    #### HERE BEGINS THE CODE BORROWED FROM gnome-schedule ###
    def __setup_timespec(self):
        
        self.special = {
                "@reboot"  : '',
                "@hourly"  : '0 * * * *',
                "@daily"   : '0 0 * * *',
                "@weekly"  : '0 0 * * 0',
                "@monthly" : '0 0 1 * *',
                "@yearly"  : '0 0 1 1 *'
                }

        self.timeranges = { 
                "minute"   : range(0,60), 
                "hour"     : range(0,24),
                "day"      : range(1,32),
                "month"    : range(1,13),
                "weekday"  : range(0,8)
                }

        self.timenames = {
                "minute"   : "Minute",
                "hour"     : "Hour",
                "day"      : "Day of Month",
                "month"    : "Month",
                "weekday"  : "Weekday"
                }

        self.monthnames = {
                "1"        : "Jan",
                "2"        : "Feb",
                "3"        : "Mar",
                "4"        : "Apr",
                "5"        : "May",
                "6"        : "Jun",
                "7"        : "Jul",
                "8"        : "Aug",
                "9"        : "Sep",
                "10"       : "Oct",
                "11"       : "Nov",
                "12"       : "Dec"
                }

        self.downames = {
                "0"        : "Sun",
                "1"        : "Mon",
                "2"        : "Tue",
                "3"        : "Wed",
                "4"        : "Thu",
                "5"        : "Fri",
                "6"        : "Sat",
                "7"        : "Sun"
                }

    def checkfield (self, expr, type):
        """Verifies format of Crontab timefields

        Checks a single Crontab time expression.
        At first possibly contained alias names will be replaced by their
        corresponding numbers. After that every asterisk will be replaced by
        a "first to last" expression. Then the expression will be splitted
        into the komma separated subexpressions.

        Each subexpression will run through: 
        1. Check for stepwidth in range (if it has one)
        2. Check for validness of range-expression (if it is one)
        3. If it is no range: Check for simple numeric
        4. If it is numeric: Check if it's in range

        If one of this checks failed, an exception is raised. Otherwise it will
        do nothing. Therefore this function should be used with 
        a try/except construct.  
        """

        timerange = self.timeranges[type]

        # Replace alias names only if no leading and following alphanumeric and 
        # no leading slash is present. Otherwise terms like "JanJan" or 
        # "1Feb" would give a valid check. Values after a slash are stepwidths
        # and shouldn't have an alias.
        if type == "month": alias = self.monthnames.copy()
        elif type == "weekday": alias = self.downames.copy()
        else: alias = None
        if alias != None:
            while True:
                try: key,value = alias.popitem()
                except KeyError: break
                expr = re.sub("(?<!\w|/)" + value + "(?!\w)", key, expr)

        expr = expr.replace("*", str(min(timerange)) + "-" + str(max(timerange)) )

        lst = expr.split(",")
        rexp_step = re.compile("^(\d+-\d+)/(\d+)$")
        rexp_range = re.compile("^(\d+)-(\d+)$")

        expr_range = []
        for field in lst:
            # Extra variables for time calculation
            step = None
            buff = None
            
            result = rexp_step.match(field)
            if  result != None:
                field = result.groups()[0]
                # We need to take step in count
                step = int(result.groups()[1])
                if step not in timerange:
                    raise ValueError("stepwidth",
                                     self.timenames[type],
                                     "Must be between %(min)s and %(max)s" % { "min": min(timerange),
                                                                               "max": max(timerange) } )

            result = rexp_range.match(field)
            if (result != None): 
                if (int(result.groups()[0]) not in timerange) or (int(result.groups()[1]) not in timerange):
                    raise ValueError("range",
                                     self.timenames[type],
                                     "Must be between %(min)s and %(max)s" % { "min": min(timerange),
                                                                               "max": max(timerange) } )
                # Now we deal with a range...
                if step != None :
                    buff = range(int(result.groups()[0]), int(result.groups()[1])+1, step)
                else :
                    buff = range(int(result.groups()[0]), int(result.groups()[1])+1)

            elif not field.isdigit():
                raise ValueError("fixed",
                                 self.timenames[type],
                                 "%s is not a number" % ( field ) )
            elif int(field) not in timerange:                
                raise ValueError("fixed",
                                 self.timenames[type],
                                 "Must be between %(min)s and %(max)s" % { "min": min(timerange),
                                                                           "max": max(timerange) } )
            if buff != None :
                expr_range.extend(buff)
            else :
                expr_range.append(int(field))

        expr_range.sort()
        # Here we may need to check wether some elements have duplicates
        self.fields[type] = expr_range
 

    #### HERE ENDS THE CODE BORROWED FROM gnome-schedule ###

    def _is_valid(self):
        """Validates the data to check for a well-formated cron
        entry.
        Returns True or false"""

        try:
            for typ, exp in self.fields.items():
                self.checkfield(exp, typ)
        except ValueError,(specific,caused,explanation):
            print "PROBLEM TYPE: %s, ON FIELD: %s -> %s " % (specific,caused,explanation)
            return False
        return True

    def __next_time(self, time_list, time_now):
        """Little helper function to find next element on the list"""
#        print "__next_time", time_list, time_now
        tmp = [x for x in time_list if x >= time_now]
#        print "tmp", tmp
        carry = False
        if len(tmp) == 0:
            carry = True
            sol = time_list[0]
        else:
            if not carry:
                sol = tmp[0]
            else :
                if len(tmp) == 1:
                    carry = True
                    sol = time_list[0]
                else :
                    carry = False
                    sol = tmp[1]
        return sol, carry

    def __prev_time(self, time_list, item):
        """Little helper function to find next element on the list"""
#        print "time_list: %s" % time_list
#        print "item: %s" % item
        pos = time_list.index(item)
#        print "pos: %s" % pos
        elem = time_list[pos-1]
#        print "elem: %s" % elem
        carry = elem >= time_list[pos]
        return elem, carry

    def __next_month(self, month, sol):
        """Find next month of execution given the month arg. If month
        is different than current calls all the other __next_*
        functions to set up the time."""
       
        sol['month'], carry = self.__next_time(self.fields['month'], month)
        if carry :
            sol['year'] += 1
        if sol['month'] != month :
            self.__next_day(1,sol)
            self.__next_hour(0,sol)
            self.__next_minute(0,sol)
            return False
        return True

    def __next_minute(self, minute, sol):
        """Find next minute of execution given the minute arg."""
        sol['minute'], carry = self.__next_time(self.fields['minute'], minute)
        if carry:
            self.__next_hour(sol['hour']+1, sol)
        return True

    def __next_hour(self, hour, sol):
        """Find next hour of execution given the hour arg. If hour is
        different than current calls the __next_hour function to set
        up the minute """
#        print "__next_hour", hour, sol
        sol['hour'], carry = self.__next_time(self.fields['hour'], hour)
#        print "sol['hour']", sol['hour'], "carry", carry
        if carry:
            self.__next_day(sol['day']+1, sol)
        if sol['hour'] != hour:
            self.__next_minute(0,sol)
            return False
        return True

    #el weekday se calcula a partir del dia, el mes y a�o dentro de sol
    def __next_day(self, day, sol):
        """Find next day of execution given the day and the month/year
        information held on the sol arg. If day is different than
        current calls __next_hour and __next_minute functions to set
        them to the correct values"""

        while True:
            try:
                now = datetime.date(sol['year'], sol['month'], day)
                # first calculate day
                day_tmp, day_carry = self.__next_time(self.fields['day'], day)
#                print "day_tmp", day_tmp
#                print "day_carry", day_carry
                day_diff = datetime.date(sol['year'], sol['month'], day_tmp) - now
#                print "day_diff", day_diff
                break
            except ValueError:
                self.__next_month(sol['month']+1, sol)
                day = 1
                now = datetime.date(sol['year'], sol['month'], day)

        # The way is handled on the system is monday = 0, but for crontab sunday =0
        weekday = now.weekday()+1

        # if we have all days but we don't have all weekdays we need to
        # perform different
        if len(self.fields['day']) == 31 and len(self.fields['weekday']) != 8:
#            print "Entra el colega por aqui ...."
            weekday_tmp, weekday_carry = self.__next_time(self.fields['weekday'], weekday)
            # Both 0 and 7 represent sunday
            weekday_tmp -= 1
            if weekday_tmp < 0 : weekday_tmp = 6
            weekday_diff = datetime.timedelta(days=weekday_tmp - (weekday - 1))
            if weekday_carry :
                weekday_diff += datetime.timedelta(weeks=1)
            weekday_next_month = (now + weekday_diff).month != now.month
#            print "weekday_next_month", weekday_next_month
            # If next weekday is not on the next month
            if not weekday_next_month:
#                print "weekday_diff", weekday_diff
#                print "now", now
                sol['day'] = (now + weekday_diff).day
#                print "sol['day']", sol['day'], "day", day
#                print "sol['month']", sol['month'], "day", day
                if sol['day'] != day :
                    self.__next_hour(0,sol)
                    self.__next_minute(0, sol)
                    return False
                return True
            else:
                flag = self.__next_month(sol['month']+1, sol)
                if flag :
#                    print "flag!"
                    #return self.__next_day(1, sol)
                    self.__next_day(1, sol)
                    self.__next_hour(0,sol)
                    self.__next_minute(0, sol)
                    #return False
                return False

        # if we don't have all the weekdays means that we need to use
        # them to calculate next day
        if len(self.fields['weekday']) != 8:
            weekday_tmp, weekday_carry = self.__next_time(self.fields['weekday'], weekday)
            # Both 0 and 7 represent sunday
            weekday_tmp -= 1
            if weekday_tmp < 0 : weekday_tmp = 6
            weekday_diff = datetime.timedelta(days=weekday_tmp - (weekday - 1))
            if weekday_carry :
                weekday_diff += datetime.timedelta(weeks=1)
            weekday_next_month = (now + weekday_diff).month != now.month
            # If next weekday is not on the next month
            if not weekday_next_month :
                #  If the next day is on other month, the next weekday
                #  is closer to happen so is what we choose
                if day_carry:
                    sol['day'] = (now + weekday_diff).day
                    if sol['day'] != day :
                        self.__next_hour(0,sol)
                        self.__next_minute(0, sol)
                        return False
                    return True
                else :
                    # Both day and weekday are good candidates, let's
                    # find out who is going to happen
                    # sooner
                    diff = min(day_diff, weekday_diff)
                    sol['day'] = (now+diff).day
                    if sol['day'] != day :
                        self.__next_hour(0,sol)
                        self.__next_minute(0, sol)
                        return False
                    return True
                
        sol['day'] = day_tmp
        if day_carry :
            self.__next_month(sol['month']+1, sol)
        if sol['day'] != day :
            self.__next_hour(0,sol)
            self.__next_minute(0, sol)
            return False
        return True
                

    def next_run(self, time = datetime.datetime.now()):
        """Calculates when will the next execution be."""
        sol = {'minute': 0, 'hour': 0, 'day': 0, 'month' : 0, 'year' : time.year}
        # next_month if calculated first as next_day depends on
        # it. Also if next_month is different than time.month the
        # function will set up the rest of the fields
        self.__next_month(time.month, sol) and \
                                      self.__next_day(time.day, sol) and \
                                      self.__next_hour(time.hour, sol) and \
                                      self.__next_minute(time.minute, sol)
        return datetime.datetime(sol['year'], sol['month'], sol['day'], sol['hour'], sol['minute'])

    def prev_run(self, time = datetime.datetime.now()):
        """Calculates when the previous execution was."""
        base = self.next_run(time)
#        print "Ya se ha calculado la siguente vez: %s" % base
        # minute
        prev_minute, carry = self.__prev_time(self.fields['minute'], base.minute)
        min_diff = datetime.timedelta(minutes=(base.minute - prev_minute))
        base -= min_diff
        if not carry :
            return base

        # hour
        prev_hour, carry = self.__prev_time(self.fields['hour'], base.hour)
        hour_diff = datetime.timedelta(hours=(base.hour - prev_hour))
        base -= hour_diff
        if not carry :
            return base

        tmp_base = base
        previous_months = False
        while True:
            # day
            while True:
                try:
#                    print "__prev_time day"
                    prev_day, carry_day = self.__prev_time(self.fields['day'], tmp_base.day)
#                    print "prev_day", prev_day
#                    print "carry_day", carry_day
                    break
                except ValueError:
                    tmp_base -= datetime.timedelta(days = 1)
#            print "base.day", base.day
#            print "base.month", base.month
#            print "prev_day", prev_day
#            print "carry_day", carry_day
            if carry_day:
#                if base.month <= 11:
#                    no_days = monthrange(base.year, base.month + 1)[1]
#                else:
#                    no_days = monthrange(base.year + 1, 1)[1]
                if (base.month == 1):
                    no_days = monthrange(base.year - 1, 12)[1]
                    carry_day = False
                else:
                    no_days = monthrange(base.year, base.month - 1)[1]
#                print "no_days", no_days
#                print "dias de diferencia:", no_days - prev_day + base.day
                day_diff = datetime.timedelta(days=(no_days - prev_day + base.day))
            else:
                day_diff = datetime.timedelta(days=(base.day - prev_day))
#            print "day_diff", day_diff
            
            prev_weekday, carry_weekday = self.__prev_time(self.fields['weekday'], base.weekday()+1)
#            print "prev_weekday: %s" % prev_weekday
#            print "carry_weekday: %s" % carry_weekday
            
            # if we have all days but we don't have all weekdays we need to
            # perform different
            if len(self.fields['day']) == 31 and len(self.fields['weekday']) != 8:
                # Both 0 and 7 represent sunday
#                print "Entrando por los dias raros estos ..."
                prev_weekday -= 1
                if prev_weekday < 0 : prev_weekday = 6
                
                if carry_weekday :
                    day_diff = datetime.timedelta(days=7+base.weekday() - prev_weekday)
#                    print "day_diff: %s" % day_diff
                    carry = base.month != (base - day_diff).month
#                    print "carry: %s" % carry
                else:
                    weekday_diff = datetime.timedelta(days=base.weekday() - prev_weekday)
                    # weekday no es en el otro mes
                    day_diff = max([day_diff, weekday_diff])
                    carry = False

            elif len(self.fields['weekday']) != 8:
                # Both 0 and 7 represent sunday
                prev_weekday -= 1
                if prev_weekday < 0 : prev_weekday = 6
                weekday_diff = datetime.timedelta(days=base.weekday() - prev_weekday)
                
                if carry_weekday :
                    weekday_diff += datetime.timedelta(weeks=1)
                    if carry_day :
                        # ambos son el otro mes
                        day_diff = max([day_diff, weekday_diff])
                        carry = True
                    else:
                        # el day simple esta en el mismo mes y el weekday en otro
                        pass
                else:
                    # weekday no es en el otro mes
                    if carry_day :
                        # el day esta en el otro mes y el weekday no
                        prev_day = weekday_diff
                        carry = False
                    else :
                        # ambos estan el el mero mes
                        day_diff = min([day_diff, weekday_diff])
                        carry = False
                    
            else :
                carry = carry_day

#            print "day_diff", day_diff
#            print "base", base
            base -= day_diff
#            print "base", base
#            print "carry", carry
            if not carry :
                return base

            # month
            try:
                if not previous_months:
#                    print "Mes anterior cuidado -----------------------------------------------------"
#                    print "base: %s    base.month: %s" % (base, base.month)
#                    print "tmp_base: %s    tmp_base.month: %s" % (tmp_base, tmp_base.month)
                    prev_month, carry = self.__prev_time(self.fields['month'], tmp_base.month)
#                    print "prev_month: %s   carry: %s" % (prev_month, carry)
                    month_diff = datetime.date(base.year, base.month, base.day) - \
                                 datetime.date(not carry and base.year or base.year - 1, prev_month, base.day)
#                    print "month_diff: %s" % month_diff
#                    print "Base: %s" % base
                    base -= month_diff
#                    print "Base menos month_diff: %s" % base
#                    print "---------------------------------------------------------------------------"
                else:
                    base = tmp_base
                break
            except ValueError:
                tmp_base -= datetime.timedelta(days = tmp_base.day)
                previous_months = True

        return base 



    def is_expired(self, time = datetime.datetime.now()):
        """If the expiration parameter has been set this will check
        wether too much time has been since the cron-entry. If the
        expiration has not been set, it throws ValueError."""
        if self.expiration == 0 :
            raise ValueError("Missing argument",
                             "Expiration time has not been set")
        next_beg = self.next_run(time)
        next_end = next_beg + self.expiration
        prev_beg = self.prev_run(time)
        prev_end = prev_beg + self.expiration
        if (time >= next_beg and time <= next_end) or (time >= prev_beg and time <= prev_end) :
            return False
        return True

if __name__ == "__main__" :
    cron_job_list = '''00 03 * * 2,5
00 02 * * 1,6
00 01 * * 1,2,3,4,5
00 04 * * 2,4
00 06 * * 2,3,4,5,6
00 04 * * 2,3,4,5,6
00 00 * * 2,3,4,5,6
00 23 * * 3,5
00 23 * * 2,4
00 23 * * 1,2,3,4,5
00 04 * * 2,4
00 04 * * 2,4
30 00 * * 1,2,3,4,5
30 01 * * 2,3,4,5,6
10 05 * * 2,3,4,5,6
58 02 * * 1,2,3,4,5,6
00 03 30 * *
00 16 * * 7'''
    cron_job_list = '''00 03 * * 6'''
    cron_job_list = '''30 01 15 * *'''
    cron_job_list = '''30 01 * * *'''
    cron_job_list = '''00 03 2 * *'''
    cron_job_list = '''30 01 4 * *'''
    cron_job_list = '''17 4 3 * *'''
    d = datetime.datetime(2012, 4, 1)
    d = datetime.datetime.now()
    for cron_job_def in cron_job_list.split('\n'):
        print "--------------------------- %s -----------------------------" % cron_job_def
        sce = SimpleCrontabEntry(cron_job_def)
        print "Hoy es: %s" % d
        d1 = sce.next_run(d) + datetime.timedelta(minutes = 1)
        print "Siguiente ejecucion: %s" % d1
        print "Siguiente ejecucion: %s" % sce.next_run(d1)
        ant = sce.prev_run(d)
        print "Anterior ejecucion: %s" % ant
        print "Anterior ejecucion a la anterior: %s" % sce.prev_run(ant)
