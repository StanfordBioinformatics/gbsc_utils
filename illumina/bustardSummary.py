from lxml import etree


class BaseCallStats:
	def __init__(self,infile):
		"""
		Args : infile - The BustardSummary.xml file.
		"""
		self.summaryFile = infile
    self.tree = self.parse()
    self.root = self.tree.getroot()
  
  def parse(self):
    """ 
    Returns : An lxml.etree._ElementTree instance.
    """
    tree = etree.parse(self.summaryFile)
    return tree


	def baseYield(self):
		"""
		Function : Gets the total number of PF bases. This number is stored in the XML file by the tag named BustardSummary.BustardSummary.yield.
							 It is an integer that represents the total number of PF bases, calulcated as follows:
								 1) Get the total number of PF clusters (BustardSummary.ChipResultsSummary.clusterCountPF).
								 2) Get the total number of read1 bases by multiplying the number of PF clusters by the number of read1 cycles.
								 3) Get the total number of read2 bases by multiplying the number of PF clusters by the number of read2 cycles.
								 4) Get the total number of index1 bases by multiplying the number of PF clusters by the number of index1 cycles.
								 5) Get the total number of index2 bases by multiplying the number of PF clusters by the number of index2 cycles.
								 6) Total the number of bases from each calculation above, that that number is the total of PF bases.
		"""
		chipResultsSummary = self.root.find("BustardSummary.xml")
		baseYield = chipResultsSummary.getchildren.find("yield")
		baseYield = int(baseYield.text)
		return baseYield


if __name__ == "__main__":
	from gbsc_utils.SequencingRuns import conf
	from argparse import ArgumentParser
	description = "Calculates the number of PF bases for a given sequencing run."
	parser = ArgumentParser(description=description)
	parser.add_argument('-r','--run-name',required=True,help="The name of the sequencing run.")
	args = parser.parse_args()
	
	runName = args.run_name
	
