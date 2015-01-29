#!/usr/bin/env python
import subprocess
from argparse import ArgumentParser
import fastq_utils as f
import os

description = "hi"
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The white-space delimited input file where the first two columns are the forward read file name and the reverse the reverse read fastq file name. If the --interleave option is used, then the 3rd column must be the interleaved output file name.")
parser.add_argument('-c','--compress-output',choices=("gzip","bz2"),help="Compress the output with selected method. For GZIP compression, the extension will be set to '.gzip', and for BZ2 it will be '.bz2'.")
parser.add_argument('--interleave',action="store_true",help="Presence of this option indicates to interleave each pair of forward and reverse read files. In this case, the 3rd column in the input file must be the interleave output file name.")
parser.add_argument('--qsub',action="store_true",help="Presence of this option indicates to run the jobs through qsub. Also set --notify argument when using this.")
parser.add_argument('-n','--notify',help="An email address for OGE notifications for job end and abort. Only makes sense to use with the --qsub argument, and is required to use this argument with --qsub.")
parser.add_argument('-w','--working-directory',help="The working directory to use with QSUB where all stdout and stderr files will be written. Required when using --qsub.")

#peExt variable below is for the extension to be used for output files when interleaving isn't requested.
# I call this format semi-interleaved, which is when a pair of read files are ordered the same and don't have any singleton reads.
peExt = "_semi-interleaved.fastq"
args = parser.parse_args()
interleave = args.interleave
infile = args.infile
qsub = args.qsub
notify = args.notify
wd = args.working_directory
if qsub and not notify:
	parser.error("You must also specify the --notify argument when using --qsub!")
if qsub and not wd:
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
	cmd="outputPairedEndReads.py -f {f} -r {r}"
	if interleave:
		iout = line[2]
		cmd += "--iout {iout} ".format(iout=iout) 
	cmd="outputPairedEndReads.py -f {f} -r {r} "
	else:
		fout = f.rsplit(".") + peExt
		rout = r.rsplit(".") + peExt
		cmd += "--fout {fout} --rout {rout} ".format(fout=fout,rout=rout)
	if qsub:
		subprocess.call("qsub -R y -l h_vmem=10G -m ea -M {notify} -wd {wd} {cmd}".format(notify=notify,wd=wd,cmd=cmd)
	else:
		popen_instance = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		popens[popen_instance] = cmd

if not qsub:
	for i in popens:
 	 stdout,stderr = i.communicate() #don't use poll() method as alternative, as docs say it may deadlock when using subprocess.PIPE
 	 if i.returncode > 0:
  	  raise Exception("Error running command {cmd}. Stdout: {stdout}\nStderr: {stderr}.".format(cmd=popens[i],stdout=stdout,stderr=stderr))
