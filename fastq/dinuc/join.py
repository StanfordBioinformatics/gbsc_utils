
from argparse import ArgumentParser
import operator

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infiles',nargs="+",required=True,help="One or more input dinucleotide stats file that is tab-delimited, and where the first column is the dinculeotide, the second the frequency. Header line must be included as the first line in the input file, otherwise a dataline may be skipped in the processing. The last non-empty line must be the line that gives the total number of reads and begins with 'Total'.")
parser.add_argument('-o','--outfile',required=True,help="The merged stats output file.")
args = parser.parse_args()
outfile = args.outfile
infiles = args.infiles
dico = {}
for i in infiles:
	fh = open(i,'r')
	fh.readline() #read off header line
	for line in fh:
		if line.lower().startswith("total"):
			break
		line = line.strip()
		if not line:
			continue
		line = line.split("\t")
		dinuc = line[0]
		freq = int(line[1])
		if dinuc not in dico:
			dico[dinuc] = freq
		else:
			dico[dinuc] += freq
	fh.close()

totReads = float(sum(dico.values()))
percDico = {}
for dinuc in dico:
	freq = dico[dinuc]
	perc = (freq/totReads) * 100	
	percDico[dinuc] = perc
#print(percDico)	
fout = open(outfile,'w')
fout.write("Dinucleotide\tFreq\tRelativeFreq\n")
for dinuc,perc in sorted(percDico.items(),key=operator.itemgetter(1),reverse=True):
	fout.write("{dinuc}\t{freq}\t{perc:.2f}%\n".format(dinuc=dinuc,freq=dico[dinuc],perc=perc))	

fout.write("\n")
fout.write("Total Reads: {totReads}\n".format(totReads=int(totReads)))
fout.close()
