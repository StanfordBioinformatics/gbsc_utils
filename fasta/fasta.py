
import sys

def getFastaIdFromHeader(header):
	"""
	Function : Parses out the FASTA record ID from the passed in header-line. The ID is parses as the first white-space delimited field in the header line.
	Args     : header - str.
	Returns  : str.
	"""
	header = header.lstrip(">")
	return header.split()[0]

class ByteIndex:
	def __init__(self,infile):
		self.fh = open(infile,'r')
		self.recBytes = self.getByteStart()

	def getByteStart(self):	
		starts = []
		recByteDict = {}
		prevTell = 0
		while 1:
			line =self.fh.readline()
			if not line: #then end of file
				break
			line = line.strip()
			curtell = self.fh.tell()
			if line.startswith(">"):
				recName = getFastaIdFromHeader(line)
				starts.append([recName,prevTell])
			prevTell = curtell
		for i in range(len(starts) - 1):
			recname = starts[i][0]
			recByteDict[recname] = [starts[i][1]] #start byte
			recByteDict[recname].append(starts[i + 1][1] - 1)	#end byte (lands on the newline character of the last line of the record in question)
		self.fh.seek(0,2) #go to end of file
		lastByte = self.fh.tell()
		lastRecName = starts[-1][0]
		recByteDict[lastRecName] = [starts[-1][1],lastByte]
		return recByteDict
	
	def getRawRecord(self,name):
		"""
		Function : Retrieves the raw FASTA record with any leading and trailing white-space removed.
		Args     : name - str. Name of the FASTA record.
		Returns  : str. 
		"""
		recCoords = self.recBytes[name]
		start = recCoords[0]
		length = recCoords[-1] - start + 1
		self.fh.seek(start)
		return self.fh.read(length).strip()

class Rec:
	def __init__(self,fastaRec):
		self.rec  = fastaRec.split("\n")
		self.header = self.rec[0].strip()
		self.name = self.header.lstrip(">").split()[0]
		seqList = [ x.strip() for x in self.rec[1:] ]
		self.seq = "".join(seqList).upper()

	def getName(self):
		return self.name

	def getSeq(self):
		return self.seq

	def getHeader(self):
		return self.header

	def printRecord(self,numCharsPerLine=70):
		"""
		Function : Prints out a sequence in chunks of size numCharsPerLine for each line.
		"""
		bins = list(range(0,len(self.getSeq()) + numCharsPerLine,numCharsPerLine))
		print(self.getHeader())
		for i in range(len(bins) - 1):
#			print bins[i],bins[i + 1]
			print(self.seq[bins[i]:bins[i + 1]])

	def motifCount(self,motif):
		"""
		Function : Counts the number of times a sequence of nucleotides is seen in the FASTA record.
		Args     : motif - str. 
		"""
		motif = motif.upper()
		return self.seq.count(motif)
	
	def dinucleotideFreqs(self):
		combos = ["AA","AC","AG","AT","CC","CA","CT","CT","GG","GA","GC","GT","TT","TA","TC","TG"]
		dico = {}
		for i in combos:
			dico[i] = str(self.motifCount(i))
		return dico
		
if __name__ == "__main__":
	index = ByteIndex(sys.argv[1])
	recTxt = index.getRawRecord(sys.argv[2])
	rec = Rec(recTxt)
	gcCount = rec.gcCount()
