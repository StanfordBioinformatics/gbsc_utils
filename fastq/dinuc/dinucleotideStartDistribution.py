import fastq_utils

from argparse import ArgumentParser

description="hi"
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="Input FASTQ file. Can be gzip'd with a .gz extension.")
parser.add_argument('-o','--outfile',required=True,help="Output file name.")

args = parser.parse_args()
infile = args.infile
outfile = args.outfile
index = fastq_utils.parse(infile)
dico = {}
for rec in index:
	key = rec[1][:2] #the first two bases of the sequence
	if key not in dico:
		dico[key] = 0
	dico[key] += 1

totReads = sum(dico.values())
fout = open(outfile,'w')
fout.write("Dinucleotide\tCount\n")
for key in sorted(dico.keys()):
	fout.write("{key}\t{val}\n".format(key=key,val=dico[key]))	

fout.write("\n")
fout.write("Total Reads: {totReads}\n".format(totReads=totReads))
fout.close()
	

