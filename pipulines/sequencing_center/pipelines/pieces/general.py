from pipu.components import Pipeline, Step, Segment, Subsegment

class CreateDirectories(Subsegment):

    # This subsegment creates new directories
    #
    # Usage example:
    # s = CreateDirectories(
    #  {
    #   'analysisDir': '/path/to/analysis/dir',
    #   'resultsDir': '/path/to/results/dir'
    #  }
    # )

    def __init__(self, directoriesToCreate):
        super(CreateDirectories, self).__init__()

        for label in directoriesToCreate:
            self.newStep(
                name = 'mkdir_'+label,
                command = 'mkdir -p %s' % directoriesToCreate[label]
                )


