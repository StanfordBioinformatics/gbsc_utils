
from pipu.components import Pipeline, Segment, Subsegment, Step

from pieces import general

class MiSeqAnalysis(Pipeline):
    
    def __init__(self, *args, **kwargs):
        super(MiSeqAnalysis, self).__init__(*args, **kwargs)

        main = Segment()
        self.add(main)

        createDirectories = general.CreateDirectories({
            'analysis': self.getUserSetting('analysisDir'),
            'results': self.getUserSetting('resultsDir'),
        })

        main.add(createDirectories)

