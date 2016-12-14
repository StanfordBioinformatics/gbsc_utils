from argparse import ArgumentParser

description = "Converts all carriage returns in the input file to line feeds, then writes the file to the specified output file."
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Input file.")
parser.add_argument('-o','--outfile',required=True,help="Output file.")

args = parser.parse_args()
infile = args.infile
outfile = args.outfile

fout = open(outfile,'w')
fh = open(infile,'r')
for line in fh:
	fout.write(line.replace("\r","\n"))
fout.close()
