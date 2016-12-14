#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stanford.edu
#Paul Billing-Ross
#pbilling@stanford.edu
###

import os
import sys
import time

from argparse import ArgumentParser
from gbsc_utils.fastq import fastq_utils

NUCLEOTIDES = "ACTGN"
FORWARD = "forward"
REVERSE = "reverse"

def parse_args(args):

    description = ("Parses the given barcoded samples out of a FASTQ file. " +
                  "Supports interleaving of paired-end reads when " + 
                  "--reads2-file is specified.")
    parser = ArgumentParser(description=description)
    parser.add_argument(
                        "--reads-file", 
                        required = True, 
                        help = "Required FastQ file. For PE sequencing, " + 
                               "this is the forward reads file.")
    parser.add_argument(
                        "--reads2-file", 
                        required = False,
                        help = "If paired-end, the reverse reads FASTQ file.")
    parser.add_argument(
                        "-b", 
                        "--barcodes", 
                        nargs = "+", 
                        required = True,
                        help = "Required. One or more case-insensitive and " + 
                               "space-separated barcodes (i.e. ATGCAG TGACTC).")
    parser.add_argument(
                        "-p",
                        "--prefix", 
                        default = time.time(), 
                        help = "The prefix of each output file name (excluding " +
                               "the directory path). Each output file is named " +
                               "prefix_barcode.fq, where prefix is the prefix " + 
                               "given here and barcode is one of the barcode " +
                               "sequences givein in --barcodes. Defaults to a timestamp.")
    parser.add_argument(
                        "-o", 
                        "--outdir", 
                        required = True,
                        help = "The output directory.")

    args = parser.parse_args(args)
    return args

#Remove empty barcode files
def rm_empty_output_files(read_direction):
	for barcode in file_handles:
		fh = file_handles[barcode][read_direction]
		if fh.tell() == 0:
			fh.close()
			os.remove(fh.name)
		else:
			fh.close()

args = parse_args(sys.argv[1:])
prefix = str(args.prefix)
freads_file = args.reads_file
rreads_file = args.reads2_file
outdir = args.outdir

if not os.path.exists(outdir):
	os.mkdir(outdir)

barcodes = [x.upper() for x in args.barcodes]
for barcode in barcodes:
	for nuc in barcode:
		if nuc not in NUCLEOTIDES:
			parser.error("Error - Barcode {barcode} contains invalid character {nuc}. Each nucleotide in the barcode must be one of {nucleotides}.".format(barcode=barcode,nuc=nuc,nucleotides=NUCLEOTIDES))

now = time.time()
bufsize = 0
file_handles = {}
for i in barcodes:
	file_handles[i] = {}
	fastq_file_path = os.path.join(outdir,prefix + "_" + i + "_R1.fastq")
	file_handles[i][FORWARD] = open(fastq_file_path,'w', bufsize)
	if rreads_file:
		reverse_fastq_file_path = os.path.join(outdir,prefix + "_" + i + "_R2.fastq")
		file_handles[i][REVERSE] = open(reverse_fastq_file_path,"w", bufsize)

fread_gen = fastq_utils.indexparse(freads_file, index=False)
for fread in fread_gen:
	attLine = fread[0]
	barcode = attLine.split(":")[-1]
	if barcode in barcodes:
		fastq_utils.writeRec(file_handles[barcode][FORWARD], fread)
if rreads_file:
    rread_gen = fastq_utils.indexparse(rreads_file, index=False)
    for rread in rread_gen:
	    attLine = rread[0]
	    barcode = attLine.split(":")[-1]
	    if barcode in barcodes:
		    fastq_utils.writeRec(file_handles[barcode][REVERSE], rread)

rm_empty_output_files(FORWARD)
if rreads_file:
    rm_empty_output_files(REVERSE)
