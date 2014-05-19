#!/usr/bin/env python

min_python_version = '2.7.0'

import sys

def checkVersionGreaterThan(required_version):
    (req_major, req_minor, req_patch) = required_version.split('.')
    version = sys.version.split(' ')[0]
    (major, minor, patch) = version.split('.')
    def badVersion():
        raise Exception(
            'Python version must be at least %s. Current version is %s' 
            % (required_version, version))
    if major == req_major:
        if minor == req_minor:
            if int(patch) < int(req_patch):
                badVersion()
        elif int(minor) < int(req_minor):
            badVersion()
    elif int(major) < int(req_major):
        badVersion()
    # else version is ok

checkVersionGreaterThan(min_python_version)


import argparse
import os
import subprocess


class CoverageReporter(object):

    def __init__(self, opts=None):
        if opts:
            self.opts = opts
        else:
            self.opts = {}
            self._parseCommandLineArgs()
        print self.opts

    def start(self):
        with open(self._getOutputFileName(), 'w') as f:
            subprocess.call(['coverageBed', 
                             '-abam', self.opts['bam'], 
                             '-b', self.opts['bed'],
                             '-hist'
                             ], stdout=f)

    @classmethod
    def _trimExtension(cls, filename, ext):
        parts = filename.split('.')
        if parts[-1] == ext:
            parts = parts[:-1]
        return '.'.join(parts)

    def _getOutputFileName(self):
        shortbamname = self._trimExtension(
            os.path.basename(self.opts['bam']),'bam')
        shortbedname = self._trimExtension(
            os.path.basename(self.opts['bed']),'bed')
        outfile = shortbamname + '_' + shortbedname + '.coverage'
        return os.path.join(self.opts['outputdir'], outfile)

    def _parseCommandLineArgs(self):
        parser = argparse.ArgumentParser(
            description='Analyze NGS coverage over a specified genome region'
        )
        parser.add_argument('--bam', dest='bam')
        parser.add_argument('--bam-pe', dest='bampe')
        parser.add_argument('--bam-list', dest='bamlist')
        parser.add_argument('--bed', dest='bed')
        parser.add_argument('--bed-list', dest='bedlist')
        parser.add_argument('--genome', dest='genome', required=True)
        parser.add_argument('--down-sample', dest='downsample')
        parser.add_argument('--output-dir', dest='outputdir')

        args = parser.parse_args()

        #TODO clean up validation after all cmdline options are in place
        if any([args.bampe, args.bamlist, args.bedlist, args.downsample]):
            raise Exception(
                'To do: Not all commandline options are implemented.')
            if not all([args.bam, args.bed, args.genome, args.outputdir]):
                raise Exception('Required arguments are missing')
        #/TODO

        self.opts['bam'] = args.bam
        self.opts['bed'] = args.bed
        self.opts['genome'] = args.genome
        self.opts['outputdir'] = args.outputdir

if __name__=='__main__':
    reporter = CoverageReporter()
    reporter.start()
