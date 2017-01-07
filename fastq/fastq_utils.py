import re
import gzip
import bzip2
wsReg = re.compile(r'\s+')

class Index:
	def __init__(self,fqFile):
		self.fh = open(fqFile,'r')
		self.index = self._indexReads()	

	def __iter__(self):
		return iter(self.index)

	def __len__(self):
		return len(self.index)

	def __getitem__(self,seqid):
		return self.index[seqid]

	def _indexReads(self):
		dico = {}
		for key,val in indexparse(fh=self.fh,index=True):
			dico[key] = val
		return dico
	
	def getRec(self,seqid):	
		start,end = self[seqid]	
		numBytes = end - start
		self.fh.seek(start)
		return self.fh.read(numBytes)

def parse(fqFile):
	fh = getFastqReadFileHandle(fqFile)
	for attLine,seq,plusLine,qual in indexparse(fqFile,index=False):
		yield attLine,seq,plusLine,qual

def mem(fqFile):
	dico = {}
	fh = getFastqReadFileHandle(fqFile)
	for attLine,seq,plusLine,qual in indexparse(fh=fh,index=False):
			seqid = getSeqIdFromAttLine(attLine)
			dico[seqid] = [attLine,seq,plusLine,qual]
	return dico

def fileseek_hash(fqFile):
	fh = getFastqReadFileHandle(fqFile)
	seeks = {}
	for i in indexparse(fh=fh,index=True):
		seeks[i[0]] = i[1]
	return fh,seek

def fastParse(fastq):
	"""
	Function :
	Args     : fastq - A FASTQ file.
	Returns  : dict. containing all FASTQ records. The key is the entire title
						     line, and the value is in turn a dict containing the keys 'seq' and 'qual'. The '+' line of the FASTQ records is ignored. 
	"""
	fh = open(fastq,'r')
	all_records = {}
	count = 0
	record = {}
	for line in fh:
		line = line.strip()
		count += 1
		if count == 1:
			uid = line
			record[uid] = {}
		elif count == 2:
			record[uid]["seq"] = line
		elif count == 4:
			record[uid]["qual"] = line
			all_records[uid] = record[uid]
			count = 0
			record = {}
	return all_records
			
def indexparse(fh,index=True):
	"""
	This is a generator that steps through each record (in order) in the input FASTQ file. When the index parameter is true, returns a two item tuple for each record.
  The first item is the sequence ID (parsed as the first whitespace delimited element on the header line and exludes the leading "@" symbol), and the second item is
	a two-item tuple being the start and end byte positions of the record. If index is not True, then returns a four item tuple containing the attLine, sequence, plus line, and quality strings
  of the FASTQ record, in that order.
	"""
	INDEX=index
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
		fh = bzip2.BZ2File(fqFile,'r')
	else:
		fh = open(fqFile,'r')
	return fh

def getSeqIdFromAttLine(attLine):
	attLine = attLine.lstrip("@")
	seqid = attLine.split()[0]
	return seqid
	

def writeRec(fh,rec):
	"""
	Function : Writes the given FASTQ record to the given file handle. 
	Args     : fh - file handle
						 rec - a FASTQ record of the form that is returned by the parse() function.
	"""
	fh.write("\n".join(rec).rstrip() + "\n")
