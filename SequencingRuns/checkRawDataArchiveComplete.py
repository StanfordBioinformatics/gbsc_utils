from argparse import ArgumentParser
import os,sys


ArchiveCompleteSentinal="Archive_complete.txt"
IlluminaCompleteSentinal="Basecalling_Netcopy_complete.txt"

description = "Run this script on any machine to which the sequencing machine writes (middleware device) in order to find out whether the given run as had its raw data archived, and delete that run if desirable from the middleware."
parser = ArgumentParser(description=description)
parser.add_argument('-r','--run-name',required=True,help="The path to a sequencing run containing the raw data. It should be on the machine that the sequencing machine writes to.")
parser.add_argument('--delete',action="store_true",help="Presence of this option indicates to delete the run from the middleware device if it has been archived already.")

args = parser.parse_args()
delete = args.delete
outfile = args.outfile
runName = args.run_name.strip()
if not os.path.exists(runName):
	raise OSError("The given run name '{runName}' that was suppled to the run_name parameter doesn't exist!".format(runName=runName))

complete = False
if os.path.exists(os.path.join(runName,IlluminaCompleteSentinal)) and os.path.exists(os.path.join(runName,ArchiveCompleteSentinal)):
	complete = True

sys.stdout.write("complete")	

