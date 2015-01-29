
###AUTHOR:Nathaniel Watson
##Jan 28, 2015
###

from argparse import ArgumentParser
import os,sys


ArchiveCompleteSentinal="Archive_complete.txt"
IlluminaCompleteSentinal="Basecalling_Netcopy_complete.txt"

description = "Run this script on any machine to which the sequencing machine writes (middleware device) in order to find out whether the given run as had its raw data archived, and delete that run if desirable from the middleware."
parser = ArgumentParser(description=description)
parser.add_argument('-r','--run-name',required=True,help="The path to a sequencing run containing the raw data. It should be on the machine that the sequencing machine writes to.")
parser.add_argument('--delete',action="store_true",help="Presence of this option indicates to delete the run from the middleware device if it has been archived already. This script doesn't actually delete the run, rather it just moves the run to the 'Archived' folder.")

args = parser.parse_args()
delete = args.delete
runName = args.run_name.strip()

if not os.path.exists(runName):
	raise OSError("The given run name '{runName}' that was suppled to the run_name parameter doesn't exist!".format(runName=runName))

toArchiveFolder = os.path.join(os.path.dirname(runName),"Archived")
if delete:
	if not os.path.exists(toArchiveFolder):
		raise OSError("Archived folder {archivedPath} does not exist!. This script assumes the Archived folder resides within the same folder as the run name.".format(archivedPath=toArchiveFolder))

sequencingCompleteFile = os.path.join(runName,IlluminaCompleteSentinal)
if os.path.exists(sequencingCompleteFile) and os.path.exists(os.path.join(runName,ArchiveCompleteSentinal)):
	status="archived"
	if delete:
		os.rename(runName,os.path.join(toArchiveFolder,os.path.basename(runName)))
elif os.path.exists(sequencingCompleteFile):	
		status="unarchived"
else:
	status="unknown" #means either sequencing in progress or the sequencing failed

print(status)	

#On ashton or maigret, for example, you can run this bash for loop:
#for i in /Volumes/IlluminaRuns5/Runs/1*; do echo -n "$i "; python checkRawDataArchiveComplete.py -r $i; done
