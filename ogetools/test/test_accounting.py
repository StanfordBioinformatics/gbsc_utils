#!/usr/bin/env python

import os
import unittest

from ogetools.accounting import Accounting

class TestAccounting(unittest.TestCase):

    def setUp(self):
        self.datafile = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
                ),
            'data',
            'test_data.txt'
            )

    def testInit(self):
        oge = Accounting(self.datafile)
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 133)

    def testInitGrep(self):
        oge = Accounting(self.datafile, 'mergesplit')
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 38)

    def testReset(self):
        oge = Accounting(self.datafile)

        oge.filter('job_name','contains','mergesplit')
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 38)

        oge.reset()
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 133)

    def testGetColumnUniqueValues(self):
        oge = Accounting(self.datafile)
        values = oge.getColumnUniqueValues('owner')
        self.assertTrue('bettingr' in values)
        self.assertTrue('nhammond' in values)
        self.assertTrue('dsalins' in values)
        self.assertEqual(len(values), 3)

    def testFilterEq(self):
        oge = Accounting(self.datafile)
        oge.filter('start_time','eq',1375813269)
        values = oge.getColumns('start_time')
        self.assertEqual(len(values), 4)
        self.assertTrue(['1375813269'] in values)

    def testFilterGt(self):
        oge = Accounting(self.datafile)
        oge.filter('start_time','gt',1375813269)
        values = oge.getColumns('start_time')
        self.assertEqual(len(values), 3)
        self.assertTrue(['1375813269'] not in values)

    def testFilterGe(self):
        oge = Accounting(self.datafile)
        oge.filter('start_time','ge',1375813269)
        values = oge.getColumns('start_time')
        self.assertEqual(len(values), 7)
        self.assertTrue(['1375813269'] in values)

    def testFilterLt(self):
        oge = Accounting(self.datafile)
        oge.filter('start_time','lt',1375813269)
        values = oge.getColumns('start_time')
        self.assertEqual(len(values), 126)
        self.assertTrue(['1375813269'] not in values)

    def testFilterLe(self):
        oge = Accounting(self.datafile)
        oge.filter('start_time','le',1375813269)
        values = oge.getColumns('start_time')
        self.assertEqual(len(values), 130)
        self.assertTrue(['1375813269'] in values)

    def testConvertDateToSeconds(self):
        seconds = Accounting.convertDateToSeconds(
            year=2013, 
            month=8, 
            day=6, 
            hour=11, 
            minute=21, 
            second=9
            )
        self.assertEqual(int(seconds), 1375813269)

    def testConvertSecondsToDate(self):
        date = Accounting.convertSecondsToDate(1375813269)
        self.assertEqual(date, '2013-08-06 11:21:09')

    def testFilterMatches(self):
        oge = Accounting(self.datafile)
        oge.filter('job_name','matches',
                   'mergesplit_L8_unmatched_R2_1774_TENN_0236')
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0][0], 
                         'mergesplit_L8_unmatched_R2_1774_TENN_0236')

    def testFilterContains(self):
        oge = Accounting(self.datafile)
        oge.filter('job_name','contains',
                   'L8')
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 28)
        self.assertTrue(['mergesplit_L8_unmatched_R2_1774_TENN_0236']
                        in values)

    def testFilterDoesNotMatch(self):
        oge = Accounting(self.datafile)
        all = oge.count()
        oge.filter('job_name','doesnotmatch',
                   'mergesplit_L8_unmatched_R2_1774_TENN_0236')
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), all - 1)

    def testFilterMultiple(self):
        oge = Accounting(self.datafile)
        oge.filter('job_name','contains',
                   'L8')
        oge.filter('start_time','ge',1375805851)
        values = oge.getColumns('job_name')
        self.assertEqual(len(values), 3)
        self.assertTrue(['stats_1774_TENN_0236_L8_2']
                        in values)


if __name__ == '__main__':
    unittest.main()
