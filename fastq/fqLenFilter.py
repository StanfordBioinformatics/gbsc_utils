###
#AUTHOR: Nathaniel Watson
###

from argparse import ArgumentParser

description = "Filters out reads of a FASTQ file whose lengths are equal to a desired value."
parser = ArgumentParser(description=description)

parser.add_argument('-i','--infile',required=True,help="Input FASTQ file.")
parser.add_argument('-o','--outfile',required=True,help="Output filtered FASTQ file.")
parser.add_argument('-f','--length-filter',type=int,required=True,help="int. specifying the length of the reads to keep.")
args = parser.parse_args()

fh = open(args.infile,'r')
fout = open(args.outfile,'w')
filtLen = args.length_filter

seqList = []
recCnt = 0
passCnt = 0
lineCnt = 0
cnt = 0
for line in fh:
	lineCnt += 1
	cnt += 1
	if cnt == 1:
		att = line
		recPos = lineCnt
		recCnt += 1
	elif cnt == 2:
		nuc = line
	elif cnt == 3:
		plus = line
	elif cnt == 4:
		qual = line
		cnt = 0
		if not att.startswith("@") or not plus.startswith("+"):
			raise ValueError("Malformed record at line number {num}.".format(num=lilneCnt))

		if len(nuc.strip()) == filtLen:
			passCnt += 1
			fout.write(att)
			fout.write(nuc)
			fout.write(plus)
			fout.write(qual)

fout.close()
fh.close()

perc = passCnt/recCnt * 100
print("Wrote {passCnt} of {recCnt} ({perc}%) reads to {outfh}.".format(passCnt=passCnt,recCnt=recCnt,perc=perc,outfh=fout.name))

