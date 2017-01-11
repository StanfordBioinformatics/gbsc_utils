import sys
import datetime

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
		Function : Parses the records in an Illumina FASTQ file and stores all records or only those having specific barcodes.
							 The sequence and quality strings of each FASTQ record are stored in a list of lists of the form
																		[ ["ACGT","#AAF"], ["GGAT"," #AAA"] ... ] 
							 where each sublist stores the sequence followed by the quality. 
							 This list of lists is stored as self.data. A lookup table (dict) is also stored as self.lookup. It is of the form 
																		{ "seqid_x": index_x, "seqid_y": index_y, ... }
							 where an index gives the position in the list of the record with the given sequence ID. The sequence ID is stored
							 as the entire title line of a FASTQ record.
		Args     : fastq - The FASTQ file to be parsed.
							 log - file handle for logging. Defaults to sys.stdout.
							 extract_barcodes - list of one or more barcodes to extract from the FASTQ file. If the barcode is duel-indexed, separate
							     them with a '+', i.e. 'ATCGGT+GCAGCT', as this is how it is written in the FASTQ file. 
		"""
		self.fastqFile = fastq
		self.barcodes = extract_barcodes
		self.log = log
		self._parse() #sets self.data
									#sets self.lookup.
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
		self.log.write("Finished parsing " + self.fastqFile + "\n")
		self.log.flush()
#Total number of lines in SCGPM_MD-DNA-1_HFTH3_L3_unmatched_R1.fastq is 347,060,820.
