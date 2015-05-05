from scgpm_lims import Connection
import subprocess
import gbsc_utils

#module load rundir/current

conn = Connection()

def getPipelineRuns(run):
	"""
	Function : Retrieves the finished and unfinished pipeline run IDs for the specified sequencing run from UHTS.
	Args     : run - str. The name of a sequencing run.
	Returns  : A two item tuple where the 1st item is a list of finished pipeline run IDs, and the 2nd is a list of unfinished pipeline run IDs.
	"""
	ri = conn.getruninfo(run) #ri = runInfo

	finishedRuns = []
	notFinishedRuns = []
	pruns = ri['pipeline_runs']  #pruns = pipelineRuns
	for runId, prd in pruns:     #prd = pipelienRunData
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
	Returns  : int
	"""
	ri = conn.getruninfo(run)      #ri = runInfo
	pruns = ri['pipeline_runs']  #pruns = pipelineRuns
	maxPrunId = max([int(x) for x in pruns.keys()])
	return maxPrunId
	
def setLatestPipelineRunToFinished(run):
	"""
	Function :
	Args     : run - str. Sequencing run name.
	Returns  : int
	"""
	maxPrunId = getMaxPipelineRunId(run)
	cmd = "endrun.py --pipeline_id {maxPrunId} {run}".format(maxPrunId=maxPrunId,run=run)
	gbsc_utils.createSubprocess(cmd)
