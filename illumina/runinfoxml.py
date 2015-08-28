from lxml import etree


class RI:
	def __init__(self,runinfoFile):
		self.runinfoFile = runinfoFile
		self.tree = self.parse()
		self.root = self.tree.getroot()
	
	def parse(self):
		"""
		Returns : An lxml.etree._ElementTree instance.
		"""
		tree = etree.parse(self.runinfoFile)
		return tree
		
	def reads(self):
		"""
		Returns : A list of dicts. Each dict has the keys from the attributes of a Read element in the RunInfo.xml file.
				      An example of a Read element in the RunInfo.xml file is:
								<Read Number="1" NumCycles="101" IsIndexedRead="N" />
		"""
		reads = self.root.find("Run").find("Reads").getchildren()
		lis = []
		for r in reads:
			lis.append(r.attrib)
		return lis	

	def isPairedEnd(self):
		"""
		Returns : bool. True if paired-end run, False otherwise.
		"""
		reads = self.reads()
		for i in reads:
			if i["IsIndexedRead"] == "Y":
				continue
			if i["Number"] == "2":
				return True
		return False


if __name__ == "__main__":
	from argparse import ArgumentParser
	
	description = "Howdy there!"
	parser = ArgumentParser(description=description)
	parser.add_argument("-i","--infile",required=True,help="The RunInfo.xml file.")

	args = parser.parse_args()
	runinfoFile = args.infile
	ri = RI(runinfoFile)
	reads = ri.reads()
	print(reads)

