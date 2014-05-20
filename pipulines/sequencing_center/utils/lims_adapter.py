import subprocess
import tempfile

class LIMSAdapter(object):

    def __init__(self, runID, rakeCommand, limsHost, rakeFile, railsEnv):

        self.runInfo = {}
        self.runID = runID
        self.RAKE_COMMAND = rakeCommand
        self.LIMS_HOST = limsHost
        self.RAKE_FILE = rakeFile
        self.RAILS_ENV = railsEnv

    def _initializeRunInfo(self):
        cmd = ['ssh', 
               self.LIMS_HOST, 
               self.RAKE_COMMAND, 
               '-f', self.RAKE_FILE, 
               'RAILS_ENV=%s' % self.RAILS_ENV, 
               'analyze:solexa:config', 
               'run=%s' % self.runID]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        (runInfoText, err) = process.communicate()
        if process.returncode != 0:
            raise Exception(
                'Return code "%s" while connecting to the LIMS host '
                'with this command: "%s"' 
                % (process.returncode, ' '.join(cmd)))
        self.runInfo = self._parseRunInfo(runInfoText)


    def _parseRunInfo(self, runInfoText):
        runInfo = {}
        for line in runInfoText.split('\n'):
            lineParts = line.strip().split(' ')
            key = lineParts[0]
            value = ' '.join(lineParts[1:])
            if key:
                runInfo[key] = value
        return runInfo

    # ---------
    # !! Internal only! for the sake of portability and testability, 
    # Don't use these getters from outside classes. 
    # Instead write a new function in this class if needed.
    def _get(self, key):
        if not self.runInfo:
            self._initializeRunInfo()
        return self.runInfo.get(key)

    def _getByLane(self, lane, key):
        return self._get('gerald:0:lane:%s:%s' % (lane, key))
    # ---------

    def isAlignmentRequested(self, lane):
        return self._getByLane(lane, 'analysis_type') == 'map'
        
    def getPipelineRunID(self):
        return self._get('pipeline_run_id')

    def getPlatform(self):
        return self._get('platform')
