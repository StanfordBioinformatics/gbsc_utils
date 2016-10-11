#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stanford.edu
#2016-10-10
###

from argparse import ArgumentParser
import os

from gbsc_utils.fastq import fastq_utils

description = "De-interleaves an interleaved Illumina FASTQ file. The separated files will be written to the specified output directory. The forward reads file will be named the same as the interleaved file, but with '_1' added prior to the file suffix. The reverse reads FASTQ file will have '_2' added prior to the file extension."
parser = ArgumentParser(description=description)
parser.add_argument('-i',"--infile",required=True,help="The interleaved FASTQ file.")
parser.add_argument('-o',"--outdir",required=True,help="The output directory. If the directory doesn't already exist, it will be recursively created.")

args = parser.parse_args()
outdir = args.outdir
if not os.path.isdir(outdir):
	os.makedirs(outdir)

infile = args.infile
infile_basename = os.path.basename(infile)
infile_ext = os.path.splitext(infile_basename)[1]

forward_outfile = os.path.splitext(infile_basename)[0] + "_1" + infile_ext
forward_outfile = os.path.join(outdir,forward_outfile)
forward_fout = open(forward_outfile,'w')
reverse_outfile = os.path.splitext(infile_basename)[0] + "_2" + infile_ext
reverse_outfile = os.path.join(outdir,reverse_outfile)
reverse_fout = open(reverse_outfile,'w')

read_num_cycle = 0

def processRec(rec):
	global forward_fout
	global reverse_fout
	global read_num_cycle
	att_line_dict = fastq_utils.parseIlluminaFastqAttLine(rec[0])
	read_num = int(att_line_dict["readNumber"])
	if read_num_cycle == read_num:
		raise Exception("Read {att_line} with read number {read_num} was preceeded by a record with the same read number.".format(att_line=rec[0],read_num=read_num))
	read_num_cycle = read_num
	if read_num == 1:
		forward_fout.write("".join(rec))
	else:
		reverse_fout.write("".join(rec))

line_count = 0
rec = []
fh = open(infile,'r')
for line in fh:
	line_count += 1
	rec.append(line)
	if line_count == 4:
		line_count = 0
		processRec(rec)
		rec = []
	
forward_fout.close()
reverse_fout.close()
