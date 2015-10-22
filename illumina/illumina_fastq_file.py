class UnknownReadNumberException(Exception):
	pass

class FastqFile:

	FORWARD_READ_NUM = 1
	REVERSE_READ_NUM = 2
	READ_NUMS = [FORWARD_READ_NUM,REVERSE_READ_NUM]

	def __init__(self,fqfile):
		"""
		Args : fqfile - A FASTQ file name as assigned/formatted the Illumina demultiplexer. 
		"""
		self.fqf = fqfile
		self.readNum = self._getReadNumber()
		self.laneNum = self._getLaneNumber()
		self.setNumber = self._getSetNumber()

	def isForwardReadFile(self):
		"""
		Function : Reports whether the FASTQ file contains forward reads only.
		Returns  : bool.
		"""
		if self.readNum == self.FORWARD_READ_NUM:
			return True
		return False
	
	def isReverseReadFile(self):
		"""
		Function : Reports whether the FASTQ file contains reverse reads only.
		Returns  : bool.
		"""
		if self.readNum == self.REVERSE_READ_NUM:
			return True
		return False
			
	def _getReadNumber(self):
		"""
		Function : According to the v1.8.4 UG, bc2fastq names FASTQ files like so:
					 		 <sample name>_<barcode sequence>_L<lane>_R<read number>_<set number>.fastq.gz	
		Returns: int. in the set [1,2], where 1 means forward read and 2 means reverse read.
		"""
		tokens = self.fqf.split("_")
		#Since the SAMPLE_PROJECT and SAMPLE_ID field in bcl2fastq 1X, and additionally SAMPLE_NAME in bcl2fastq2, can contain underscores, then we must always use negative indexing to get
		# a token for the chunck, read number, or lane.	
		readNum = int(tokens[-2].lstrip("R"))
		if readNum not in  self.READ_NUMS:
			raise UnknownReadNumberException("Unkwown read number '{readNum}' in FASTQ file name '{name}'. Only the following read numbers are recognized: '{allowed}'.".format(readNum=readNum,name=self.fqf,allowed=self.READ_NUMS))
		return readNum
	
	def _getLaneNumber(self):
		"""
		Function : Grabs the lane number (i.e. 1) from the FASTQ file name that was assigned by the sequencer.
		Returns  : int.
		"""
		tokens = self.fqf.split("_")
		#Since the SAMPLE_PROJECT and SAMPLE_ID field in bcl2fastq 1X, and additionally SAMPLE_NAME in bcl2fastq2, can contain underscores, then we must always use negative indexing to get
		# a token for the chunck, read number, or lane.	
		laneNum = tokens[-3].lstrip("L")
		return int(laneNum)
	
	def _getSetNumber(self):
		"""
		Function : Grabs the set number of a FASTQ file.
		Returns  : int.
		""" 
		tokens = self.fqf.split("_")
		#Since the SAMPLE_PROJECT and SAMPLE_ID field in bcl2fastq 1X, and additionally SAMPLE_NAME in bcl2fastq2, can contain underscores, then we must always use negative indexing to get
		# a token for the chunck, read number, or lane.	
		setNumber = tokens[-1].split(".")[0]
		return setNumber
