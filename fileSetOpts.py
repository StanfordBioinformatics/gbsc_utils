###
#AUTHOR: Nathaniel Watson
###

import argparse
import os

description = "Given two files containing row-by-row records whose fields are delimited by the specified delimiter, calculates the set difference or the set intersection between the two datasets based on a comparison of the primary key between each dataset. At present, only one field in each file may serve as the primary key."

parser = argparse.ArgumentParser()
parser.add_argument("-r","--reference",required=True,help="The reference file.")
parser.add_argument("-q","--query",required=True,help="The query file.")
parser.add_argument("--pkey-r",default=0,type=int,help="The 0-base field number of the primary key in --reffile.")
parser.add_argument("--pkey-q",default=0,type=int,help="The 0-base field number of the primary key in --query.")
parser.add_argument("-d","--delimiter",default="\t",help="The delimiter separating fields in --reffile and --query. The default is '\\t'.")
parser.add_argument("-o","--outfile",help="Output file name. If not specified, the original query file will be renamed to itself with a .bak extension, and the output will be named the original query file's name.")
parser.add_argument("--operation",required=True,choices=("diff","intersect"),help="Type type of set operation to perform.")
parser.add_argument("--debug",action="store_true", help="Currently only helps to debug when --operation is set to 'intersct'")

args = parser.parse_args()
debug = args.debug
op = args.operation
delim = args.delimiter
rkeyField = args.pkey_r
qkeyField = args.pkey_q
query = args.query
reference = args.reference
outfile = args.outfile
if not outfile:
	outfile = query
	queryBak = query + ".bak"
	os.rename(query,queryBak)
	query = queryBak

refdic = {}
rfh = open(reference,'r')
for line in rfh:
	line = line.strip("\n")
	if not line:
		continue	
	line = line.split(delim)
	key = line[rkeyField]
	refdic[key] = 1
rfh.close()

fout = open(outfile,'w')
qfh = open(query,'r')
for line in qfh:
	line = line.strip("\n")
	if not line:
		continue	
	line = line.split(delim)
	key = line[qkeyField]
	if key in refdic:
		if op == "intersect":
			fout.write("\t".join(line) + "\n")
	else:
		if debug and op == "intersect":
			print("Key {} not found.".format(key))
		if op == "diff":
			fout.write("\t".join(line) + "\n")
fout.close()
qfh.close()
	
	
