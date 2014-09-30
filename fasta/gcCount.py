
from argparse import ArgumentParser

description = ""
parser = ArgumentParser(description)
parser.add_argument('-i','--outfile',required=True,help="Input FASTA file")

args = parser.parse_args()
infile = args.infile
fh = open(infile,'r')

