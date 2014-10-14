import fasta
from argparse import ArgumentParser
from operator import itemgetter

description = ""
parser = ArgumentParser(description)
parser.add_argument('-i','--infile',required=True,help="Input FASTA file")
parser.add_argument('-n','--name',required=True,help="The record name in the FASTQ file for which motif frequencies are to be calculated.")
parser.add_argument('-d','--dinucleotide',action="store_true",help="Presence of this option indicates that all dinucleotide frequencies will be calculated for --name in --infile.")

args = parser.parse_args()
recName = args.name
infile = args.infile
index = fasta.ByteIndex(infile)
rawRecord = index.getRawRecord(recName)
record = fasta.Rec(rawRecord)
#record.printRecord(recName,50)
dico = record.dinucleotideFreqs()
for i in sorted(dico.items(),key=itemgetter(1),reverse=True):
	print(i[0] + ": " + str(i[1]))




