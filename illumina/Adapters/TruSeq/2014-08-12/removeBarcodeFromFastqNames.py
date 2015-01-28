import os
import glob
from argparse import ArgumentParser

description="hi"
parser = ArgumentParser(description=description)
parser.add_argument('-d','--directory',help="The directory containing the FASTQ files. Only FASTQ files present with a .fastq or .fastq.gz extension will be found.")
args = parser.parse_args()

directory = args.directory

for i in glob.glob(os.path.join(directory,"*.fastq")) +  glob.glob(os.path.join(directory,"*.fastq.gz")):
	basename = os.path.dirname(i)
	fq = os.path.basename(i)
	newFq = fq.split("_")
	newFq = newFq[0:2] + newFq[3:]
	newFq = "_".join(newFq)
	newfilename = os.path.join(basename,newFq)
	os.rename(i,newfilename)
