###
#AUTHOR: Nathaniel Watson
###


from argparse import ArgumentParser
from Bio import SeqIO
import sys,os
import gzip,bz2

def fileExists(path):
	if not os.path.exists(path):
		raise OSError("File {path} does not exist!".format(path=path))
	return path

def interleave(iter1, iter2) :
	while True :
		yield iter1.next()
		yield iter2.next()

GZIP="gzip"
BZ2="bz2"

description = "Interleaves paired-end reads using BioPython. Accepts one forward read file (F) and one reverse read file (R). Reads are interleaved based on the order they appear - F1 with R1, F2 with R2, and so on. Accepts uncompressed input as well as gzip (file extension must be either .gz or .gzip) and bz2 (file extension must be .bz2) compressed input."
parser = ArgumentParser(description=description)
parser.add_argument('--forward',required=True,help="The forward reads file.")
parser.add_argument('--reverse',required=True,help="The reverse reads file.")
parser.add_argument('--format',choices=("fasta","fastq"),default="fastq",help="The format of the input reads. Default is %(default)s.")
parser.add_argument('--outfile',required=True,help="Interleaved output filename.")
parser.add_argument('--compress-output',choices=(GZIP,BZ2),help="Compress the output with selected method.")

args = parser.parse_args()
left = fileExists(args.forward.strip())
right = fileExists(args.reverse.strip())
outfile = args.outfile
format = args.format

compress = args.compress_output
if compress:
	if compress == GZIP:
		fout = gzip.open(outfile,'w')
	elif compress == BZ2:
		fout = bz2.BZFile(outfile,'w')
else:
	fout = open(args.outfile,'w')

records = interleave(SeqIO.parse(left, format), SeqIO.parse(right, format))
count = SeqIO.write(records, fout, format)
fout.close()

print("Interleaved {count} sequence records.".format(count=count))
