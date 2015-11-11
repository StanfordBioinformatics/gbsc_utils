#!/usr/bin/env python

import os
import sys
import csv
import re
import glob
from pprint import pprint
from gbsc_utils.illumina import fastq_file_name as ffn

class SampleSheetException(Exception):
	pass

class UnknownSampleError(Exception):
	pass


def getFlowCellId(runName):
	"""
	Args : runName - the name of the sequencing run.
	Returns : str.
	"""
	return runName.rsplit("_",1)[-1][1:] 



class V1:
	#list SampleSheet Fields
	FCID = "FCID"
	LANE = "Lane"
	SAMPLE_ID = "SampleID"
	SAMPLE_REF = "SampleRef"
	INDEX = "Index"
	DESCRIPTION = "Description"
	CONTROL = "Control"
	RECIPE = "Recipe"
	OPERATOR = "Operator"
	SAMPLE_PROJECT = "SampleProject"	

	#Default sample name if not multiplexed lane:
	NO_INDEX_NAME = "NoIndex"
	UNDETERMINED_INDEX_NAME = "Undetermined"

	UNDETERMINED_INDICES_FOLDER = "Undetermined_indices"

	PROJECT_DIR_PREFIX = "Project_" #prefix added to SAMPLE_PROJECT by bcl2fastq
	SAMPLE_DIR_PREFIX = "Sample_"   #prefix added to SAMPLE_ID by bcl2fastq
	
	SS_COLUMNS = [ #orderd as seen in the SS
		FCID,
		LANE,
		SAMPLE_ID,
		SAMPLE_REF,
		INDEX,
		DESCRIPTION,
		CONTROL,
		RECIPE,
		OPERATOR,
		SAMPLE_PROJECT	
	]


	def __init__(self,runName,bcl2fastqOutputDir,sampleSheet):
		"""
		Args : runName - the name of the sequencing run
					 bcl2fastqOutputDir - The output directory used in the demultiplexing command.
					 sampleSheet - File path to the SampleSheet.csv file.
		"""
		self.runName = runName
		self.outdir = bcl2fastqOutputDir
		self.ss = self._parseSampleSheet(sampleSheet)
		print(self.ss)

	def __iter__(self):
		return iter(self.ss)

	def __getitem__(self,index):
		return self.ss[index]

	def _parseSampleSheet(self,sampleSheet):
		"""
		Function:
			The sample sheet needs to have a header line, b/c bcl2fastq will read past the first line.
			The sample sheet contains the following columns:
		
			Column			Description
			FCID				Flow cell ID.
			Lane				Positive integer, indicating the lane number (1-8).
			SampleID		ID of the sample. (Does not have the uniqueness requirement that bcl2fastq2 has)
			SampleRef		The name of the reference.
			Index				Index sequence(s).
			Description	Description of the sample.
			Control			Y indicates this lane is a control lane, N means sample.
			Recipe			Recipe used during sequencing.
			Operator		Name or ID of the operator SampleProject The project the sample belongs to.
			SampleProject
		
	
			This function requires the presence of the following fields:
				1) Lane,

			For Each project specified in the samplesheet, a directory will be created by that name, but prefixed with "Project_". If the SampleProject isn't specified, it defaults
			to FCID, which in turn is calculated automatically if omitted in the SampleSheet.
			Each entry in the sample sheet will be stored in a sample directory underneath the project directory. The sample directory has the same name
			as the sample specified in the entry, but is prefixed with "Sample_". 
	
			As stated in the UG: "Reads with undetermined indices will be placed in the directory Undetermined_indices, unless the sample sheet specifies
			a specific sample and project for reads without index in that lane".
	
		Args : sampleSheet - File path to the SampleSheet.csv file.
		Returns : list of dicts. Each dict describes a row of the sample sheet. The keys of a dict are the field names.
		"""
		fcid = self.getFlowCellId()
		rows = []
		fh = open(sampleSheet,'r')
		header = fh.readline().strip("\n").split(",")
		if header != self.SS_COLUMNS:
			print(header)
			print(self.SS_COLUMNS)
			raise SampleSheetException("Missing header line in sample sheet " + sampleSheet + ". The first line must contain comma-delimited fields '{fieldNames}'.".format(fieldNames=",".join(self.SS_COLUMNS)))
	
		lanesPresent = []
		for line in fh:
			line = line.strip("\n")
			if not line:
				continue
			line = line.split(",")
			entry = {}
			index = -1
			for columnName in self.SS_COLUMNS:
				index += 1
				entry[columnName] = line[index]
			if not entry[self.LANE]:
				raise SampleSheetException("Missing value for 'Lane' field in Sample Sheet {samplesheet} in line {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			entry[self.LANE] = int(entry[self.LANE])
			lane = int(entry[self.LANE])
			if lane not in lanesPresent:
				lanesPresent.append(lane)
			if not entry[self.SAMPLE_ID]:
				entry[self.SAMPLE_ID] = self.createSampleId(lane=lane) #default set by bcl2fastq
			if not entry[self.SAMPLE_PROJECT]:
				entry[self.SAMPLE_PROJECT] = fcid #default used by bcl2fastq
			rows.append(entry)
			#bcl2fastq can include a line for the unmatched reads in the SampleSheet, even when there are other samples present. This is so the user can define the project name and sample name for unmatched reads. 
			# Furthermore, for the unmatched sample line the user must use the word Unmatched.
			# bcl2fastq2 on the other hand only allows the user to specify an unmatched sample line when there are no other sample lines present. Going back to bcl2fastq1, the output structure for the no-index sample differs
			# depending on whether there is an entry in the SamplSheet for it. The two cases are detailed below:
			#    case 1, There exists an entry in the sample sheet for no-index sample) The output structure is the same as if the no-index sample had a real index specified, except for the index in the file name will be 
      #            'Undetermined' if that was what was written in the index field in the sample sheet, otherwise the index in the file name will be 'NoIndex'.
			#    case 2, There doesn't exist an entry in the sample sheet for the no-index sample) The project folder that Illumina creates is Undetermined_indices, and the sample subfolder is prefixed with 'Sample', as
      #            are all other Sample projects, but the sample name used is 'lane' follwed by the lane number. Thus, if this were lane 1, then the project and sample folders would be in this 
			#            structure: Undetermined_indices/Sample_lane1, and the filenames will have "NoIndex" in place of the barcode sequence.	
			# 
			# Since we only care and support case 1, then we won't implement support for case 2.
			
		#Now check for lanes not present in the SampleSheet
		lanesNotPresent = set(range(1,9)).difference(lanesPresent)
		for lane in lanesNotPresent:
			row = {}
			row[self.FCID] = fcid
			row[self.LANE] = lane
			row[self.SAMPLE_ID] = self.createSampleId(lane=lane)
			row[self.SAMPLE_REF] = ""
			row[self.INDEX] = self.NO_INDEX_NAME
			row[self.DESCRIPTION] = ""
			row[self.CONTROL] = "N"
			row[self.RECIPE] = ""
			row[self.OPERATOR] = ""
			row[self.SAMPLE_PROJECT] = self.getFlowCellId()
			rows.append(row)
		#now check if any lanes are multiplexed, but don't specify a sample name and project for unmatched reads (with the Index beign set to "Undetermined"). If there is an 
		# Undetermined record for a lane, then it must specify the SampleID and SampleProject fields, or else the undetermined reads will not have been output. 
		#If there doens't exist such an entry, then the unmatched reads go into the Undetermined_indices folder, which has Sample_laneX folders, where X refers to the lane number.
		for lane in lanesPresent:
			multiplexed = False
			unmatchedSample = False
			for entry in rows:
				if not entry[self.LANE] == lane:
					continue
				if entry[self.INDEX]:
					multiplexed = True
				elif entry[self.INDEX] == self.UNDETERMINED_INDEX_NAME:
					unmatchedSample = True
			if multiplexed and not unmatchedSample:
				row = {}
				row[self.FCID] = fcid
				row[self.LANE] = lane
				row[self.SAMPLE_ID] = self.createSampleId(lane=lane)
				row[self.SAMPLE_REF] = ""
				row[self.INDEX] = self.UNDETERMINED_INDEX_NAME
				#As stated in the bcl2fastq v1.8.4 UG: In the case of non-multiplexed runs, <sample name> will be replaced with the lane numbers 
				# (lane1, lane2, ..., lane8) and <barcode sequence> will be replaced with "NoIndex".
				row[self.DESCRIPTION] = ""
				row[self.CONTROL] = "N"
				row[self.RECIPE] = ""
				row[self.OPERATOR] = ""
				row[self.SAMPLE_PROJECT] = self.UNDETERMINED_INDICES_FOLDER
		return rows

	def createSampleId(self,lane):
		"""
		Function : Creates a sample ID according to the UG when one isn't present for a given record in a given lane in the sample sheet.
		Args : lane - int. 
		"""
		return "lane" + str(lane)
			
	def getFlowCellId(self):
		return getFlowCellId(runName=self.runName)

	def getSampleSheetEntriesByLane(self,lane):
		entries = []
		for entry in self.ss:
			if lane != entry[self.LANE]:
				continue
			entries.append(entry)
		return entries

	def getFastqFilePathsBySample(self,ssEntry):
		"""
		Function : Searches for FASTQ files having a .fastq or .fastq.gz extension within the respective project and sample directories that blc2fastq would have output the 
							 FASTQ files in for the given sample sheet entry. Within this path, only the FASTQ files having the index in their file name that matches that of the provided
							 sample sheet entry are returned.
		Args     : ssEntry - dict. An element of self.ss.
		Returns  : list.
		"""
		project = ssEntry[self.SAMPLE_PROJECT]
		sample = ssEntry[self.SAMPLE_ID]
		index = ssEntry[self.INDEX]
		sampleDir = self.SAMPLE_DIR_PREFIX + sample
		if project != self.UNDETERMINED_INDICES_FOLDER:
			projectDir = self.PROJECT_DIR_PREFIX + project
		path = os.path.join(self.outdir,projectDir,sampleDir)
		print("Looking for FASTQ files haivng a .fastq or .fastq.gz extension in path {path}".format(path=path))
		fastqGlob = os.path.join(path,"*.fastq")
		fastqGzGlob = fastqGlob + ".gz"
		fqfiles = glob.glob(fastqGlob) + glob.glob(fastqGzGlob)
		if not fqfiles:
			raise Exception("No FASTQ files found in the path search ('{path}')for SampleSheet entry {ssEntry}!".format(ssEntry=ssEntry))
		fqfObjs = [ffn.FastqFile(i) for i in fqfiles]
		fqfObjs = [x for x in fqfObjs if x.id == index]
		return fqfObjs

	def getFastqFilePathsByLane(self,lane):
		"""
		Retrieves the paths to the FASTQ files (with or without a .gz extension) belonging to a given lane.

		According to the v1.8.4 UG, bc2fastq names FASTQ files like so:
			<sample name>_<barcode sequence>_L<lane>_R<read number>_<set number>.fastq.gz	

		Args     : lane - int. The number of the sequencing lane.
		Returns  : dict. where each key is an index of a sample in the given lane. The value of the key is a list of FASTQ files belonging to that barcode in the given sample and lane.
		"""
		entries = self.getSampleSheetEntriesByLane(lane=lane)
		fqfileDict = {}
		for ssEntry in entries:
			index = ssEntry[self.INDEX]
			fqfObjs = self.getFastqFilePathsBySample(ssEntry=ssEntry)
			fqfileDict[index] = fqfObjs
		return fqfileDict
	
#for each FASTQ file, dx stores these properties:    { 'SampleProject': 'Demo', 'SampleID': 'PhiX', 'Index': 'TTAGGC', 'Lane': 1, 'Read': 1, 'Chunk': 1 } 
def main(bcl2fastqOutputDir,sampleSheet,lanes=None):
	d = V1(sampleSheet=sampleSheet)
	visited = {}
	for entry in d.sampleSheet:
		#print(entry)
		fqfObjs = d.getFastqFilePathsBySample(ssEntry=entry)
		for f in fqfObjs:
			print("Found FASTQ file {f}".format(f=f.path))
			#uploadFastqFile(fqfile=fqfile,props=entry)

class V2:
	"""
	The software versions dependencies given below are copied from the v2.17 UG.

	The following software is required to run bcl2fastq2 Conversion Software v2.17:
		1) zlib
		2) librt
		3) libpthread
	To build bcl2fastq2 Conversion Software v2.17, you need the following software. Versions listed are tested and supported; newer versions are untested.
		1) gcc 4.7 (with support for c++11)
		2) boost 1.54 (with its dependencies) } CMake 2.8.9
		3) zlib
		4) librt
		5) libpthread
	Changes in bcl2fastq v2x:
		1) The binary name is bcl2fastq instead of configureBclToFastq.pl.
		2) Demultiplexes with 1mm by default. Can go upto 2 mm.
		3) By default, reads are output in the BaseCalls directory.
	  4) If a project is specified, a project subdirectory is created, and that subdirectory is named exactely as it appears in the SampleSheet.
		5) As stated in the bcl2fastq 2.1 UG: For each sample, there is one file per lane per read number (if reads exist for that sample, lane, and read number).
		6) The last part of the file name (before the .fastq.gz_ is _001. 
		7) By default, the SampleSheet.csv file will be searched for in the top-level run directory.
		8) As the UG puts it: --runfolder-dir is the current directory and --output-dir is the Data/Intensities/BaseCalls subdirectory of the run folder.
		   With this structure, the bcl2fastq command can be issued from the run-folder
		9) There isn't a --no-eamss option anymore.
		10) There isn't a NoIndex sample for unmultiplexed runs (sample sheet w/o entries) as there is with V1.
		11) It's multithreaded
		12) FASTQ header format is now 
					@<instrument>:<run number>:<flowcell ID>:<lane>:<tile>:<x- pos>:<y-pos>:<UMI> <read>:<is filtered>:<control number>:<index>
				In v1.8.4 it was:
					@<instrument>:<run number>:<flowcell ID>:<lane>:<tile>:<x- pos>:<y-pos> <read>:<is filtered>:<control number>:<index>
				
		The difference is the presence of the <UMI> tag in v2x. UMI stands for Unique Molecular Identifier. The UG states:
			UMIs are random k-mers attached to the genomic DNA before PCR amplification. The UMI is amplified with the amplicons, which 
			later allows for detection of PCR duplicates and correction of amplification errors. bcl2fastq2 Conversion Software v2.17 
			removes these bases and places them into the read name in the FASTQ files.			
	"""

	#If no sample sheet is provided, all reads are saved in Undetermined_S0_* FASTQ files (UG), i.e. Undetermined_S0_L001_R1_001.fastq.gz or Undetermined_S0_L001_R2_001.fastq.gz.
	#Sample_ID and Sample_Name may only contain alpha-numerics and '-' and '_'.
	#It is possible to assign samples without index to Sample_ID or other identifiers by leaving the Index field empty (but unlike V1, this must be the only entry in the SampleSheet!)
	#SAMPLE SHEET DETAILS
	# 1) Sample_ID is required and must be unique within a lane
	#	2) FASTQ files are named like so:
	#      <SampleName>_S1_L001_R1_001.fastq.gz 
	#    Where SampleName is optional. As stated in the UG, "If a sample name is not provided, the file name includes the 
	#    sample ID, which is a required field in the sample sheet and must be unique within a lane".
  #    But I noticed that the Sample_ID field isn't actually required. If absent but the Sample_Name field is present, bcl2fastq will output 
  #    a directory called "unknown" (within a project directory if one was specified) and put the sample's fastq files in there. But this script will mandate the presence of Sample_ID.
	#    The sample number, here S1, is a "numeric assignment based on the order in the sample sheet that a sample ID first appeared in a given lane".
	#    This numbering starts at 1. 0 is reserved for the unmatched reads FASTQ file.
	# The only difference between the file names output by V1 and V2 are that V1 has a barcode sequence in the spot that V2 has the sample number.

	#bcl2fastq2 Conversion Software v2.17 uses the following sample sheet columns in the [Data] section.
		#1) Sample_Project - If specified, a directory with the specified name is created and FASTQ files are stored there. Multiple samples can use the same project.
		#2) Lane - If specified, FASTQ files are generated only for those samples with the specified lane number.
		#3) Sample_ID - ID of the sample. Must be unique within a given lane.
		#4) Sample_Name - Descriptive name of the sample
		#5) index - Index sequence
		#6) index2 - Index sequence for index 2, if using dual indexing

	#NOTE: As the UG states - "If the Sample_ID and Sample_Name columns are both specified and do not match, the FASTQ files are placed in an additional subdirectory called <SampleId>."

	#SS Columns
	SAMPLE_PROJECT = "Sample_Project"
	LANE	= "Lane"
	SAMPLE_ID = "Sample_ID"
	SAMPLE_NAME = "Sample_Name"
	INDEX = "index"
	INDEX2 = "index2"

	SS_COLUMNS = [ #orderd as seen in the SS
		SAMPLE_PROJECT,
		LANE,
		SAMPLE_ID,
		SAMPLE_NAME,
		INDEX,
		INDEX2 ]

	UNDETERMINED = "Undetermined"
	SAMPLE_NUM = "" #Used to store the sample number that corresponds to the S# field in the file name, where # is an int.
	S0 = "S0" # the sample number used samples not having a barcode

	def __init__(self,runName,bcl2fastqOutputDir,sampleSheet):
		"""
		Args : runName - the name of the sequencing run
					 bcl2fastqOutputDir - The output directory used in the demultiplexing command.
					 sampleSheet - File path to the SampleSheet.csv file.
		"""
		self.runName = runName
		self.outdir = bcl2fastqOutputDir
		self.ss = self._parseSampleSheet(sampleSheet)
		print(self.ss)

	def _parseSampleSheet(self,sampleSheet):
		"""
		The sample sheet needs to have a [Data] section line, followed by a field header line. bcl2fastq2 does not appear to require these lines (especially the field header line as needed for 
		bcl2fastq 1X which will expect it and will otherwise skip the first sample if the header line isn't present) and doesn't appear to skip samples if the header line is missing. But this script
		will require them.

		This function requires at minimum the presence of the following fields in each sample line:
			1) Lane,
			2) SampleID,

		For Each project specified in the samplesheet, a directory will be created by that name. A subdirectory of the project by the name of the provided
		Sample_ID will only created if Sample_Name is provided and different from the value of the Sample_ID.

		Args : sampleSheet - File path to the SampleSheet.csv file.
		Returns : list of dicts. Each dict describes a row of the sample sheet. The keys of a dict are the field names.
		"""
		rows = []	
		lanesPresent = []
		foundDataSection = False
		fh = open(sampleSheet,'r')
		while 1:
			line = fh.readline()
			if not line:
				break
			if line.startswith("[Data]"):
				foundDataSection = True
				break
		if not foundDataSection:
			raise SampleSheetException("SampleSheet {ss} doesn't have a [Data] section.".format(ss=fh.name))
		header = fh.readline().rstrip("\n").split(",")
		if header != self.SS_COLUMNS:
			print(self.SS_COLUMNS)
			raise SampleSheetException("Missing header line in sample sheet " + sampleSheet + ". The first line in the SampleSheet that follows the [Data] section line must contain the comma-delimited fields '{fieldNames}'.".format(fieldNames=",".join(self.SS_COLUMNS)))
		#the rest of the lines are sample lines
		sampleNumber = 0 #used for calculating the sample number field in the FASTQ file name.
		sampleIdDict = {}
		for sampleLine in fh:
			entry = {}
			sampleLine = sampleLine.rstrip("\n").split(",")
			index = -1
			for columnName in self.SS_COLUMNS:
				index += 1
				entry[columnName] = sampleLine[index]
			lane = entry[self.LANE]
			if not lane:
				raise SampleSheetException("Missing value for 'Lane' field in Sample Sheet {samplesheet} in sampleLine {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			if lane not in lanesPresent:
				lanesPresent.append(lane)
			sampleId = entry[self.SAMPLE_ID]	
			if not sampleId:
				raise SampleSheetException("Missing value for 'SampleID' field in Sample Sheet {samplesheet} in sampleLine {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			if not entry[self.INDEX]:
				entry[self.SAMPLE_NUM] = 0
			if sampleId not in sampleIdDict:
				if not entry[self.INDEX]:
					sampleIdDict[sampleId] = self.S0
				else:
					sampleNumber += 1
					sampleIdDict[sampleId] = "S" + str(sampleNumber)
			entry[self.SAMPLE_NUM] = sampleIdDict[sampleId]
			if sampleId != entry[self.SAMPLE_NAME]: #then a folder is created named after the SAMPLE_ID, and will be inside the SAMPLE_PROJECT folder if one was specified.
				entry[self.SAMPLE_PROJECT] = os.path.join(entry[self.SAMPLE_PROJECT],sampleId)
				entry[self.SAMPLE_NAME] = sampleId #b/c the SAMPLE_ID will appear in the FASTQ file name in place of the SAMPLE_NAME now
			rows.append(entry)

		lanesNotPresent = set(range(1,9)).difference(lanesPresent)
		for i in lanesNotPresent:
			#lane is unmultiplexed sample with no entries in the [Data] section of the SampleSheet.
			row = {}
			row[self.SAMPLE_PROJECT] = ""
			row[self.SAMPLE_LANE] = lane
			row[self.SAMPLE_ID] = self.UNDETERMINED
			row[self.SAMPLE_NAME] = self.UNDETERMINED
			row[self.INDEX] = ""
			row[self.INDEX2] = ""
			row[self.SAMPLE_NUM] = self.S0
			rows.append(row)
		return rows

	def getFastqFilePaths(self,lane):
		"""
	  The sample number in the FASTQ file name starts at 1, except for sample number 0 (S0) which is reserved for the unmatched reads FASTQ file.
		According to the v2.17 UG, bc2fastq names FASTQ files like so:
			<SampleName>_S1_L001_R1_001.fastq.gz
	  where SampleName is optional. The sample number, here S1, is a "numeric assignment based on the order in the sample sheet that a sample ID first appeared in a given lane".
		This numbering starts at 1. 0 is reserved for the unmatched reads FASTQ file.

		Function : 
		Args     : lane - int. The number of the sequencing lane.
		Returns  : list of FASTQ files that belong to the given lane.
		"""
		entries = self.getSampleSheetEntriesByLane(lane=lane)
		fqfileDict = {}
		for ssEntry in entries:
			project = ssEntry[self.SAMPLE_PROJECT]
			sampleName = ssEntry[self.SAMPLE_NAME]
			sampleNum = ssEntry[self.SAMPLE_NUM]
			index = ssEntry[self.INDEX]
			index2 = ssEntry[self.INDEX2]
			combinedIndex = index
			if index2:
				combinedIndex = index + "-" + index2
			path = os.path.join(self.outdir,project) #based on V2._parseSampleSheet(), the directory for the sample is combined into that of the project.
			print("Looking for FASTQ files in path {path}".format(path=path))
			#we need a lot of details in the glob pattern, b/c lanes can have their FASTQ files output in the same directory, and can even have the same SAMPLE_ID and hence the same SAMPLE_NUM. 
			# Thus, its necessary to include the lane number in the glob pattern.
			globPattern = os.path.join(path,sampleName + "_" + sampleNum + "_" + "L00" + str(lane) + "*.fastq.gz")
			fqfiles = glob.glob(globPattern)
			fqfileDict[combinedIndex] = fqfiles
		return fqfileDict


if __name__ == "__main__":
	from argparse import ArgumentParser
	parser = ArgumentParser()
	parser.add_argument('-b','--bcl2fastq-version',required=True,type=int,help="int. The major version number of the bcl2fastq demultiplexer that was used to demultiplex the run.")
	parser.add_argument('-o','--outdir',required=True,help="The output directory that bcl2fastq used.")
	parser.add_argument('-s','--samplesheet',required=True,help="The sample sheet")
	parser.add_argument('-r','--run-name',required=True,help="runName - the name of the sequencing run")
	
	args = parser.parse_args()
	runName = args.run_name
	ss = args.samplesheet
	outdir = args.outdir
	version = args.bcl2fastq_version
	if version == 1:
		obj = V1(runName=runName,bcl2fastqOutputDir=outdir,sampleSheet=ss)
	elif version == 2:
		obj = V2(runName=runName,bcl2fastqOutputDir=outdir,sampleSheet=ss)
