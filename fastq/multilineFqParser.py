#from argparse import ArgumentParser
#
#parser = ArgmentParser()
#parser.add_argument('-i','--infile',required=True,help="Input FASTQ file.")
#
#args = parser.parse_args()

import re
wsReg = re.compile(r'\s+')

def read_fastq(fqFile):
	fh = open(fqFile,'r')
	plusLineSeen = False
	attLine = ""
	seq = ""
	plusLine = ""
	qual = ""
	for line in fh:
		line = line.strip()
		if not line:
			continue
		if line.startswith("@"):
			if not plusLineSeen:
				attLine = line
			else:
				qual += wsReg.sub("",line)
		elif line.startswith("+"):
			if attLine:
				if not plusLineSeen:
					plusLineSeen = True
				plusLine = line
			else:
				qual += wsReg.sub("",line)
		else:
			if plusLineSeen:
				qual += wsReg.sub("",line)
			else:
				seq += wsReg.sub("",line)
		if attLine and seq and plusLine and qual:
			if len(seq) == len(qual):
				yield attLine,seq,plusLine,qual
				attLine = ""
				seq = ""
				plusLine = ""
				plusLineSeen = False
				qual = ""
	
		
	

