import os
import subprocess
import tempfile

class LIMSAdapter(object):

    def __init__(self, 
                 runID, 
                 rakeCommand=None, 
                 limsHost=None, 
                 rakeFile=None, 
                 railsEnv=None):

        self.runID = runID

    def isAlignmentRequested(self, lane):
        return True
        
    def getRelativeAnalysisPath(self):
        return self.runID+'_9999'

    def getPlatform(self):
        return 'miseq'

    def getRelativeReferencePath(self, BWAVersion):
        return os.path.join(
            'H_sapiens',
            'hg19',
            'BWA-'+BWAVersion,
            'hg19.fa'
            )

