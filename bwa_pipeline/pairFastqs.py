
import os
import glob
import re

from argparse import ArgumentParser

laneDirReg = re.compile(r'^L\d+$')
forwardSuffix = "_1_pf.fastq"
reverseSuffix = "_2_pf.fastq"

def getFastqs(path,whichRead):
	"""
	Function : Retuns the paths to all the forward FASTQ or reverse FASTQ files.
	Args     : path - The directory path containing the FASTQ files. 
	           which Read - either 'forward' or 'reverse'.
	Returns  : list.
	"""
	if whichRead == "forward":
		suffix = forwardSuffix
	elif whichRead == "reverse":
		suffix = reverseSuffix
	else:
		raise Exception("Incorrect value for 'whichRead' argument. Must be one of ['forward','reverse'].")
	globPath = os.path.join(path,"*" + suffix)
	res = glob.glob(globPath)
	if not res:
		globPath += ".gz"
		res = glob.glob(globPath)
	return res

def pairFastqs(forwards,reverses):
	pairs = {}
	for f in forwards:
		base_f = f.rstrip(".gz").rstrip(forwardSuffix)
		for r in reverses:
			base_r = r.rstrip(".gz").rstrip(reverseSuffix)
			if base_f == base_r:
				pairs[f] = r
		if f not in pairs:
			raise Exception("Could not find a reverse reads FASTQ file to match {f}.".format(f=f))
	return pairs
	

description = ""
parser = ArgumentParser(description=description)
parser.add_argument("--rundir",required=True,help="Path to the sequencing results directory that has a lane subdirectory of the form L# for each lane, where # is the number of the lane. The FASTQS must exist within the lane directory, and may be gzip'd.")
parser.add_argument("-o","--outfile",required=True,help="The output file containing the following columns: 1) Path to the forward reads FASTQ file, 2) Path to the reverse reads file, 3) Path to the output SAM file.")
parser.add_argument("--lanes",nargs="+",help="The lane numbers to map. The default is all lanes found within the --rundir.")

args = parser.parse_args()
rundir = args.rundir
outfile = args.outfile
fout = open(outfile,'w')
lanes = args.lanes
os.chdir(rundir)
for laneDir in os.listdir("."):
	if not os.path.isdir(laneDir):
		continue
	if laneDirReg.match(laneDir):
		if lanes:
			if not laneDir.lstrip("L") in lanes:
				continue
		bwaDir = os.path.join(rundir,"bwa_mem")
		if not os.path.exists(bwaDir):
			os.mkdir(bwaDir)
		bwaLaneDir = os.path.join(bwaDir,laneDir)
		if not os.path.exists(bwaLaneDir):
			os.mkdir(bwaLaneDir)
		readsDir = os.path.join(rundir,laneDir)
		forwards = getFastqs(path=readsDir,whichRead="forward")
		reverses = getFastqs(path=readsDir,whichRead="reverse")
		pairs = pairFastqs(forwards,reverses)
		for i in pairs:
			samFile = os.path.join(bwaLaneDir,os.path.basename(i).rstrip(".gz").rstrip(forwardSuffix) + ".sam")
			fout.write(i + "\t" + pairs[i] + "\t" + samFile + "\n")
fout.close()


