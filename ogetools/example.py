#!/bin/env python

from ogetools import accounting

source = '/srv/gs1/software/oge2011.11p1/scg3-oge-new/common/accounting'
grepkey = 'seq_pipeline'

jobstats = accounting.Accounting(source, grepkey)

jobstats.filter('qname', 'matches', 'seq_pipeline')
jobstats.filter('owner', 'matches', 'nhammond')

print "Total jobs in queue 'seq_pipeline' by owner 'nhammond': %s" \
    % jobstats.count()

jobstats.reset()
jobstats.filter('qname', 'matches', 'seq_pipeline')
owners = jobstats.getColumnUniqueValues('owner')
print "Users who have run jobs in 'seq_pipeline': %s" % owners

jobstats.reset()

jobstats.filter('qname', 'matches', 'seq_pipeline')
jobstats.filter('job_name', 'contains', 'TENN_0235')
print 'Stats for analysis run TENN_0235:'
print '  Total jobs: %s' % jobstats.count()
jobtime = 0
for job in jobstats.getColumns('ru_wallclock', 'slots'):
    ru_wallclock = float(job[0])
    slots = int(job[1])
    jobtime += (ru_wallclock * slots)/60/60
print '  Total hours used: %s' % jobtime


