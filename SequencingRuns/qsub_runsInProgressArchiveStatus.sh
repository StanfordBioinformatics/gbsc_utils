#!/bin/bash


###AUTHOR: Nathaniel Watson
###Date  : May 11, 2015
###Description: Run this program to call runsInProgressArchiveStatus.py through qsub. Calls that script with these parameters hardcoded: -c -m -a.
###             There is one required argument to this program, being the run name.


#$ -l h_vmem=1G
#$ -m a
#$ -M nathankw@stanford.edu
#$ -R y
#$ -o /srv/gs1/software/gbsc/gbsc_utils/SequencingRuns
#$ -e /srv/gs1/software/gbsc/gbsc_utils/SequencingRuns

module load gbsc/archiving_runs/uhts

python $GBSC/gbsc_utils/SequencingRuns/runsInProgressArchiveStatus.py -r $1 -c -m -a
