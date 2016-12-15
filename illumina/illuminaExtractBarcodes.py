#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stanford.edu
###

from argparse import ArgumentParser
import time
import os
from gbsc_utils.fastq import fastq_utils


NUCLEOTIDES = "ACTGN+"
#Note I add the '+' above b/c Illumina duel-indexed barcodes are separated by '+' in the header line of a FASTQ record, i.e. ATC+CAG.
FORWARD = "forward"
REVERSE = "reverse"

description = "Parses the given barcoded samples out of a FASTQ file. Supports interleaving of paired-end reads when --reads2-file is specified."
parser = ArgumentParser(description=description)
parser.add_argument("--reads-file",required=True,help="Required. The FASTQ file. For PE sequencing, this is the forward reads file.")
parser.add_argument("--reads2-file",help="If paired-end, the reverse reads FASTQ file.")
parser.add_argument("-b","--barcodes",nargs="+",required=True,help="Required. One or more case-insensitive and space-separated barcodes; i.e. ATGCAG TGACTC")
parser.add_argument("-p","--prefix",default=time.time(),help="The prefix of each output file name (excluding the directory path). Each output file is named prefix_barcode.fq, where prefix is the prefix given here and barcode is one of the barcode sequences givein in --barcodes. Defaults to a timestamp.")
parser.add_argument("-o","--outdir",required=True,help="The output directory.")

args = parser.parse_args()
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
file_handles = {}
for i in barcodes:
	file_handles[i] = {}
	fastq_file_path = os.path.join(outdir,prefix + "_" + i + "_1.fastq")
	file_handles[i][FORWARD] = open(fastq_file_path,'w')
	if rreads_file:
		reverse_fastq_file_path = os.path.join(outdir,prefix + "_" + i + "_2.fastq")
		file_handles[i][REVERSE] = open(reverse_fastq_file_path,"w")

freads_fh, freads = fastq_utils.fileseek_hash(freads_file)
rreads = {}
if rreads_file:
	rreads_fh, rreads = fastq_utils.fileseek_hash(rreads_file)

for seqid in freads:
	start,end = freads[seqid]
	freads_fh.seek(start)
	forward_rec = freads_fh.read(end - start).split("\n")
	#forward_rec is a list of the 4 elements ["attLine", "sequence string", "+" ,"quality string"]
	attLine = forward_rec[0]
	barcode = attLine.split(":")[-1]
	if barcode in barcodes:
		fastq_utils.writeRec(file_handles[barcode][FORWARD],forward_rec)	
		if rreads:
			start,end = rreads[seqid]
			rreads_fh.seek(start)
			reverse_rec = rreads_fh.read(end - start).split("\n")
			fastq_utils.writeRec(file_handles[barcode][REVERSE],reverse_rec)

#Remove empty barcode files
def rm_empty_output_files(read_direction):
	for barcode in file_handles:
		fh = file_handles[barcode][read_direction]
		if fh.tell() == 0:
			fh.close()
			os.remove(fh.name)
		else:
			fh.close()
	
rm_empty_output_files(FORWARD)
rm_empty_output_files(REVERSE)

freads_fh.close()
if rreads:
	rreads_fh.close()
