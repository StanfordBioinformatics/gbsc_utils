
import runPaths
import json
import re
import os
from argparse import ArgumentParser

parser = ArgumentParser(description="")
parser.add_argument("-r","--runname",required=True,help="The name of an Illumina sequencing run. Directory path may be supplied but will be removed.")

args = parser.parse_args()
runName = os.path.basename(args.runname)

conf = os.path.join(os.path.dirname(__file__),"conf.json")
conf = json.load(open(conf,'r'))

runsInProgressDir = conf["runsInProgressDir"]
analysisDoneDir = conf["analysisDoneDir"]

runReg = re.compile(r'^\d{4}_')

#check if the raw archive of the run is done
rawDone = runPaths.rawArchiveDone(runName)
#check if the analysis archive of the run is done
analysisDone = runPaths.analysisArchiveDone(runName)

runNamePath = os.path.join(runsInProgressDir,runName)
if analysisDone:		
	dest = os.path.join(analysisDoneDir,runName)
	print("Moving run {run} to {dest}.".format(run=runName,dest=dest))
	os.rename(runNamePath,dest)
