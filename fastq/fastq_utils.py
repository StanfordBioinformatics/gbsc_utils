import re
import gzip
import bz2
wsReg = re.compile(r'\s+')

def index(fqFile):
	dico = {}
	for key,val in indexparse(fqFile,index=True):
		dico[key] = val
	return dico

def parse(fqFile):
	for attLine,seq,plusLine,qual in indexparse(fqFile,index=False):
		yield attLine,seq,plusLine,qual

def indexparse(fqFile,index=True):
	"""
	This is a generator that steps through each record (in order) in the input FASTQ file. When the index parameter is true, returns the a two item tuple for each record.
  The first item is the sequence ID (parsed as the first whitespace delimited element on the header line and exluces the leading "@" symbol), and the second item is
	a two-item tuple being the start and end byte positions of the record.
	"""
	INDEX=index
	fh = getFastqReadFileHandle(fqFile)
	plusLineSeen = False
	attLine = ""
	seq = ""
	plusLine = ""
	qual = ""
	while 1:
		prevTell = fh.tell()
		line = fh.readline()
		curTell = fh.tell()	
		if not line: #end of file
			break
		line = line.strip()
		if not line:
			continue
		if line.startswith("@"):
			if not plusLineSeen:
				attLine = line
				#seqid will be set as the first white-space delimited value (without the leading "@")
				seqid = attLine[1:].split()[0]
				startTell = prevTell
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
			if not len(seq) == len(qual):
				raise ValueError("Error in file {fqFile}: Sequence length does not match quality length for FASTQ record {attLine}.  \nSequence is: '{seq}\nQual is: '{qual}'".format(fqFile=fqFile,attLine=attLine,seq=seq,qual=qual))
			else:
				if INDEX:
					yield seqid,(startTell,curTell)
				else:
					yield attLine,seq,plusLine,qual
				attLine = ""
				seq = ""
				plusLine = ""
				plusLineSeen = False
				qual = ""

def getFastqReadFileHandle(fqFile):
	if fqFile.endswith(".gz"):
		fh = gzip.open(fqFile,'r')
	elif fqFile.endswith(".bz2"):
		fh = bz2.BZ2File(fqFile,'r')
	else:
		fh = open(fqFile,'r')
	return fh


def writeRec(fh,rec):
	"""
	Function : Writes the given FASTQ record to the given file handle. 
	Args     : fh - file handle
						 rec - a FATQ record of the form that is returned by the parse() function.
	"""
	fh.write("\n".join(rec) + "\n")
