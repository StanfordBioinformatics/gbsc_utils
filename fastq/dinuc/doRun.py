#!/usr/bin/env python

from argparse import ArgumentParser
import subprocess
import os
import sys
import glob

description=""
parser = ArgumentParser(description=description)
parser.add_argument('-r','--run-dir',required=True,help="The run directory path.")
parser.add_argument('-n','--read-number',required=True,type=int,choices=(1,2),help="The read number.  Must be one of %(choices)s.")

args = parser.parse_args()
print("howdy")
rundir = args.run_dir
readnum = args.read_number
readnum_glob = "*_{readnum}_pf.fastq".format(readnum=readnum)
popens = {} #dict of subprocess.Popen instances as keys and the corresponding command-line as a a key's value
for lane in range(1,8):
	print(lane)
	lane = "L" + str(lane)
	lanedir = os.path.join(rundir,lane)
	fastq_glob,fastqgz_glob = os.path.join(lanedir,readnum_glob),os.path.join(lanedir,readnum_glob + ".gz")	
	fastq_files,fastqgz_files = glob.glob(fastq_glob), glob.glob(fastqgz_glob)
	for fqfile in fastq_files + fastqgz_files:
		print(fqfile)
		dirname = os.path.dirname(fqfile)
		basename =  os.path.basename(fqfile)
		outfile = os.path.join(dirname,basename.split(".")[0] + "_dinucDist.txt")
		cmd = "python dinucleotideStartDistribution.py -i {fqfile} -o {outfile}".format(fqfile=fqfile,outfile=outfile)
		popen_instance = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		popens[popen_instance] = cmd

for i in popens:
	stdout,stderr = i.communicate() #don't use poll() method as alternative, as docs say it may deadlock when using subprocess.PIPE
	if i.returncode > 0:
		sys.stderr.write("Error running command {cmd}. Stdout: {stdout}\nStderr: {stderr}.".format(cmd=popens[i],stdout=stdout,stderr=stderr))
	
