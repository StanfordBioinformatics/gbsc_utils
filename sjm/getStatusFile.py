###
#AUTHOR: Nathaniel Watson
###

import argparse
import glob
import subprocess
import os

description = "Given a file with directory paths, one per line, looks for SJM status files in each path.  For each status file found, it is searched for the specified jobid. All status files containing the job ID will be reported."
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Input file with paths to check for *.sjm.status files. There is one path per line.")
parser.add_argument('-j','--jobid',required=True,help="The job ID to search for.")
parser.add_argument('-r','--rerun',action="store_true",help="Rerun the status file if one was found.  Make sure you have the path to sjm in your path.")

args = parser.parse_args()
jobid = args.jobid
rerun = args.rerun
fh = open(args.infile,'r')
for line in fh:
	path = line.strip()
	if not path:
		continue
	path = os.path.join(path,"*.status")
	statusList = glob.glob(path) #if there are multiple status files, then the most recent one will be at index 0 
	if not statusList:
		continue
	status = statusList[0]
	cmd = "grep -w 'id {jobid}' {status}".format(jobid=jobid,status=status)
	res = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).communicate()[0]
	if res:
		print("Found jobid {jobid} in {status}".format(jobid=jobid,status=status))
		if rerun:
			subprocess.call("sjm {}".format(status),shell=True)
		break
fh.close()
	
	
		



