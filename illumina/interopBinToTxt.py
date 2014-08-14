###
#AUTHOR: Nathaniel Watson
###

from illumina import interop
from argparse import ArgumentParser

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-i','--interop-file',required=True,help="The input interop file. Currenlty only ExtractionMetricsOut.bin and CorrectedIntMetricsOut.bin are supported.")
parser.add_argument('-m','--metric',choices=interop.RawIntensities.metricFiles,required=True,help="The type of interop file.")
parser.add_argument('-o','--outfile',help="Output file name. Defaults to same name as --input but with the addition of the extension '.txt'.") 

args = parser.parse_args()

metric = args.metric
infile = args.interop_file
outfile = args.outfile
if not args.outfile:
	outfile = infile + ".txt"


ob = interop.RawIntensities(metric=metric,infile=infile)
ob.writeRecs(outfile)
