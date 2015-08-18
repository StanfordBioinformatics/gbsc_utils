###
#AUTHOR: Nathaniel Watson
###

from gbsc_utils.illumina.Illumina import SampleSheetMiSeqToHiSeq
import argparse


parser = argparse.ArgumentParser(description="Howdy")
parser.add_argument('-i','--infile',required=True,help="The MiSeq SampleSheet")
parser.add_argument('-o','--outfile',required=True,help="HiSeq SampleSheet name")
args = parser.parse_args()

infile = args.infile
outfile = args.outfile

m = SampleSheetMiSeqToHiSeq(infile)
m.convert(outfile)
