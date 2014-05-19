#!/bin/env python

import copy
import datetime
import re
import subprocess
import tempfile
import time

class Accounting(object):

    def __init__(self, filename, grepkey=None):

        self.fields = None
        self._data = None
        self._data_original = None

        self._init_fields()

        if grepkey:
            with self._grep(filename, grepkey) as f:
                self._init_from_file(f)
        else:
            with open(filename, 'r') as f:
                self._init_from_file(f)

    def _init_fields(self):
        # OGE accounting file column info: 
        # http://manpages.ubuntu.com/manpages/lucid/man5/sge_accounting.5.html
        field_names = [
            'qname',    #'seq_pipeline', 
            'hostname',    #'greenie.local', 
            'group',    #'scg-users', 
            'owner',    #'bettingr', 
            'job_name',    #'unpack_bcl_L1_1514_HAVE_0319', 
            'job_number',    #'6866', 
            'account',    #'sge', 
            'priority',    #'0', 
            'submission_time',    #'1351796387', 
            'start_time',    #'1351796388', 
            'end_time',    #'1351802518', 
            'failed',    #'100', 
            'exit_status',    #'137', 
            'ru_wallclock',    #'6130',   
            'ru_utime',    #'56.981337', 
            'ru_stime',    #'71.228171', 
            'ru_maxrss',    #'24900.000000',
            'ru_ixrss',    #'0', 
            'ru_ismrss',    #'0', 
            'ru_idrss',    #'0', 
            'ru_isrss',    #'0', 
            'ru_minflt',    #'30929642', 
            'ru_majflt',    #'0', 
            'ru_nswap',    #'0', 
            'ru_inblock',    #'0.000000', 
            'ru_oublock',    #'16432', 
            'ru_msgsnd',    #'0', 
            'ru_msgrcv',    #'0', 
            'ru_nsignals',    #'0', 
            'ru_nvcsw',    #'350907', 
            'ru_nivcsw',    #'75533', 
            'project',    #'NONE', 
            'department',    #'defaultdepartment', 
            'granted_pe',    #'shm', 
            'slots',    #'8', 
            'task_number',    #'0', 
            'cpu',    #'783.980000', 
            'mem',    #'26.547771', 
            'io',    #'9.985688', 
            'category',    #'-U seq_pipeline_operators -u bettingr -q seq_pipeline -pe shm 8', 
            'iow',    #'0.000000', 
            'pe_taskid',    #'NONE', 
            'max_vmem',    #'3274579968.000000', 
            'arid',    #'0', 
            'ar_submission_time',    #'0'
            ]
        
        self.fields = {}
        i = 0
        for field in field_names:
            self.fields[field] = i
            i+=1

    def _grep(self, filename, grepkey):
        f = tempfile.TemporaryFile()
        subprocess.call(['grep',grepkey,filename], stdout=f)
        return f

    def _init_from_file(self, f):
        self._data = []
        f.seek(0)
        for line in f:
            self._data.append(line.strip().split(':'))

    def count(self):
        return len(self._data)

    def getColumnUniqueValues(self, field):
        values = set()
        for row in self._data:
            values.add(row[self.fields[field]])
        return list(values)

    def getColumns(self, *fields):
        values = []
        for row in self._data:
            values_row = []
            for field in fields:
                values_row.append(row[self.fields[field]])
            values.append(values_row)
        return values

    def reset(self):
        if self._data_original:
            self._data = self._data_original
            self._data_original = None

    def filter(self, fieldname, comparator, value):
        if not self._data_original:
            self._data_original = copy.copy(self._data)

        def eq(a,b):
            return float(a) == float(b)
        def gt(a,b):
            return float(a) > float(b)
        def ge(a,b):
            return float(a) >= float(b)
        def lt(a,b):
            return float(a) < float(b)
        def le(a,b):
            return float(a) <= float(b)
        def matches(string,pattern):
            return re.match(pattern,string)
        def contains(string,pattern):
            return re.search(pattern,string)
        def doesnotmatch(string,pattern):
            return not re.match(pattern,string)

        comparefxn = eval(comparator)

        filtered_data=[]

        for row in self._data:
            if comparefxn(row[self.fields[fieldname]], value):
                filtered_data.append(row)

        self._data = filtered_data

    @classmethod
    def convertDateToSeconds(cls,
        year, month=0, day=0, hour=0, minute=0, second=0):
        return time.mktime(
            datetime.datetime(
                year, 
                month, 
                day, 
                hour, 
                minute, 
                second
                ).timetuple()
            )

    @classmethod
    def convertSecondsToDate(cls, seconds):
        dt = datetime.datetime.fromtimestamp(float(seconds))
        return dt.__str__()
