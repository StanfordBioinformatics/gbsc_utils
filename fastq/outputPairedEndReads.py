#!/srv/gs1/software/python/python-2.7/bin/python
from argparse import ArgumentParser
import fastq_utils as f
import os

#Illumina FASTQ format is 
# @<instrument-name>:<run ID>:<flowcell ID>:<lane>:<tile>:<x-pos>:<y-pos> <read number>:<is filtered>:<control number>:<barcode sequence>

def compressWriteFh(outfileName,format):
	"""
	Function : Creates an output file handle that is either a regular stream, a GZIP stream, or a BZ2 stream, depending on the value of the format field.
		         Will add the appropriate compression extension if it doesn't exist already to the outfileName, which for GZIP is '.gzip' and for 
 						 BZ2 is '.bz2'.
	Args     : format - one of [gzip,bz2]
	"""
	if format == "gzip":
		if not outfileName.endswith(".gzip"):
			outfileName += ".gzip"
		fout = gzip.open(outfileName,'w')
	elif compress == "bz2":
		if not outfileName.endswith(".bz2"):
			outfileName += ".bz2"
		fout = bz2.BZFile(outfileName,'w')
	else:
		fout = open(outfileName,'w')
	return fout


description="Given two paired-end reads files in FASTQ format, where one contains the forward reads and the other the reverse, outputs either an interleaved FASTQ file or two separate ordered FASTQ files. There are two reasons for wanting to do the latter: 1) To get rid of the singleton reads, and 2) The reads are out of order. Out of order means that the ordering of reads in one FASTQ file isn't the same as those in the other FASTQ file."
parser = ArgumentParser(description=description)
parser.add_argument('-f','--forward',required=True,help="The forward reads file.")
parser.add_argument('-r','--reverse',required=True,help="The reverse reads file.")
parser.add_argument('--fout',help="The forward reads output file name. When using this, also specify --rout. Can't be used with the -iout option.")
parser.add_argument('--rout',help="The reverse reads output file name. When using this, also specify --fout. Can't be used with the -iout option.")
parser.add_argument('--iout',help="The interleaved output file name. Can't be used with either of the --fout or --rout options.")
#parser.add_argument('--format',choices=("fasta","fastq"),default="fastq",help="The format of the input reads. Default is %(default)s.")
parser.add_argument('-c','--compress-output',choices=("gzip","bz2"),help="Compress the output with selected method.")

args = parser.parse_args()
if not args.fout and not args.rout and not args.iout:
	parser.error("You must supply either the --iout option or both the --fout and --rout options!")
if args.fout and not args.rout:
	parser.error("You must supply the --rout option with the --fout option!")
if args.rout and not args.fout:
	parser.error("You must supply the --fout option with the --rout option!")
if args.fout and args.iout:
	parser.error("The --iout option cannot be used with the --fout option!")
if args.rout and args.iout:
	parser.error("The --iout option cannot be used with the --rout option!")

compressFormat = args.compress_output
forward = args.forward.strip()
reverse = args.reverse.strip()
forwardOut = args.fout
reverseOut = args.rout
interleavedOut = args.iout
for infile in forward,reverse:
	if not os.path.exists(infile):
		raise OSError("Input file {} does not exist!".format(infile))
outfileNames = {}
if interleavedOut:
	outfileNames['iout'] = interleavedOut
else:
	outfileNames['fout'] = forwardOut
	outfileNames['rout'] = reverseOut

outfileHandles = {}
for outfile in outfileNames:
	if compressFormat:
		outfileHandles[outfile] = compressWriteFh(outfileNames[outfile],compressFormat)
	else:
		outfileHandles[outfile] = open(outfileNames[outfile],'w')

forwardIndex = f.mem(forward)
reverseIndex = f.mem(reverse)

if not interleavedOut:
	forwardFout = outfileHandles['fout']
	reverseFout = outfileHandles['rout']
	for seqid in forwardIndex:
		if seqid in reverseIndex:
			forwardFout.write(forwardIndex[seqid])
			reverseFout.write(reverseIndex[seqid])
	forwardFout.close()
	reverseFout.close()
else:
	interleavedFout = outfileHandles['iout']
	for seqid in forwardIndex:
		if seqid in reverseIndex:
			interleavedFout.write(forwardIndex[seqid])
			interleavedFout.write(reverseIndex[seqid])
	interleavedFout.close()
