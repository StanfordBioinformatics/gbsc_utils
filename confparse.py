###
#AUTHOR: Nathaniel Watson
###

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
