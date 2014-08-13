###
#AUTHOR: Nathaniel Watson
###

from argparse import ArgumentParser

description = "Given two files containing row-by-row records whose fields are delimited by a specified delimiter, copies selected fields from the donor file to the receiver file where the primary keys between files match."
parser = ArgumentParser(description)
parser.add_argument('-r','--receiver',required=True,help="The file to which fields are added. A field-header must be present and at the first line.")
parser.add_argument('-d','--donor',required=True,help="The file donating fields to the receiver. A field-header must be present and at the first line.")
parser.add_argument('--rkey',required=True,help="Comma-separated list of field names (case-insensitive) that form the primary key in the receiver file.")
parser.add_argument('--dkey',required=True,help="Comma-separated list of field names (case-insensitive) that form the primary key in the donor file.")
parser.add_argument('--fields',required=True,help="Comma-separated list of field names (case-insensitive) in the donor to transfer to the receiver.")
parser.add_argument('--sep',default="\t",help="The delimiter separating fields in the input files. Default is '\\t'.")
parser.add_argument('-o','--outfile',required=True,help="Output file.")

args = parser.parse_args()
sep = args.sep

rfh = open(args.receiver,'r')
dfh = open(args.donor,'r')
fout = open(args.outfile,'w')

orig_rheader = rfh.readline().strip("\n")
rheader = orig_rheader.lower().split(sep)
dheader = dfh.readline().lower().strip("\n").split(sep)

rkeys = args.rkey.lower().split(",")
dkeys = args.dkey.lower().split(",")
tnames = args.fields.lower().split(",")

rkeyFields = [rheader.index(x) for x in rkeys]
dkeyFields = [dheader.index(x) for x in dkeys]
tfields = [dheader.index(x) for x in tnames]

outHeader = orig_rheader + sep + sep.join(tnames) + "\n"
fout.write(outHeader)

ddico = {}
for line in dfh:
	line = line.strip("\n").split(sep)
	if not line:
		continue
	key = ""
	for pos in dkeyFields:
		key += line[pos]
	ddico[key] = []
	for pos in tfields:
		ddico[key].append(line[pos])
dfh.close()

for line in rfh:
	line = line.strip("\n").split(sep)
	if not line:
		continue
	key = ""
	for pos in rkeyFields:
		key += line[pos]
	fout.write(sep.join(line))
	if key in ddico:
		fout.write(sep + sep.join(ddico[key]))
	else:
		fout.write(sep * len(tfields))
	fout.write("\n")
rfh.close()
fout.close()

		
		
