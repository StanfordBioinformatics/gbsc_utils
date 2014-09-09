###
#AUTHOR: Nathaniel Watson
###

import re

class Parse():
	"""
	Parses a configuration file having key and value pairs separated by "=". Whitespace is allowed before and after the separator.
	Lines beginning with "#" (or any whitespace then a "#") are skipped.
	Objects of this class look and feel like dictionaries whose keys are the keys in the configuration file.
	"""
	def __init__(self,confFile):
		self.confFile=confFile
		self.dico = self.__confDico()	
	def __confDico(self):
		fh = open(self.confFile,'r')
		dico = {}
		for line in fh:
			line = line.strip()
			if not line: continue
			if line.startswith("#"):
				continue
			key,value = line.split("=")
			key = key.strip()
			value = value.strip()
			dico[key] = value
		return dico
	
	def getDict(self):
		return self.dico

	def __iter__(self):
		return iter(self.dico)

	def __getitem__(self,key):
		return self.dico[key]

	def __setitem__(self,key,value):
		self.dico[key] = value

	def __contains__(self,key):
		return key in self.dico

def parseConfFile(confFile):
	"""
	FUNCTION:
	This method can be used to parse both the sample conf file and the control conf file. For examples of these files, see 
	/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/replicates/human/SK-N-SH_IRF3_SC-9082_rep1vs2/inputs/sample.conf and 
	/srv/gsfs0/projects/gbsc/SNAP_Scoring/production/controls/human/SK-N-SH_Rabbit_IgG/inputs/control.conf, respectively. The sample.conf file as it exists at
	now (9/4/2014) contains sections containing configuraiton lines particular to that section. A section is delcared at the start of a line and is of the form "[tag]",
    where "tag" is the section name.

  Sections in sample.conf:
    The sample.conf contains a "general" section and a section for each replicate.  Replicate sections begin with the word "replicate",
	and are followed by a replicate number (i.e. [replicate1] is the section for replicate number 1. There is a replicate section for each sample replicate.

	Sections in control.conf:
	The control.conf contains a single section, which is called "peakset".

	Regarding both the sample.conf and the control.conf, each line within a section contains a key and value pair, separated by an "=" sign.
	
	ARGS: confFile - path to a sample or control configuration file
	RETURNS: dict. Each key in the dict is a section that was parsed in the conf file. All keys in the dict are the same as the section names found in the conf file,
                   with the exception of replicate sections, which only have the replicate number forming the key.  The value of each section key in the dict is another dict, 
								 where the keys are the same as the keys found within a section of the conf file, and the values are the same as the key's values in the conf file.
	"""
	sections = {}
	sectionReg = re.compile(r'^\[\s*(\w+)\s*\]')
	splitReg = re.compile(r'\s*=\s*')
	fh = open(confFile,'r')
	section = "unknown"
	for line in fh:
		line = line.strip()
		if not line:
			continue
		if sectionReg.match(line):
			section = sectionReg.match(line).groups()[0]
			if section.startswith("replicate"):
				section = int(section.lstrip("replicate")) #only keep integer ID part
			sections[section] = {}
		else:
			key,val = splitReg.split(line)
			sections[section][key] = val
	return sections


def parseSignatures(sigFile):
	sectionReg = re.compile(r'^\[\s*(\w+)\s*\]')	
	sectDict = {}
	fh = open(sigFile,'r')
	for line in fh:
		line = line.strip()
		if not line:
			continue
		if sectionReg.match(line):
			section = sectionReg.match(line).groups()[0]
			sectDict[section] = []
			continue
		sectDict[section].append(line)
	for section in sectDict:
		sectDict[section] = "\n".join(sectDict[section])
	return sectDict
