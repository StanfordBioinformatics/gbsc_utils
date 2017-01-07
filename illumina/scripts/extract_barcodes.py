#!/bin/env python

import os
from argparse import ArgumentParser

from gbsc_utils.illumina import Illumina

description ="Extracts the FASTQ records with the given barcodes from a FASTQ file or a pair of FASTQ files. The extracted records are written to a new pair of FASTQ files per barcode specified. Alternatively, the extracted barcodes for a pair of FASTQ files can be interleaved into a new file per barcode."

parser = ArgumentParser(description=description)
parser.add_argument("--r1",required=True,help="FASTQ file containing the (forward) reads.")
parser.add_argument("--r2",help="FASTQ file containing the reverse reads.")
parser.add_argument("--outdir",help="The pre-existing directory to output the FASTQ files containing the extracted barcodes. Defaults to the current working directory.")
parser.add_argument("--outfile-prefix",required=True,help="The file prefix of each output FASTQ file for a given barcode. The barcode name will be appended to this prefix, as well as the read number (if --interleaved is not specified). For example, setting the outfile prefix to 'output' would result in the partially formed prefix 'output_${barcode}.fastq' if --interleaved is specified, and 'output_${barcode}_R1.fastq' and 'output_${barcode}_R2.fastq' if --interleaved is not set. The output R2 FASTQ file will of course only be present if both --r1 and --r2 were set.")
parser.add_argument("-b","--barcodes",nargs="+",help="One or more barcodes to extract from the input FASTQ file(s).")
parser.add_argument("-i","--interleave",action="store_true",help="If paired-end sequencing and thus both --r1 and --r2 are specified, then adding this option indicates to output a single, interleaved FASTQ file per extracted barcode rather than separate FASTQ fies.")

FASTQ_EXT =  ".fastq"
R1 = "R1"
R2 = "R2"

args = parser.parse_args()
r1_file = args.r1
r2_file = args.r2
outdir = args.outdir
if not outdir:
	outdir = os.getcwd()
else:
	if not os.path.exists(outdir):
		raise Exception("The path {path} passed to --outdir does not exist!".format(path=outdir))

outfile_prefix = args.outfile_prefix
barcodes = [x.replace("-","+") for x in args.barcodes] 
#In the title line of Illumina FASTQ records, a duel-indexed barcode is separated with a '+', i.e. ATC+CGA.

interleave = args.interleave

if not os.path.exists(r1_file):
	raise Exception("{r1_file} provided to --r1 doesn't exist!".format(r1_file=r1_file))
if r2_file and not os.path.exists(r2_file):
	raise Exception("{r2_file} proided to --r2 doens't exist!".format(r2_file=r2_file))

r1_records = Illumina.fastqParse(fastq=r1_file,extract_barcodes=barcodes)
r2_records = {}
if r2_file:
	r2_records = Illumina.fastqParse(fastq=r2_file,barcodes=barcodes)

file_handles = {}
for barcode in barcodes:
	file_handles[barcode] = {}
	outfile_name = os.path.join(outdir,outfile_prefix + "_" + barcode.replace("+","-"))
	if interleave:
		outfile_name += FASTQ_EXT
	else:
		outfile_name += "_" + R1 + FASTQ_EXT
	file_handles[barcode][R1] = open(outfile_name,"w")
	if not interleave:
		file_handles[barcode][R2] = open(outfile_name.replace(R1,R2),"w")

output_barcode_counts = {}
for barcode in barcodes:
	output_barcode_counts[barcode] = 0

def format_rec_for_output(rec_id,rec):
	return "\n".join([rec_id,rec["seq"],"+",rec["qual"]]) + "\n"

for rec_id in r1_records:
	record = r1_records[rec_id]
	barcode = record["header"]["barcode"]
	if r2_records:
		rec_2_id = Illumina.get_pairedend_read_id(read_id=rec_id)
		try:
			record_2 = r2_records[rec_2_id]
		except KeyError:
			print("Warning: Found foward read {rec_id} but not reverse read {rec_2_id}. Skipping".format(rec_id=rec_id,rec_2_id=rec_2_id))
			continue
	file_handles[barcode][R1].write(format_rec_for_output(rec_id,record))
	if r2_records and interleave:
		file_handles[barcode][R1].write(format_rec_for_output(rec_2_id,record_2))	
	elif r2_records:
		file_handles[barcode][R2].write(format_rec_for_output(rec_2_id,record_2))	
	output_barcode_counts[barcode] += 1
	
for barcode in file_handles:
	for output_key in file_handles[barcode]:
		file_handles[barcode][output_key].close()

print("Output Statistics")
for barcode in output_barcode_counts:
	print(barcode + ": " + str(output_barcode_counts[barcode]))


