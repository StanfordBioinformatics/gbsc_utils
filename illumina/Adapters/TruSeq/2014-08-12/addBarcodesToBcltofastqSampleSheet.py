import os
from argparse import ArgumentParser

description="hi"
parser = ArgumentParser(description=description)
parser.add_argument('-s','--sample-sheet',required=True,help="The samplesheet to write to. If the file exists already, sample lines will be appended (the header line must be the first line also). Otherwise, when writing to a new file the header line will be added first.")
parser.add_argument('-b','--barcode-file',required=True,help="File containing the barcodes to add to the samlesheet. Format is tab-delimited. The first field is an integer that identifies the barcode id, the second is the barcode sequence. Any additional fields will be ignored.")
parser.add_argument('-p','--project',required=True,help="The project to which all samples belong. Technically there can be a different project for each sample, but for simplicity that isn't supported (yet).")
parser.add_argument('-o','--operator',required=True,help="The person who entity that owns the run data. Will serve as the 'operator' field of the samplesheet.")

args = parser.parse_args()
ss = args.sample_sheet
project = args.project
operator = args.operator
headerLine = "FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,Project\n" #see the bcl2fastq user guide for these fields
if os.path.exists(ss):
	fout = open(ss,'a')
else:
	fout = open(ss,'w')
	fout.write(headerLine)

fh = open(args.barcode_file,'r')
sampleId = 0 #Note that I won't use 0 itself as this is reserved for the FASTQ file that contains unmatched reads.
for line in fh:
	line = line.strip()
	if not line:
		continue
	line = line.split()
	barcode = line[1]
	sampleId += 1
	
	fout.write(",1,{barcode}_S{sampleId},,{barcode},,N,,{operator},{project}\n".format(barcode=barcode,sampleId=sampleId,operator=operator,project=project))

#now create entry for unknown reads
fout.write(",1,{Undetermined}_S0,,,,,N,,{operator},{project}\n".format(barcode=barcode,sampleId=sampleId,operator=operator,project=project))
fout.close()
