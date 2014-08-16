
###
#AUTHOR: Natheniel Watson
#DATE  : May 6, 2014

from argparse import ArgumentParser
import os
import glob

description = "Given an Illumina HiSeq sequencing run name, looks at all Unaligned* directories and merges the samplesheets into 1."
parser = ArgumentParser(description=description)
parser.add_argument('-r','--run-name',required=True,help="Name of a sequencing run (full path).")
parser.add_argument('-o','--outfile',required=True,help="Name of the output samplesheet.")

args = parser.parse_args()
run = args.run_name
outfile = args.outfile

fout = open(outfile,'w')
header = False

os.chdir(run)
for i in glob.glob(os.path.join(run,"Unaligned*")):
	if not os.path.isdir(i):
		continue
	for project in glob.glob(os.path.join(i, "Project*")):
		if not os.path.isdir(project):
			continue
		for sample in glob.glob(os.path.join(project,"Sample*")):
			if not os.path.isdir(sample):
				continue
			fh = open(os.path.join(sample,"SampleSheet.csv"),'r')
			lines = fh.readlines()
			for l in lines:
				if l.startswith("FCID"): #header line
					if not header:
						fout.write(l)
						header = True
					continue
				fout.write(l)
			fh.close()
fout.close()
			
