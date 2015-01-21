import os
from argparse import ArgumentParser

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',help="The input dinuc stats file. Format is two tab-delimited fields, where the first field is the dinucleotide and the second field is the frequency. Must contain a header line as the very first line, or else the first data line will be read past.")
args = parser.parse_args()

fh = open(args.infile,'r')
header = fh.readline().strip().split()
newheader = header[::] + ["RelativeFreq"]
freqs = {}
for line in fh:
	line = line.strip()
	if not line:
		continue
	line = line.split()
	dinuc = line[0]
	freq = int(line[1])
	freqs[dinuc] = freq
	
tot = float(sum(freqs.values()))
relatFreqs = {}
for dinuc in freqs:
	relfreq = (freqs[dinuc]/tot) * 100
	relatFreqs[dinuc] = relfreq

fh.close()
outfileName = fh.name + "perc.txt"
fout = 	open(outfileName,'w')
fout.write("\t".join(newheader) + "\n")

for dinuc in relatFreqs:	
	relfreq = relatFreqs[dinuc]
	fout.write("{dinuc}\t{freq}\t{relfreq:>.2f}%\n".format(dinuc=dinuc,freq=freqs[dinuc],relfreq=relfreq))
fout.write("\n")
fout.write("Total Reads: {tot:,}\n".format(tot=int(tot)))

fout.close()
os.rename(fout.name,fh.name)
