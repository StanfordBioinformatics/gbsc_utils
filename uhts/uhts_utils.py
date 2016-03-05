from scgpm_lims import Connection
import subprocess
from gbsc_utils import gbsc_utils

#module load rundir/current

conn = Connection()

def getRunInfo(run):
	"""
	Function :
	Args     : run - A sequencing run name.
	Returns  :
	"""
	ri = conn.getruninfo(run)['run_info']
	return ri

def getLaneInfo(run,lane):
	"""
	Function : Returns the lane information from a lane on a sequencing run.
	Args     : run - A sequencing run name.
						 lane - int. Lane number.
	Returns  : dict.
	"""
	ri = getRunInfo(run)
	return ri['lanes'][str(lane)]

def isSequencingFailed(run):
	ri = getRunInfo(run)
	run_status = ri["sequencing_run_status"]
	if (run_status == "sequencing_failed") or (run_status == "sequencing_exception"):
		return True
	return False

def isSequencingDone(run):
	ri = getRunInfo(run)
	run_status = ri["sequencing_run_status"]
	if run_status == "sequencing_done":
		return True
	return False

def getPipelineRuns(run):
	"""
	Function : Retrieves the finished and unfinished pipeline run IDs for the specified sequencing run from UHTS.
	Args     : run - str. The name of a sequencing run.
	Returns  : A two item tuple where the 1st item is a list of finished pipeline run IDs, and the 2nd is a list of unfinished pipeline run IDs.
	"""
	ri = getRunInfo(run)

	finishedRuns = []
	notFinishedRuns = []
	pruns = ri['pipeline_runs']  #pruns = pipelineRuns
	for runId in pruns:     
		prd = pruns[runId]    #prd = pipelienRunData
		finished = prd['finished']
		if finished:
			finishedRuns.append(runId)
		else:
			notFinishedRuns.append(runId)
	return (finishedRuns,notFinishedRuns)

def getMaxPipelineRunId(run):
	"""
	Function :
	Args     : run - str. Sequencing run name.
	Returns  : int, or the None object if no pipeline runs.
	"""
	ri = getRunInfo(run)
	pruns = ri['pipeline_runs']  #pruns = pipelineRuns
	if not pruns:
		return None
	maxPrunId = max([int(x) for x in pruns.keys()])
	return maxPrunId
	
def setLatestPipelineRunToFinished(run):
	"""
	Function : Of the pipeline runs of the specified run, sets the one with the largest ID (integer) to finished.
	           If no pipeline runs, nothing happens.
	Args     : run - str. Sequencing run name.
	Returns  : 
	"""
	maxPrunId = getMaxPipelineRunId(run)
	cmd = "endrun.py --pipeline_id {maxPrunId} {run}".format(maxPrunId=maxPrunId,run=run)
	gbsc_utils.createSubprocess(cmd)


def isArchivingDone(run):
	ri = getRunInfo(run)
	return ri['archiving_done']
