#!/usr/bin/env python

bam = '/srv/gsf0/projects/bustamante/chrY/02_getCoverage/input/bamfiles/130723_PINKERTON_0257_AC28G4ACXX_L4_AAGCTA_pf_small.bam'
bed = '/srv/gsf0/projects/bustamante/chrY/02_getCoverage/input/bedfiles/chrY.capture.hg19.bed'
genome = '/srv/gsf0/projects/bustamante/chrY/02_getCoverage/hg19.genome'
outputdir = '/home/nhammond/out'

from coverageReporter.coverageReporter import CoverageReporter

opts = {}
opts['bam'] = bam
opts['bed'] = bed
opts['genome'] = genome
opts['outputdir'] = outputdir

r = CoverageReporter(opts)
r.start()
