import sys
import re

class SampleSheetMiSeqToHiSeq:
	"""Parses a SampleSheet in the MiSeq format. The MiSeq SampleSheet has several sections, with each denoted by a section header within brackets (i.e. [Header]). Sections include [Header],
		 [Reads], [Settings, and [Data]. 
	"""
	hiseq_header = "FCID,Lane,SampleID,SampleRef,Index,Description,Control,Recipe,Operator,Project"
	def __init__(self,samplesheet):
		self.SampleSheet = samplesheet
		self.dico = self.__parse()
		self.__formatHeader()
		self.__formatData()

	def __parse(self):
		"""Creates a dictionary attribute called 'dico' which contains keys for each traversed section in the SampleSheet (where the key is the same name as the section key).  
			 The value of each key is a list where each element is a line (stripped of white-space) that belongs to that that particular section.
		"""
		wsReg = re.compile("\s")
		reg = re.compile(r'^\[\w+\]$')
		dico = {}
		dico["extra"] = []
		fh = open(self.SampleSheet,'r')
		for line in fh:
			line = line.strip()
			if not line:
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
		hdico = {} #header dict
		for h in self.dico['Header']:
			key,val = h.split(",")
			hdico[key] = val
		self.dico['Header'] = hdico
	
	def __formatData(self):
		"""
		Formats each sample in the [Data] section of self.__parse() into a dictionary whose key is the Sample_ID and whose value is a dictionary containing the field headers in the header line of the [Data] section,
		which are (in order): Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description.
		"""
		header = self.dico['Data'].pop(0).split(",")
		if header[0] != "Sample_ID":
			raise Exception("Excpeted field header as first line in Data section, instead found {header}".format(header=",".join(header)))
	
		sidField = header.index("Sample_ID")
		snameField = header.index("Sample_Name")
		splateField = False
		try:
			splateField = header.index("Sample_Plate")
		except ValueError:
			pass

		swellField = False
		try: 
			swellField = header.index("Sample_Well")
		except ValueError:
			pass
		
		i7indexIdField = False
		try:
			i7indexIdField = header.index("I7_Index_ID")
		except ValueError:
			pass

		i7indexField = False
		if i7indexIdField:	
			i7indexField = header.index("index")
		
		i5indexIdField = False
		try:
			i5indexIdField = header.index("I5_Index_ID") 
		except ValueError:
			pass

		i5indexField = False
		if i5indexIdField:
			i5indexField = header.index("index2")

		sprojectField = header.index("Sample_Project")
		descriptionField = header.index("Description")
		

		sdico = {} #sample dict
		for sample in self.dico['Data']:
			sample = sample.split(",")
			sid = sample[sidField]
			sdico[sid] = {}
			sdico[sid]["Sample_ID"] = sid
			sdico[sid]["Sample_Name"] = sample[snameField]
			if splateField:
				sdico[sid]["Sample_Plate"] = sample[splateField]
			else:
				sdico[sid]["Sample_Plate"] = ""

			if swellField:
				sdico[sid]["Sample_Well"] = sample[swellField]
			else:
				sdico[sid]["Sample_Well"] = ""
			
			if i7indexIdField:	
				sdico[sid]["I7_Index_ID"] = sample[i7indexIdField]
				sdico[sid]["index"] = sample[i7indexField]
			else:
				sdico[sid]["I7_Index_ID"] = ""
				sdico[sid]["index"] = ""

			if i5indexField:
				sdico[sid]["I5_Index_ID"] = sample[i5indexIdField]
				sdico[sid]["index2"] = sample[i5indexField]
			else:
				sdico[sid]["I5_Index_ID"] = ""
				sdico[sid]["index2"] = ""
				

			sampleProject = sample[sprojectField]
			if not sampleProject:
				sampleProject = ""
			sdico[sid]["Sample_Project"] = sampleProject

			description = sample[descriptionField]
			if not description:
				description = ""
			sdico[sid]["Description"] = description

		self.dico['Data'] = sdico


	def getDescription(self):
		des = self.dico["Header"]["Description"]
		return des

	def getProjectName(self):
		pn = self.dico["Header"]["ProjectName"]
		return pn

	def getInvestigatorName(self):
		iname = self.dico["Header"]["InvestigatorName"]
		return iname

	def	convert(self,outfile):
		"""This is the step that performs the actual MiSeq-to-HiSeq SampleSheet conversion. All samples are treated as non-control since it's not possible to determine this from the MiSeq SampleSheet.
		  	Therefore, be sure to manually modify the control field in the generated HiSeq SampleSheet file if any should be marked as control.
		"""
		fout = open(outfile,'w')
		fout.write(self.hiseq_header + "\n")
		for sampleName in sorted(self.dico['Data']):
			sample = self.dico['Data'][sampleName]
			fcid = "" #when running configureBclToFastq.p[, defaults to that in config.xml file in BaseCalls dir
			fout.write(fcid + ",")
			lane  = "1"
			fout.write(lane + ",")
			sid = sample["Sample_ID"]
			fout.write(sid + ",")
			sampleRef = ""
			fout.write(sampleRef + ",")
			index = sample["index"]
			index2 = False
			try:
				index2 = sample["index2"]
			except KeyError:
				pass
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
			operator = self.getInvestigatorName()
			fout.write(operator + ",")
			project = self.getProjectName()
			fout.write(project)
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
	
		
			

		










			

