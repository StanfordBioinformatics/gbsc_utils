
import sys

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
			if not line:
				break
			line = line.strip()
			curtell = self.fh.tell()
			if line.startswith(">"):
				recName = ByteIndex.getFastaId(line)
				starts.append([recName,prevTell])
			prevTell = curtell
		for i in range(len(starts) - 1):
			recname = starts[i][0]
			recByteDict[recname] = [starts[i][1]] #start byte
			recByteDict[recname].append(starts[i + 1][1] - 1)	#end byte
		self.fh.seek(0,2) #go to end of file
		lastByte = self.fh.tell()
		lastRecName = starts[-1][0]
		recByteDict[lastRecName] = [starts[-1][1],lastByte]
		return recByteDict
	
	@staticmethod
	def getFastaId(header):
		header = header.lstrip(">")
		return header.split()[0]

	def getRawRecord(self,name):
		recCoords = self.recBytes[name]
		start = recCoords[0]
		length = recCoords[-1] - start
		self.fh.seek(start)
		return self.fh.read(length).strip()

class Rec:
	def __init__(self,fastaRec):
		self.rec  = fastaRec.split("\n")
		self.header = self.rec[0]
		self.name = self.header.lstrip(">").split()[0]
		self.seq = "".join(self.rec[1:]).upper()

	def getSeq(self):
		return self.seq

	def getHeader(self):
		return self.header

	def printRecord(self,name,numChars):
		bins = list(range(0,len(self.getSeq()) + numChars,numChars))
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
