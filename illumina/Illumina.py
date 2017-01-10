import sys
import re
import collections
import datetime




class SampleSheetMiSeqToHiSeq:
	"""Parses a SampleSheet in the MiSeq format. The MiSeq SampleSheet has several sections, with each denoted by a section header within brackets (i.e. [Header]). Sections include [Header],
		 [Reads], [Settings, and [Data]. 
	"""
	#Below are the SampleSheet fields that make up the Data section, as documentedin the v2.17 UG:
	SAMPLE_PROJECT = "Sample_Project"
	LANE = "Lane"
	SAMPLE_ID = "Sample_ID"
	SAMPLE_NAME = "Sample_Name"
	INDEX = "index"
	INDEX2 = "index2"
	#End SS fields.
	#Note that the SampleSheet can have other fields in the Data section that aren't documented in the UG.
	
	def __init__(self,samplesheet):
		self.SampleSheet = samplesheet
		self.ss = self.__parse()
		self.__formatHeader()
		self.__formatData()

	def __parse(self):
		"""Creates a dictionary attribute called 'dico' which contains keys for each traversed section in the SampleSheet (where the key is the same name as the section key).  
			 The value of each key is a list where each element is a line (stripped of white-space) that belongs to that that particular section.
		"""
		wsReg = re.compile("\s")
		reg = re.compile(r'^\[\w+\]')
		dico = {}
		dico["extra"] = []
		fh = open(self.SampleSheet,'r')
		for line in fh:
			line = line.strip("\n")
			if not line or not line.strip(","): #gets rid of empty lines and lines with nothing but commas
				continue
			hit = reg.match(line)
			if hit:
				key = hit.group()[1:-1]
				dico[key] = []
				continue
			line = wsReg.sub("",line) #white space not allowed in sample lines when demultiplexing
			dico[key].append(line)
#		print(dico)
		return dico
	

	def __formatHeader(self):
		"""
		Function : Each header line (within the Header section) has a key and a value. The key is the first comma-delimited field, and
							 the value is the second. The value may be empty. The parsed key will be stored into a dict along with the parsed value as
							 the key's value. The key's value will be the empty string if not value was parsed from the header line.
							 The dict will be set as the value of self's dico attribute.
		"""	
		hdico = {} #header dict
		for h in self.ss['Header']:
			try:
				line = h.split(",")
				key = line[0]
				val = line[1]
			except ValueError: #empty value
				key = h
				val = ""
			hdico[key] = val
		self.ss['Header'] = hdico
	
	def __formatData(self):
		"""
		Formats each sample in the [Data] section of self.__parse() into a collection.namedtubple whose attributes
		are the field names in the Header section of the sample sheet.
		"""
		header = self.ss['Data'].pop(0)
		print(header)
		SSEntry = collections.namedtuple("SSEntry",header)
		print(self.ss["Data"])
		newData = []
		newData = map(SSEntry._make,[x.split(",") for x in self.ss['Data']])
		self.ss['Data'] = newData

	def getDescription(self):
		des = self.ss["Header"]["Description"]
		return des

	def getProjectName(self):
		try:
			pn = self.ss["Header"]["ProjectName"]
		except KeyError:
			return ""
		return pn

	def getInvestigatorName(self):
		iname = self.ss["Header"]["InvestigatorName"]
		return iname

	def	convert(self,outfile):
		"""This is the step that performs the actual MiSeq-to-HiSeq SampleSheet conversion. All samples are treated as non-control since it's not possible to determine this from the MiSeq SampleSheet.
		  	Therefore, be sure to manually modify the control field in the generated HiSeq SampleSheet file if any should be marked as control.
		"""
		bcl2fastq_1_8_4_header = "FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,Project"
		fout = open(outfile,'w')
		fout.write(bcl2fastq_1_8_4_header + "\n")
		for sample in self.ss['Data']:
			fcid = "" #when running configureBclToFastq.p[, defaults to that in config.xml file in BaseCalls dir
			fout.write(fcid + ",")
			try:
				lane = sample.lane
			except AttributeError:
				lane = "1" #MiSeq
			fout.write(lane + ",")
			fout.write(sample.Sample_ID + ",")
			sampleRef = ""
			fout.write(sampleRef + ",")
			index = sample.index
			index2 = False
			index2 = sample.index2
			if index2:
				index += "-" + index2
			del index2
			fout.write(index + ",")
			description = self.getDescription()
			fout.write(description + ",")
			control = "N"
			fout.write(control + ",")
			recipe = ""
			fout.write(recipe + ",")
			operator = ""
			#operator = self.getInvestigatorName()
			fout.write(operator + ",")
			fout.write(sample.Sample_Project)
			fout.write("\n")
		fout.close()


class BclSampleSheet:
	"""
	Sample Sheet Columns
	The sample sheet contains the following columns:
		FCID - Flow cell ID
		Lane - Positive integer, indicating the lane number (1-8) SampleID ID of the sample
		SampleID - ID of the sample
		SampleRef - The reference used for alignment for the sample
		Index - Index sequences. Multiple index reads are separated by a hyphen (for example, ACCAGTAA-GGACATGA).
		Description - Description of the sample
		Control - Y indicates this lane is a control lane, N means sample Recipe Recipe used during sequencing
		Operator - Name or ID of the operator
		SampleProject - The project the sample belongs to
	"""

