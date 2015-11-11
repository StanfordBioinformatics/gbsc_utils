import os

class UnknownReadNumberException(Exception):
	pass

class FastqFile:
	"""
	Parses the individual fields of an Illumina FASTQ file name as output from bcl2fastq, and stores the fields as instance attributes.

	According to the v1.8.4 UG, bc2fastq names FASTQ files like so:
	<sample name>_<barcode sequence>_L<lane>_R<read number>_<set number>.fastq.gz	

	#Add FASTQ name format for bcl2fastq 2.17

	Since the SAMPLE_PROJECT and SAMPLE_NAME field in bcl2fastq 1X, and additionally SAMPLE_NAME in bcl2fastq2, can contain underscores, then we must always use negative indexing to get
	a token for the chunck, read number, or lane.	
	"""

	FORWARD_READ_NUM = 1
	REVERSE_READ_NUM = 2
	READ_NUMS = [FORWARD_READ_NUM,REVERSE_READ_NUM]

	def __init__(self,fqfile):
		"""
		Args : fqfile - A FASTQ file name, with or without the direcotry path, as assigned/formatted the Illumina demultiplexer. The directory path if provided will be stored in the 
										'path' instance attribute.
		"""
		self.path = fqfile
		self.fqf = os.path.basename(fqfile)
		self.tokens = self.fqf.split("_")
		self._setReadNumber()   #self.read
		self._setLaneNumber()   #self.lane
		self._setSetNumber()    #self.set
		self._setSampleId()     #self.id
		self._setSampleName()   #self.sampleName

	def isForwardReadFile(self):
		"""
		Function : Reports whether the FASTQ file contains forward reads only.
		Returns  : bool.
		"""
		if self.read == self.FORWARD_READ_NUM:
			return True
		return False
	
	def isReverseReadFile(self):
		"""
		Function : Reports whether the FASTQ file contains reverse reads only.
		Returns  : bool.
		"""
		if self.read == self.REVERSE_READ_NUM:
			return True
		return False

	def _setSampleName(self):
		"""
		Function : Parses out the <sample name> field from the FASTQ file's name. Sets the value to the 'sampleName' instance attribute.
		"""
		#the SAMPLE_NAME field can itself contain underscores.
		sampleFields =  self.tokens[0:-5 + 1] 
		self.sampleName = "_".join(sampleFields)
			
	def _setReadNumber(self):
		"""
		Function : Parses out the <read number> field from the FASTQ file's name. Sets the value to the 'read' instance attribute.
		"""
		readNum = int(self.tokens[-2].lstrip("R"))
		if readNum not in  self.READ_NUMS:
			raise UnknownReadNumberException("Unkwown read number '{readNum}' in FASTQ file name '{name}'. Only the following read numbers are recognized: '{allowed}'.".format(readNum=readNum,name=self.fqf,allowed=self.READ_NUMS))
		self.read = readNum
	
	def _setLaneNumber(self):
		"""
		Function : Parses out the <lane> number from the FASTQ file's name. Sets the value to the 'lane' instance attribute.
		"""
		laneNum = self.tokens[-3].lstrip("L")
		self.lane = int(laneNum)
	
	def _setSetNumber(self):
		"""
		Function : Grabs the set number of a FASTQ file.
		Returns  : int.
		""" 
		setNumber = self.tokens[-1].split(".")[0]
		self.set = setNumber

	def _setSampleId(self):
		"""
		This parse out the 4th '_' delimited field from the right, in the file name. For bcl2fastq v1.8.4, this
		will be the barcode sequence (I7, or I7-I5). For bcl2fastq v2.17, this will be the sample number (i.e S1).
		"""
		self.id = self.tokens[-4]
