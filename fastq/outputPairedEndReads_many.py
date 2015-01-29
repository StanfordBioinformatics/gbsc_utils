#!/usr/bin/env python
import subprocess
from argparse import ArgumentParser
import fastq_utils as f
import os

description = "Given an input file containing one or more lines of datasets to interleave (or output paire-end reads only in separate files and in the same read order), uses either the local machine or qsub to call outputPairedEndReads.py. Note that you must have your PYTHONPATH set to contain the path /srv/gs1/software/gbsc/gbsc_utils/fastq if you specify the --qsub parameter, since the -v option in the qsub commandline is used to add the PYTHONPATH environment varialbe in the subprocess's environment. I know this is bad styling, will improve when I have the time."

parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The white-space delimited input file where the first two columns are the forward read file name and the reverse the reverse read fastq file name. If the --interleave option is used, then the 3rd column must be the interleaved output file name.")
parser.add_argument('-c','--compress-output',choices=("gzip","bz2"),help="Compress the output with selected method. For GZIP compression, the extension will be set to '.gzip', and for BZ2 it will be '.bz2'.")
parser.add_argument('--interleave',action="store_true",help="Presence of this option indicates to interleave each pair of forward and reverse read files. In this case, the 3rd column in the input file must be the interleave output file name.")
parser.add_argument('--qsub',action="store_true",help="Presence of this option indicates to run the jobs through qsub. Also set --notify argument when using this.")
parser.add_argument('-n','--notify',help="An email address for OGE notifications for job end and abort. Only makes sense to use with the --qsub argument, and is required to use this argument with --qsub.")
parser.add_argument('--outdir',required=True,help="The output directory (must already exist); also the working directory to use with QSUB when --qsub is specified where all stdout and stderr files will be written too. Technially this option isn't needed when --interleave is specified and --qsub isn't, since the input file in this case will specify the output file names; however, for simplicity it's required at this time.")

#peExt variable below is for the extension to be used for output files when interleaving isn't requested.
# I call this format 'paired end ordered' which is when a pair of read files are ordered the same and don't have any singleton reads.
peExt = "_peOrdered.fastq"
args = parser.parse_args()
interleave = args.interleave
infile = args.infile
qsub = args.qsub
notify = args.notify
outdir = args.outdir
if not os.path.exists(outdir):
	parser.error("The path provided to --outdir doens't exist!")
if qsub and not notify:
	parser.error("You must also specify the --notify argument when using --qsub!")
if qsub and not outdir:
	parser.error("You must also specify the --working-directory argument when using --qsub!")

fh = open(infile)
popens = {}
for line in fh:
	line = line.strip()
	if not line:
		continue
	line = line.split()
	f=line[0]
	r=line[1]
	cmd="/srv/gs1/software/gbsc/gbsc_utils/fastq/outputPairedEndReads.py -f {f} -r {r} ".format(f=f,r=r)
	if interleave:
		iout = line[2]
		cmd += "--iout {iout} ".format(iout=iout) 
	else:
		fout = os.path.basename(f).rsplit(".")[0] + peExt
		fout = os.path.join(outdir,fout)
		rout = os.path.basename(r).rsplit(".")[0] + peExt
		rout = os.path.join(outdir,rout)
		cmd += "--fout {fout} --rout {rout} ".format(fout=fout,rout=rout)
	if qsub:
		cmd = "qsub -v PYTHONPATH={PYTHONPATH} -R y -l h_vmem=10G -m ea -M {notify} -wd {outdir} {cmd}".format(notify=notify,outdir=outdir,cmd=cmd,PYTHONPATH=os.getenv('PYTHONPATH'))
		print(cmd)
		subprocess.Popen(cmd,shell=True)
	else:
		print(cmd)
		popen_instance = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		popens[popen_instance] = cmd

if not qsub:
	for i in popens:
 	 stdout,stderr = i.communicate() #don't use poll() method as alternative, as docs say it may deadlock when using subprocess.PIPE
 	 if i.returncode > 0:
  	  raise Exception("Error running command {cmd}. Stdout: {stdout}\nStderr: {stderr}.".format(cmd=popens[i],stdout=stdout,stderr=stderr))
