
import argparse
import subprocess
import os
import datetime

#runPrefix = "/srv/gs1/projects/scg/SNAP_Scoring/production/replicates/human" #old path on gs1
runPrefix = "/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human" #new path on gsfs0
description = "Runs multiple scoring jobs in parallel, calling runPeakseqWithoutSnapUpdates.rb"
parser = argparse.ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Batch input file.")
parser.add_argument('-r','--run-field-pos',default=0,help="Run name field position (0-base).")
parser.add_argument('-c','--control-field-pos',default=5,help="Control name field position (0-base).")
parser.add_argument('-l','--limit',type=int,help="The number of scoring jobs to run (which will run in parallel as well). For example, a limit of 5 would amount to only running the first 5 jobs (rows) in --infile.")
parser.add_argument('-p','--paired-end',action="store_true",help="Presence of this option indicates that reads are paired-end.")
parser.add_argument('--rescore-control',type=int,default=0,help="The number of days old the control scoring should be in order for it to be rescored. This option is mainly used to rescore a control that is a paired-end (PE) and that was scored using all reads instead of just the forward reads.  So, this option would be helpful to use if the control is paired-end (PE). Up until May 2014, all scoring was done with both forward and reverse reads, so in order to rescore a control with just the forward reads, you'd wan't to incude the --paired-end option and set --rescore_control to the number of since since May 1, 2014.")
#parser.add_argument('--sample-time',action="store_true")
args = parser.parse_args()

limit = args.limit
count = 0
fh = open(args.infile,'r')
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	if line.startswith("#"):
		continue
	line = line.split("\t")
	run = line[args.run_field_pos].strip()
	runPath = os.path.join(runPrefix,run)
	resultsPath = os.path.join(runPath,"results")
#	refTime = datetime.datetime(2014,6,20)
#	if args.sample_time:
#		try:
#			mtime = os.path.getmtime(resultsPath)
#		except OSError:
#			mtime = 0
#		if mtime:
#			dte = datetime.datetime.fromtimestamp(mtime)	
#			if dte > refTime:
#				print("Continuing")
#				continue  #assume that scoring is still ongoing
	control = line[args.control_field_pos].strip()
	cmd = "ruby runPeakseqWithoutSnapUpdates.rb --name {run} --control {control} --force".format(run=run,control=control)
	if args.paired_end:
		cmd += " --paired-end"
	if args.rescore_control > 0:
		cmd += " --rescore-control={}".format(args.rescore_control)
	print(cmd)
	subprocess.Popen(cmd,shell=True)
	if limit:
		count += 1
		if count >= limit:
			break
fh.close()
