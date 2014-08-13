###
#AUTHOR: Nathaniel Watson
###

from argparse import ArgumentParser

description = "Filters out reads of a FASTA file whose lengths are equal to a desired value."
parser = ArgumentParser(description=description)

parser.add_argument('-i','--infile',required=True,help="Input FASTA file.")
parser.add_argument('-o','--outfile',required=True,help="Output filtered FASTA file.")
parser.add_argument('-f','--length-filter',required=True,help="int. specifying the length of the reads to keep.")
args = parser.parse_args()

fh = open(args.infile,'r')
fout = open(args.outfile,'w')
filtLen = args.length_filter

att = fh.readline().strip()
if not att.startswith(">"):
	raise ValueError("Invalid FASTA file. Expected first line to start with '>'.")

seqLen = 0
seqList = []
recCnt = 1
passCnt = 0
for line in fh:
	line = line.strip()
	if not line:
		continue
	if line.startswith(">"):
		recCnt += 1
		if seqLen == filtLen:
			passCnt += 1
			fout.write(att + "\n")
			for i in seqList:
				fout.write(i + "\n")
		seqList = []
		seqLen = 0
		att = line
	else:
		seqList.append(line)
		seqLen += len(line)	
fout.close()
fh.close()

perc = passCnt/recCnt * 100
print("Wrote {passCnt} of {recCnt} ({perc}%) reads to {outfh}.".format(passCnt=passCnt,recCnt=recCnt,perc=perc,outfh=fout.name))

