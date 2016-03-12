import sys
import re
import collections



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
	
		
			

		


