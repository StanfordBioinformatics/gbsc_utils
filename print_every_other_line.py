#!/usr/bin/env python

###
#Nathaniel Watson
#2017-07-17
#nathankw@stanford.edu
###

import argparse

description = "Prints every even or odd line from the input file."
parser = argparse.ArgumentParser(description=description)
parser.add_argument("-i","--infile",required=True,help="The input file.")
me_group = parser.add_mutually_exclusive_group(required=True)
me_group.add_argument("-e","--even",action="store_true",help="Print the even-numbered lines.")
me_group.add_argument("-o","--odd",action="store_true",help="Print the odd-numbered lines.")
args = parser.parse_args()

infile = args.infile
even = args.even
odd = args.odd

fh = open(infile,'r')
count = -1
for line in fh:
	count += 1
	remainder = count % 2
	if remainder and even:
		print(line)
	elif not remainder and odd:
		print(line)
fh.close()
