###
#AUTHOR: Nathaniel Watson
###

class Parse():
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
