from argparse import ArgumentParser
import time
import fastq_utils

NUCLEOTIDES = "ACTGN"
parser = ArgumentParser()
parser.add_argument('-i','--infile',required=True,help="Input FASTQ file.")
parser.add_argument('-b','--barcodes',nargs="+",required=True,help="One or more case-insensitive and space-separated barcodes; i.e. ATGCAG TGACTC")
parser.add_argument('-p','--prefix',default=time.time(),help="The prefix of each output file name. Each output file is named prefix_barcode.fq, where prefix is the prefix gien here and barcode is one of the barcode sequences givein in --barcodes. Defaults to a timestamp.")

args = parser.parse_args()
prefix = str(args.prefix)

infile = args.infile
barcodes = [x.upper() for x in args.barcodes]
for barcode in barcodes:
	for nuc in barcode:
		if nuc not in NUCLEOTIDES:
			parser.error("Error - Barcode {barcode} contains invalid character {nuc}. Each nucleotide in the barcode must be one of {nucleotides}.".format(barcode=barcode,nuc=nuc,nucleotides=NUCLEOTIDES))

now = time.time()
fileHandles = {}
for i in barcodes:
	fileHandles[i] = open(prefix + "_" + i + ".fq",'w')
gen = fastq_utils.parse(infile)
for rec in gen:
	attLine = rec[0]
	barcode = attLine.split(":")[-1]
	if barcode in barcodes:
		fastq_utils.writeRec(fileHandles[barcode],rec)	
for key in fileHandles:
	fh = fileHandles[key]
	if fh.tell() == 0:
		fh.close()
		os.rm(fh.name)
