#!/usr/bin/env python

import os
import sys
import csv
import re
import glob
from pprint import pprint
import dxpy

class SampleSheetException(Exception):
	pass


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
	NO_INDEX = "NoIndex"

	PROJECT_DIR_PREFIX = "Project_"
	SAMPLE_DIR_PREFIX = "Sample_"
	
	
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


	def __init__(self,bcl2fastqOutputDir,sampleSheet):
		"""
		Args : bcl2fastqOutputDir - The output directory used in the demultiplexing command.
					 sampleSheet - File path to the SampleSheet.csv file.
		"""
		self.outdir = bcl2fastqOutputDir
		self.sampleSheet = self.parseSampleSheet(sampleSheet)

	def __iter__(self):
		return iter(self.sampleSheet)

	def __getitem__(self,index):
		return self.sampleSheet[index]

	def parseSampleSheet(self,sampleSheet):
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
		
	
			This function requires the presence of the following fields:
				1) Lane,
				2) SampleID,
				3) Project

			For Each project specified in the samplesheet, a directory will be created by that name, but prefixed with "Project_".
			Each entry in the sample sheet will be stored in a sample directory underneath the project directory. The sample directory has the same name
			as the sample specified in the entry, but is prefixed with "Sample_". 
	
			As stated in the UG: "Reads with undetermined indices will be placed in the directory Undetermined_indices, unless the sample sheet specifies
			a specific sample and project for reads without index in that lane".
	
		Args : sampleSheet - File path to the SampleSheet.csv file.
		Returns : list of dicts. Each dict describes a row of the sample sheet. The keys of a dict are the field names.
		"""
		rows = []
		fh = open(sampleSheet,'r')
		header = fh.readline().strip("\n").split(",")
		if header != self.SS_COLUMNS:
			print(header)
			print(self.SS_COLUMNS)
			raise SampleSheetException("Missing header line in sample sheet " + sampleSheet + ". The first line must contain comma-delimited fields '{fieldNames}'.".format(fieldNames=",".join(self.SS_COLUMNS)))
	
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
			if not entry[self.SAMPLE_ID]:
				raise SampleSheetException("Missing value for 'SampleID' field in Sample Sheet {samplesheet} in line {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			if not entry[self.SAMPLE_PROJECT]:
				raise SampleSheetException("Missing value for 'SampleProject' field in Sample Sheet {samplesheet} in line {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			rows.append(entry)
			#bcl2fast1 can include a line for the unmatched reads in the SampleSheet, even when there are other samples present. This is so the user can define the project name and sample name for unmatched reads. 
			# Furthermore, for the unmatched sample line the user can eithe leave the barcode blank, or use the word Unmatched, but these are the only two options for the index read text. 
			# bcl2fastq2 on the other hand only allows the user to specify an unmatched sample line when there are no other sample lines present. Going back to bcl2fastq1, the output structure for the no-index sample differs
			# depending on whether there is an entry in the SamplSheet for it. The two cases are detailed below:
			#    case 1, There exists an entry in the sample sheet for no-index sample) The output structure is the same as if the no-index sample had a real index specified, except for the index in the file name will be 
      #            'Undetermined' if that was what was written in the index field in the sample sheet, otherwise the index in the file name will be 'NoIndex'.
			#    case 2, There doesn't exist an entry in the sample sheet for the no-index sample) The project folder that Illumina creates is Undetermined_indices, and the sample subfolder is prefixed with 'Sample', as
      #            are all other Sample projects, but the sample name used is 'lane' follwed by the lane number. Thus, if this were lane 1, then the project and sample folders would be in this 
			#            structure: Undetermined_indices/Sample_lane1.	
			# 
			# Since we only care and support case 1, then we won't implement support for case 2.
		if not row:
			raise Exception("Error: This program does not support a sample sheet without any samples.")
		return rows
			
	def getFastqFiles(self,sampleSheetEntry):
		"""
		Retrieves the paths to the FASTQ files (with or without a .gz extension) belonging to a given sample from the SampleSheet.
		According to the v1.8.4 UG, bc2fastq names FASTQ files like so:
			<sample name>_<barcode sequence>_L<lane>_R<read number>_<set number>.fastq.gz	
		Function : 
		Args		 : sampleSheetEntry   - dict. reperesenting a row from the SampleSheet.csv file that was used in the demultiplexing.
	                                  Should be formatted as one of the dicts stored in the list returned by parseSampleSheet().
		Returns  : list of FASTQ files that belong to the sampleSheetEntry.
		"""
		project = sampleSheetEntry[self.SAMPLE_PROJECT]
		sample = sampleSheetEntry[self.SAMPLE_ID]
		lane = sampleSheetEntry[self.LANE]
		index = sampleSheetEntry[self.INDEX]
	
		if not index:
			index = self.NO_INDEX
			#As stated in the bcl2fastq v1.8.4 UG: In the case of non-multiplexed runs, <sample name> will be replaced with the lane numbers 
			# (lane1, lane2, ..., lane8) and <barcode sequence> will be replaced with "NoIndex".
	
		sampleDir = self.SAMPLE_DIR_PREFIX + sample
		projectDir = self.PROJECT_DIR_PREFIX + project
		path = os.path.join(self.outdir,projectDir,sampleDir)
		print("Looking for FASTQ files in path {path}".format(path=path))
		fastqGlob = os.path.join(path,sample + "_" + index + "*.fastq")
		fastqGzGlob = fastqGlob + ".gz"

		fqfiles = glob.glob(fastqGlob) + glob.glob(fastqGzGlob)
		return fqfiles
	
	def filterSampleSheetEntries(self,entries,lanes):
		"""
		Args : entries - a list of dicts as returned by parseSampleSheet_va().
					 lanes   - list of lane numbers (may be int or str.) that indicate which samplesheet entries to keep.
	                   If lanes is set to None, then the input 'entries' is returned unchanged.
		"""
		if not lanes:
			return entries
		keep = []
		lanes = [str(x) for x in lanes]
		for i in entries:
			lane = entries[LANE]
			if lane in lanes:
				keep.append(entry)
		return keep
			
	def getFastqFileReadNumber(self,fastqfile):
		"""
		According to the v1.8.4 UG, bc2fastq names FASTQ files like so:
		<sample name>_<barcode sequence>_L<lane>_R<read number>_<set number>.fastq.gz	

		Returns: int
		"""
		tokens = fastqfile.split("_")
		return int(tokens[-2].lstrip("R"))
	
	def getFastqFileSetNumber(self,fastqfile):
		tokens = fastqfile.split("_")
		setNumber = tokens[-1].split(".")[0]
		return setNumber
		
#for each FASTQ file, dx stores these properties:    { 'SampleProject': 'Demo', 'SampleID': 'PhiX', 'Index': 'TTAGGC', 'Lane': 1, 'Read': 1, 'Chunk': 1 } 
def main(bcl2fastqOutputDir,sampleSheet,lanes=None):
	d = V1(sampleSheet=sampleSheet)
	visited = {}
	for entry in d.sampleSheet:
		#print(entry)
		fqfiles = d.getFastqFiles(sampleSheetEntry=entry)
		for f in fqfiles:
			print("Found FASTQ file {f}".format(f=f))
			#uploadFastqFile(fqfile=fqfile,props=entry)

if __name__ == "__main__":
	import sys
	main(sys.argv[1],sys.argv[2])



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
			 If a project is specified, a project subdirectory is created, and that subdirectory is named exactely as it appears in the SampleSheet.
		4) As stated in the bcl2fastq 2.1 UG: For each sample, there is one file per lane per read number (if reads exist for that sample, lane, and read number).
		5) The last part of the file name (before the .fastq.gz_ is _001. 
		6) By default, the SampleSheet.csv file will be searched for in the top-level run directory.
		7) As the UG puts it: --runfolder-dir is the current directory and --output-dir is the Data/Intensities/BaseCalls subdirectory of the run folder.
													With this structure, the bcl2fastq command can be issued from the run-folder
		8) There isn't a --no-eamss option anymore.
		9) It's multithreaded
		10) FASTQ header format is now 
					@<instrument>:<run number>:<flowcell ID>:<lane>:<tile>:<x- pos>:<y-pos>:<UMI> <read>:<is filtered>:<control number>:<index>
				In v1.8.4 it was:
					@<instrument>:<run number>:<flowcell ID>:<lane>:<tile>:<x- pos>:<y-pos> <read>:<is filtered>:<control number>:<index>
				
		The difference is the presence of the <UMI> tag in v2x. UMI stands for Unique Molecular Identifier. The UG states:
			UMIs are random k-mers attached to the genomic DNA before PCR amplification. The UMI is amplified with the amplicons, which 
			later allows for detection of PCR duplicates and correction of amplification errors. bcl2fastq2 Conversion Software v2.17 
			removes these bases and places them into the read name in the FASTQ files.			
	"""

	#If no sample sheet is provided, all reads are saved in Undetermined_S0_ FASTQ files (UG), i.e. Undetermined_S0_L001_R1_001.fastq.gz or Undetermined_S0_L001_R2_001.fastq.gz.
	#Sample_ID and Sample_Name may only contain alpha-numerics and '-' and '_'.
	#It is possible to assign samples without index to Sample_ID or other identifiers by leaving the Index field empty.
	#SAMPLE SHEET DETAILS
	# 1) Sample_ID is required and must be unique within a lane
	#	2) FASTQ files are named like so:
	#      <SampleName>_S1_L001_R1_001.fastq.gz 
	#    Where SampleName is optional. The sample number, here S1, is a "numeric assignment based on the order in the sample sheet that a sample ID first appeared in a given lane".
	#    This numbering starts at 1. 0 is reserved for the unmatched reads FASTQ file.

	#bcl2fastq2 Conversion Software v2.17 uses the following sample sheet columns in the [Data] section.
		#1) Sample_Project - If specified, a directory with the specified name is created and FASTQ files are stored there. Multiple samples can use the same project.
		#2) Lane - If specified, FASTQ files are generated only for those samples with the specified lane number.
		#3) Sample_ID - ID of the sample. Must be unique within a given lane.
		#4) Sample_Name - Descriptive name of the sample
		#5) index - Index sequence
		#6) index2 - Index sequence for index 2, if using dual indexing

	#NOTE: If the Sample_ID and Sample_Name columns are both specified and do not match, the FASTQ files are placed in an additional subdirectory called <SampleId>. (UG)
	#SS Columns
	SAMPLE_PROJECT = "Sample_Project"
	LANE	= "Lane"
	SAMPLE_ID = "Sample_ID"
	SAMPLE_NAME = "Sample_Name"
	INDEX = "index"
	INDEX2 = "index2"

	#Default sample name if not multiplexed lane:
	NO_INDEX = "NoIndex"

	SS_COLUMNS = [ #orderd as seen in the SS
		SAMPLE_PROJECT,
		LANE,
		SAMPLE_ID,
		SAMPLE_NAME,
		INDEX,
		INDEX2 ]

	def __init__(self,bcl2fastqOutputDir,sampleSheet):
		"""
		Args : bcl2fastqOutputDir - The output directory used in the demultiplexing command.
					 sampleSheet - File path to the SampleSheet.csv file.
		"""
		self.outdir = bcl2fastqOutputDir
		self.sampleSheet = self.parseSampleSheet(sampleSheet)

	def parseSampleSheet(self,sampleSheet):
		"""
		The sample sheet needs to have a header line, b/c bcl2fastq will read past the first line.
		This function requires the presence of the following fields:
			1) Lane,
			2) SampleID,
			3) Project

		For Each project specified in the samplesheet, a directory will be created by that name. A subdirectory of the project by the name of the provided
		Sample_ID will only created if Sample_Name is provided and different from the value of the Sample_ID.

		Args : sampleSheet - File path to the SampleSheet.csv file.
		Returns : list of dicts. Each dict describes a row of the sample sheet. The keys of a dict are the field names.
		"""
		rows = []	
		fh = open(sampleSheet,'r')
		for line in fh:
			if line.startswith("[Data]"):
				break
		header = fh.readline().rstrip("\n").split(",")
		#the rest of the lines are sample lines
		for sampleLine in fh:
			sampleLine = sampleLine.rstrip("\n").split(",")
			entry = {}
			index = 0
			for columnName in self.SS_COLUMNS:
				index += 1
				entry[columnName] = sampleLine[index]
			if not entry[self.LANE]:
				raise SampleSheetException("Missing value for 'Lane' field in Sample Sheet {samplesheet} in sampleLine {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			if not entry[self.SAMPLE_ID]:
				raise SampleSheetException("Missing value for 'SampleID' field in Sample Sheet {samplesheet} in sampleLine {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			if not entry[self.SAMPLE_PROJECT]:
				raise SampleSheetException("Missing value for 'SampleProject' field in Sample Sheet {samplesheet} in sampleLine {line}.".format(sampleSheet=sampleSheet,line=",".join(line)))
			rows.append(entry)
		return rows

	def getFastqFiles(self,sampleSheetEntry):
		"""
	  This numbering starts at 1. 0 is reserved for the unmatched reads FASTQ file.
		According to the v2.17 UG, bc2fastq names FASTQ files like so:
			<SampleName>_S1_L001_R1_001.fastq.gz
	  where SampleName is optional. The sample number, here S1, is a "numeric assignment based on the order in the sample sheet that a sample ID first appeared in a given lane".
		This numbering starts at 1. 0 is reserved for the unmatched reads FASTQ file.

		Function : 
		Args     : sampleSheetEntry   - dict. reperesenting a row from the SampleSheet.csv file that was used in the demultiplexing.
	                                  Should be formatted as one of the dicts stored in the list returned by parseSampleSheet().
		Returns  : list of FASTQ files that belong to the sampleSheetEntry.
		"""
		project = sampleSheetEntry[self.SAMPLE_PROJECT]
		sampleID = sampleSheetEntry[self.SAMPLE_ID]
		sampleName = sampleSheetEntry[self.SAMPLE_NAME]
		lane = sampleSheetEntry[self.LANE]
		index = sampleSheetEntry[self.INDEX]
	
		projectDir = project
		path = os.path.join(self.outdir,projectDir)
		sampleDir = None
		if sampleID != sampleName:
			sampleDir = sampleID
			path = os.path.join(path,sampleDir)
		print("Looking for FASTQ files in path {path}".format(path=path))
		globPattern = os.path.join(path,sampleName + "_" + "*.fastq.gz")
		fqfiles = glob.glob(globPattern)
		return fqfiles

	def filterSampleSheetEntries(self,entries,lanes):
		pass

	def getFastqFileReadNumber(self,fastqfile):
		pass
