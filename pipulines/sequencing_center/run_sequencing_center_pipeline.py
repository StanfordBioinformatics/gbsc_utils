#!/usr/bin/env python
from optparse import OptionParser
import os

from config import Config
from pipelines import miseq
from utils.lookup import Lookup

class IlluminaPipelineWrapper(object):

    _pipelineConstructors = {
        'miseq': {
            # Do alignment?
            True: miseq.MiSeqAnalysis,
        }
    }

    def __init__(self, settings=None):

        self.pipelines = []

        # settings contains values that may be set with commandline arguments,
        # or may be automatically determined if not provided
        #
        # lims is an API for getting and setting values available from the LIMS
        #
        # config contains information for running the pipeline in a given 
        # environment. It can return different sets of values for different
        # detected environments. Values are defined in config.py
        #
        # Lookup contains dictionaries of unchanging values, such as 
        # the number of lanes per flow cell for a given platform

        if settings:
            self.settings = settings
        else:
            self.settings = self._parse_commandline_input()

        self.config = Config()

        self.lims = self.getLIMSAdapter(
            runID=self.settings.get('run'),
            rakeCommand=self.config.get('RAKE_COMMAND'),
            limsHost=self.config.get('LIMS_HOST'),
            rakeFile=self.config.get('RAKE_FILE'),
            railsEnv=self.config.get('RAILS_ENV'),
            )

        self._initializeSettings()

    def _initializeSettings(self):
        if not self.settings.get('lanes'):
            self.settings['lanes'] = self._getDefaultLanes()
        self.settings['analysisDir'] = os.path.join(
            self.config.get('ANALYSIS_ROOT_DIRECTORY'), 
            self.lims.getRelativeAnalysisPath())
        self.settings['runDir'] = os.path.join(
            self.config.get('ACTIVE_RUNS_ROOT_DIRECTORY'),
            self.settings.get('run'))
        self.settings['resultsDir'] = os.path.join(
            self.config.get('RESULTS_ROOT_DIRECTORY'),
            self.settings.get('run'))

    def runPipelines(self):
        if not self.pipelines:
            self._createPipelines()

        for pipeline in self.pipelines:
            pipeline.run()

    def _createPipelines(self):

        self.pipelines = []

        for lane in self.settings.get('lanes'):

            referenceFile = self._getReferenceFile(lane)

            pipelineConstructor = self._getPipelineConstructor(lane)

            pipeline = pipelineConstructor(
                mail=self.config.get('MAIL'),
                directory=self.settings.get('analysisDir'),
                jobManager=self.config.get('JOB_MANAGER'),
                userSettings={
                    'lane': lane,
                    'analysisDir': self.settings.get('analysisDir'),
                    'runDir': self.settings.get('runDir'),
                    'resultsDir': self.settings.get('resultsDir'),
                    'referenceFile': referenceFile
                }
            )

            self.pipelines.append(pipeline)

    def _parse_commandline_input(self):
        parser = OptionParser()
        parser.add_option(
            "-r", 
            "--run", 
            dest="run",
            help="sequencing run name")
        parser.add_option(
            "-l", 
            "--lanes", 
            dest="lanes",
            help="comma-separated list of lane numbers to be analyized")
        (options, args) = parser.parse_args()
        self._clean_args(args)
        return self._clean_options(options)

    def _clean_args(self, args):
        # No args are expected, only keyword options
        if args:
            raise Exception('Unused argument(s): "%s"' % args)

    def _clean_options(self, options_raw):
        options = {}
        options['run'] = self._clean_run_option(options_raw.run)
        options['lanes'] = self._clean_lanes_option(options_raw.lanes)
        return options

    def _clean_run_option(self, run):
        if not run:
            raise Exception('--run argument is required')
        return run

    def _clean_lanes_option(self, lanes_str):
        if lanes_str is None:
            lanes = None
        else:
            lanes = self._parse_lanes_str(lanes_str)
        return lanes

    def _parse_lanes_str(self, lanes_str):
        lanes = []
        try:
            for lane in lanes_str.split(','):
                lanes.append(int(lane))
        except:
            raise Exception('Unable to parse --lanes argument "%s". \n'
                            '  Format is comma-separated with no spaces,'
                            ' e.g. --lanes 1,2,3' % lanes_str)
        return lanes

    def _getDefaultLanes(self):
        numLanes = Lookup.platform\
                   [self.lims.getPlatform()]['lanesPerRun']
        return range(1, numLanes+1)

    def getLIMSAdapter(self, runID, rakeCommand, limsHost, rakeFile, railsEnv):
        # This allows using different lims adapters for different environments.
        exec("from %s import LIMSAdapter" 
             % self.config.get('LIMS_MODULE'))
        return LIMSAdapter(runID, rakeCommand, limsHost, rakeFile, railsEnv)

    def _getReferenceFile(self, lane):
        if self.lims.isAlignmentRequested(lane):
            referenceFile = os.path.join(
                self.config.get('GENOMES_ROOT_DIRECTORY'),
                self.lims.getRelativeReferencePath(
                    self.config.get('BWA_VERSION'))
            )
        else:
            referenceFile = None
        return referenceFile

    def _getPipelineConstructor(self, lane):
        return self._pipelineConstructors\
            [self.lims.getPlatform()]\
            [self.lims.isAlignmentRequested(lane)]

if __name__=="__main__":
    IlluminaPipelineWrapper().runPipelines()
