import runPaths
import json
import re
import os
import sys
from argparse import ArgumentParser
import subprocess
from gbsc_utils import gbsc_utils

conf = os.path.join(os.path.dirname(__file__),"conf.json")
conf = json.load(open(conf,'r'))

runsInProgressDir = conf["runsInProgressDir"]
runsCompletedDir = conf["analysisDoneDir"] #the "Completed" folder in the $runsInProgressDir
runReg = re.compile(r'^\d{4}_')


parser = ArgumentParser(description="Outputs the archive status of a run as being one of 'in_progress','raw_only', or 'all_done'. In addition, the program will, upon request, perform an archive of the raw run and the analysis, and move the rundir from {runsInProgressDir} to {runsCompletedDir}. In order for archiving to occur, make sure to have the environment module 'illumina_pipeline/production' loaded. Note that a run status is set to 'in_progress' when either the raw archive, the analysis archive, or both have a modification timestamp dated within the past {modMinThreshold} minutes, and such runs will not be eligible for archiving or moving.".format(runsInProgressDir=runsInProgressDir,runsCompletedDir=runsCompletedDir,modMinThreshold=runPaths.modMinThreshold))
parser.add_argument("-r","--runname",required=True,help="The name of an Illumina sequencing run. Directory path may be supplied but will be removed.")
parser.add_argument("-m","--move",action="store_true",help="Presence of this option indicates to move the run directory specified in -r to the runs completed folder {completed} if the raw data and analysis archiving is done. If an archive-in-progress is detected, nothing will happen".format(completed=runsCompletedDir))
parser.add_argument("-a","--archive",action="store_true",help="Presence of this option indicates to archive the analysis of a run if the analysis hasn't been archived yet. This step doesn't check the LIMS, but instead takes the lazy approach and assumes that the run has an analysis and that the analysis has finished. Make sure to have the environment module 'illumina_pipeline/production' loaded in order to perform this step!")
args = parser.parse_args()
runName = os.path.basename(args.runname)
runNamePath = os.path.join(runsInProgressDir,runName)
move = args.move
archive = args.archive

#check if the raw archive of the run is done
rawAS = runPaths.rawArchiveDone(runName) #rawAS = rawArchiveStatus
#check if the analysis archive of the run is done
aAS = runPaths.analysisArchiveDone(runName) #aAS = analysisArchiveStatus

doneFlag = runPaths.ARCHIVE_STATE_COMPLETE
notDoneFlag = runPaths.ARCHIVE_STATE_NOT_STARTED
inProgressFlag = runPaths.ARCHIVE_STATE_IN_PROGRESS

if rawAS == inProgressFlag or aAS == inProgressFlag:
	print("in_progress\t{runName}".format(runName=runName))
	sys.exit()
if rawAS == doneFlag and aAS == notDoneFlag:
	print("raw_only\t{runName}".format(runName=runName))
elif rawAS == notDoneFlag and aAS == doneFlag:
	print("analysis_only\t{runName}".format(runName=runName))
elif rawAS == doneFlag and aAS == doneFlag:
	print("all_done\t{runName}".format(runName=runName))
elif rawAS == notDoneFlag and not aAS == notDoneFlag:
	print("nothing_done\t{runName}".format(runName=runName))

if archive:
	if rawAS == notDoneFlag:
    #running the below command always archives the analysis when doing a raw archive
		print("Archiving the raw data and the analysis for run {runName}".format(runName=runName))
		cmd = "run_analysis.rb archive_illumina_run -r {runName} --keep_rundir --verbose".format(runName=runName)
		popen = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		gbsc_utils.checkPopen(cmd=cmd,popen=popen)
	
	elif aAS == notDoneFlag:
		print("Archiving the analysis for run {runName}".format(runName=runName))
		cmd = "run_analysis.rb archive_illumina_run -r {runName} --analysis_only --keep_rundir --verbose".format(runName=runName)
		popen = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		gbsc_utils.checkPopen(cmd=cmd,popen=popen)

	
	
runNamePath = os.path.join(runsInProgressDir,runName)
if rawAS == doneFlag and aAS == doneFlag and move:
	dest = os.path.join(runsCompletedDir,runName)
	print("Moving run {run} to {dest}.".format(run=runName,dest=dest))
	os.rename(runNamePath,dest)
