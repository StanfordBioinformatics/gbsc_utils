#!/usr/bin/env python

###
#2016-12-16
#Nathaniel Watson
#nathankw@stanford.edu
###

from argparse import ArgumentParser

description = "Given some search criteria, finds and prints the absolute paths to FASTQ files on the cluster (pre-DNAnexus)."
parser = ArgumentParser(description=description)
parser.add_argument("-i","--infile",required=True,help="Tab-delimited input file containing the columns 1) UHTS run name, 2) lane, and 3) barcode.")

args = parser.parse_args()
infile = args.infile

from gbsc_utils.SequencingRuns import runPaths
fh = open(infile)
for line in fh:
	line = line.strip().split("\t")
	if not line:
		continue
	fastqs = runPaths.findFastqs(line[0],line[1],line[2])
	if not fastqs:
		raise Exception("Could not find fastqs")
	for f in fastqs:
		print(f)
