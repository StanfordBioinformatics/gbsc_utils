import runPaths
import json
import re
import os
import sys
from argparse import ArgumentParser
import subprocess
from gbsc_utils import gbsc_utils
from gbsc_utils.uhts import uhts_utils

def setRunToArchived(runName):
	cmd = "lims.py modifyRun {runName} archiving_done True".format(runName=runName)
	print("Setting UHTS archiving flag to finished")
	gbsc_utils.createSubprocess(cmd)
	

#module load rundir/current

conf = os.path.join(os.path.dirname(__file__),"conf.json")
conf = json.load(open(conf,'r'))

runsInProgressDir = conf["runsInProgressDir"]
runsCompletedDir = conf["analysisDoneDir"] #the "Completed" folder in the $runsInProgressDir
newRunsArchive = conf["newRunsArchive"]
runReg = re.compile(r'^\d{4}_')
miseqReg = re.compile(r'.*SPENSER.*')


parser = ArgumentParser(description="Make sure to have the following environment module loaded: gbsc/archiving_runs/uhts. Outputs the archive status of a run as being one of 'in_progress','raw_only', or 'all_done'. In addition, the program will, upon request, perform an archive of the raw run and the analysis, move the rundir from {runsInProgressDir} to {runsCompletedDir}, and set the status of the run in UHTS to archived. Note that a run status is set to 'in_progress' when either the raw archive, the analysis archive, or both have a modification timestamp dated within the past {modMinThreshold} minutes, and such runs will not be eligible for archiving or moving.".format(runsInProgressDir=runsInProgressDir,runsCompletedDir=runsCompletedDir,modMinThreshold=runPaths.modMinThreshold))
parser.add_argument("-r","--runname",required=True,help="The name of an Illumina sequencing run. Directory path may be supplied but will be removed.")
parser.add_argument("-m","--move",action="store_true",help="Presence of this option indicates to move the run directory specified in -r to the runs completed folder {completed} if the raw data and analysis archiving is done. If an archive-in-progress is detected, nothing will happen".format(completed=runsCompletedDir))
parser.add_argument("-a","--archive",action="store_true",help="Presence of this option indicates to archive that which hasn't been archive yet (i.e the raw data and the analysis). This step doesn't check the LIMS, but instead takes the lazy approach and assumes that the run has an analysis and that the analysis has finished. Make sure to have the environment module 'illumina_pipeline/production' loaded in order to perform this step!")
parser.add_argument("-c","--check-finished",action="store_true",help="Presence of this option indicates to check if the run has a finished pipeline run in UHTS. If not, then it will set the latest pipeline run (the one with the largest pipeline run id) to finished in UHTS, granted that there is at least one pipeline run.")
args = parser.parse_args()
runName = os.path.basename(args.runname)
runNamePath = os.path.join(runsInProgressDir,runName)
move = args.move
doArchive = args.archive
checkFinished = args.check_finished


#MISEQ = miseqReg.match(runName)

#check if the raw archive of the run is done
#rawAS = runPaths.rawArchiveDone(runName) #rawAS = rawArchiveStatus
#check if the analysis archive of the run is done
#aAS = runPaths.analysisArchiveDone(runName) #aAS = analysisArchiveStatus

archivingDone = uhts_utils.isArchivingDone(run=runName)
if archivingDone:
	print("{run}: Archived.".format(run=runName))
else:
	print("{run}: Not Archived.".format(run=runName))

#doneFlag = runPaths.ARCHIVE_STATE_COMPLETE
#notDoneFlag = runPaths.ARCHIVE_STATE_NOT_STARTED
#inProgressFlag = runPaths.ARCHIVE_STATE_IN_PROGRESS
#
#if rawAS == inProgressFlag or aAS == inProgressFlag:
#	print("in_progress\t{runName}".format(runName=runName))
#	sys.exit()
#if rawAS == doneFlag and aAS == notDoneFlag:
#	print("raw_only\t{runName}".format(runName=runName))
#elif rawAS == notDoneFlag and aAS == doneFlag:
#	print("analysis_only\t{runName}".format(runName=runName))
#elif rawAS == doneFlag and aAS == doneFlag:
#	print("all_done\t{runName}".format(runName=runName))
#elif rawAS == notDoneFlag and aAS == notDoneFlag:
#	print("nothing_done\t{runName}".format(runName=runName))


#Before running the archive script, must check that there is a pipeline run in UHTS with the status 'done', otherwise, the archive won't proceed.
# Thus, I'll first do that check, and if there isn't one with 'status' set to 'done', I'll set the most recent one to 'done', and if there isn't 
# any pipeline run at all, I'll just let the program error out.

finishedPipelineRuns,unfinishedPipelineRuns = uhts_utils.getPipelineRuns(runName)
allPipelineRuns = finishedPipelineRuns + unfinishedPipelineRuns

if allPipelineRuns: #if none, could be a MiSeq Run as prior to May 20, 2015, those werent analyzed through the APF pipeline.
	if checkFinished:
		if not finishedPipelineRuns:
			uhts_utils.setLatestPipelineRunToFinished(runName) #uses endrun.py in rundir


if doArchive:
#	if rawAS == notDoneFlag:
	if not archivingDone:
		cmd = "run_analysis.rb archive_illumina_run -r {runName} --keep_rundir --verbose".format(runName=runName)
		msg = "Archiving the raw data and the analysis for run {runName}".format(runName=runName)
		if not allPipelineRuns: #could be a MiSeq and thus not have any pipeline runs
			runYear = runPaths.getRunYearMonth(runName)[0]
			cmd = "make_archive_tar.py -f -d {dest} {runNamePath}".format(dest=os.path.join(newRunsArchive,runYear),runNamePath=runNamePath)
    #running the below command always archives the analysis when doing a raw archive
			msg = "Archiving the raw data and the analysis for run {runName}".format(runName=runName)
		print(msg)
		gbsc_utils.createSubprocess(cmd)
		setRunToArchived(runName)
	
#	elif aAS == notDoneFlag:
#		if allPipelineRuns: #then at least there is an analysis to archive
#			print("Archiving the analysis for run {runName}".format(runName=runName))
#			cmd = "run_analysis.rb archive_illumina_run -r {runName} --analysis_only --keep_rundir --verbose".format(runName=runName)
#			gbsc_utils.createSubprocess(cmd)
#			#setRunToArchived(runName) #not necessary since run_analysis.rb will set the flag
#		else:
#			print("No pipelines to archive for run {runName}".format(runName=runName))

#	if (rawAS == doneFlag and aAS == doneFlag) or (rawAS == doneFlag and not allPipelineRuns): 
		#then make sure that in the LIMS, the archive flag is set
		#setRunToArchived(runName)

	
	
runNamePath = os.path.join(runsInProgressDir,runName)
#move to Completed folder if all archiving is done:
#if rawAS == doneFlag and (aAS == doneFlag or not allPipelineRuns) and move:
if archivingDone and move:
	dest = os.path.join(runsCompletedDir,runName)
	print("Moving run {run} to {dest}.".format(run=runName,dest=dest))
	try:
		os.rename(runNamePath,dest)
	except OSError:
		pass 	
