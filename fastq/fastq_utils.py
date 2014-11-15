import re
import gzip
wsReg = re.compile(r'\s+')

def parse(fqFile):
	if fqFile.endswith(".gz"):
		fh = gzip.open(fqFile,'r')
	else:
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

def writeRec(fh,rec):
	"""
	Function : Writes the given FASTQ record to the given file handle. 
	Args     : fh - file handle
						 rec - a FATQ record of the form that is returned by the parse() function.
	"""
	fh.write("\n".join(rec) + "\n")