#	def __init__(ss):
#		self.ss = ss
#		fh = open(self.ss,'r')
#		for line in fh:
#			line = line.strip()
#			if not line or line.startswith("FCID"):
#				continue
#		dico = {}
#		line = line.split(",")
#		fcid = line[0]
#		lane = line[1]
#		sampleId = line[2]
#		sampleRef = line[3]
#		index = line[4]
#		desc = line[5]
#		control = line[6]
#		operator = line[7]
#		project = line[8]
#		
#		if not project:
#			project = "project"
#	
#		if lane not in dico:
#			dico[lane] = {}
#		if project not in dico[lane]:
#			dico[lane][project] = {}
	
def get_pairedend_read_id(read_id):
	"""
	Function : Given either a forward read or reverse read identifier, returns the corresponding paired-end read identifier.
	Args     : read_id - str. forward read or reverse read identifier. This should be the entire title line of a FASTQ record.
	Returns  : str. The pairend-end read identifier (title line). 
	Example  : Setting read_id to "@COOPER:74:HFTH3BBXX:3:1101:29894:1033 1:N:0:NATGAATC+NGATCTCG" will return 
						     @COOPER:74:HFTH3BBXX:3:1101:29894:1033 2:N:0:NATGAATC+NGATCTCG
	"""
	part1, part2 = read_id.strip().split()
	if part2.startswith("1"):
		part2 = part2.replace("1","2",1)
	elif part2.startswith("2"):
		part2 = part2.replace("2","1",1)
	else:
		raise Exception("Unknown read number in {title}".format(title=read_id))
	return part1 + " " + part2

class FastqParse():
	def __init__(self,fastq,log=sys.stdout,extract_barcodes=[]):
		"""
		Function : Parses the records in an Illumina FASTQ file and returns a dict containing all records or only those with the specifie
	             barcodes.
		Args     : fastq - A FASTQ file.
							 log - file handle for logging. Defaults to sys.stdout.
							 extract_barcodes - list of one or more barcodes to extract from the FASTQ file. If the barcode is duel-indexed, separate
							     them with a '-', i.e. 'ATCGGT+GCAGCT', as this is how it is written in the FASTQ file. 
		Returns  : dict. containing all FASTQ records, or only those records that have the barcode(s) of interest. The key is the entire title
							     line, and the value is in turn a dict containing the keys 'seq', 'qual', and 'header'. The value of 'header' is a dict
							     containing the parsed elements of the title line of a FASTQ record; its keys are documented in the
								   parseIlluminaFastqAttLine() function of this module. Note that the '+' line of the FASTQ records is ignored. 
		"""
		self.fastqFile = fastq
		self.barcodes = extract_barcodes
		self.log = log
		self._parse() #sets self.data to the parsed FASTQ file as a dict.

	@classmethod
	def parseIlluminaFastqAttLine(cls,attLine):
		#Illumina FASTQ Att line format (as of CASAVA 1.8 at least):
		#  @<instrument-name>:<run ID>:<flowcell ID>:<lane>:<tile>:<x-pos>:<y-pos> <read number>:<is filtered>:<control number>:<barcode sequence>
		uid = attLine.strip()
		header = uid.lstrip("@").split(":")
		dico = {}
		dico["instrument"] = header[0]
		dico["runId"] = header[1]
		dico["flowcellId"] = header[2]
		dico["lane"] = header[3]
		dico["tile"] = header[4]
		dico["xpos"] = header[5]
		ypos,readNumber = header[6].split()
		dico["ypos"] = ypos
		dico["readNumber"] = readNumber
		dico["isFiltered"] = header[7]
		dico["control"] = header[8]
		dico["barcode"] = header[9]
		return dico	

	def _parse(self):
		self.log.write("Parsing " + self.fastqFile + "\n")
		self.log.flush()
		fh = open(self.fastqFile,'r')
		self.data = []
		self.lookup = {}
		count = 0
		lineCount = 0
		for line in fh:
			lineCount += 1
			count += 1
			line = line.strip()
			if count == 1:
				#uid = lineCount
				uid = line
				barcode = line.rsplit(":",1)[-1]
				#self.data[uid] = {"name": line}
				#self.data[uid] = {}
			elif count == 2:
				seq = line
				#self.data[uid]["seq"] = line
			elif count == 4:
				#self.data[uid]["qual"] = line
				if barcode in self.barcodes or not self.barcodes:
						self.data.append([seq,line])
						self.lookup[uid] = len(self.data) - 1
				count = 0
			if lineCount % 1000000 == 0:
				self.log.write(str(datetime.datetime.now()) + ":  " + str(lineCount) + "\n")
				self.log.flush()
		fh.close()
		self.log.write("hey bob" + "\n")
		self.log.flush()
#Total number of lines in SCGPM_MD-DNA-1_HFTH3_L3_unmatched_R1.fastq is 347,060,820.
