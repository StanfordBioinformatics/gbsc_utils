from argparse import ArgumentParser
import subprocess
import os
import sys
import glob

description=""
parser = ArgumentParser(description=description)
parser.add_argument('-r','--run-dir',required=True,help="The run directory path.")
parser.add_argument('-n','--read-number',required=True,type=int,choices=(1,2),help="The read number.  Must be one of %(choices)s.")
parser.add_argument('-l','--lanes',type=int,choices=range(1,9),nargs="+",required=True,help="The lanes of in the run directory to perform the dinuc stats on.")

args = parser.parse_args()
rundir = args.run_dir
readnum = args.read_number
readnum_glob = "*_{readnum}_pf.fastq".format(readnum=readnum)
dinucExt = "_Read" + str(readnum) + "dinucDist.txt"
dinucExtGlob = "*" + dinucExt
popens = {} #dict of subprocess.Popen instances as keys and the corresponding command-line as a a key's value
for lane in range(1,9):
	lane = "L" + str(lane)
	lanedir = os.path.join(rundir,lane)
	fastqgz_glob = os.path.join(lanedir,readnum_glob + ".gz")	
	fastqgz_files = glob.glob(fastqgz_glob)
	for fqfile in fastqgz_files:
		print(fqfile)
		dirname = os.path.dirname(fqfile)
		basename =  os.path.basename(fqfile)
		outfile = os.path.join(dirname,basename.split(".")[0] + dinucExt)
		cmd = "python dinucleotideStartDistribution.py -i {fqfile} -o {outfile}".format(fqfile=fqfile,outfile=outfile)
		popen_instance = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		popens[popen_instance] = cmd

for i in popens:
	stdout,stderr = i.communicate() #don't use poll() method as alternative, as docs say it may deadlock when using subprocess.PIPE
	if i.returncode > 0:
		raise Exception("Error running command {cmd}. Stdout: {stdout}\nStderr: {stderr}.".format(cmd=popens[i],stdout=stdout,stderr=stderr))

for lane in range(1,9):
	lane = "L" + str(lane)
	landedir = os.path.join(rundir,lane)
	dinuc_files = glob.glob(os.path.join(lanedir,dinucExtGlob))
	joinedFile = "All" + dinucExt
	subprocess.check_call("python join.py -i {dinuc_files} -o {joinedFile}".format(dinuc_files=dinuc_files,joinedFile=joinedFile),shell=True) 	
