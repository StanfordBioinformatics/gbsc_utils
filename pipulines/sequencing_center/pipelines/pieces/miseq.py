import os
import re

from pipu.components import Pipeline, Step, Subsegment, Segment

class Helper(object):

    _R1MatchPattern = '^([\S]*)R1([\S]*).fastq(.gz)?$'

    def _getFastqDir():
        return os.path.join(
            self.runDir, 'Data', 'Intensities', 'BaseCalls')
            
    def _getFastqFiles(self):
        files = os.listdir(fastqDir)
        R1List = self._getRead1(files)
        R2List = self._getRead2(files, R1List)
        if R2List:
            isSingle = False
            if len(R1) != len(R2):
                raise Exception(
                    'fastq files for paired ends could not be matched. '
                    'Read1: "%s". Read2: "%s".' % (R1, R2))
            return (zip(R1List, R2List), isSingle)
        else:
            isSingle = True
            return (R1List, isSingle)

    def _getRead1(self):
        R1List = []
        for filename in files:
            match = re.match(self._R1MatchPattern, filename)
            if match:
                R1List.append(filename)
        return R1List

    def _getRead2(self, files, R1List):
        R2List = []
        for R1 in R1List:
            match = re.match(self._R1MatchPattern, R1)
            R2 = match.groups()[0]+'R2'+match.groups()[1]+\
                 '.fastq'+match.groups()[2]
            if R2 in files:
                R2List.append(R2)
        return R2List

    def _getSamFile(self, read1):
        return os.path.join(self.analysisDir,
                            read1+'.sam')        

class AlignSubsegment(Subsegment):
    def prepare(self):

        helper = AlignmentHelper()

        (fastqList, isSingle) = helper._getFastqFiles()
        for fastq in fastqList:
            if isSingle:
                cmd = 'bwa mem %s %s > %s' % (self.referenceFile, fastq, helper._getSameFile(fastq))
            else:
                cmd = 'bwa mem %s %s %s > %s' % (self.referenceFile, fastq[0], fastq[1], helper._getSameFile(fastq[0]))
                step = self.newStep(
                    command=cmd
                )

        #bwa mem ref.fa reads.fq > aln-se.sam
        #bwa mem ref.fa read1.fq read2.fq > aln-pe.sam
