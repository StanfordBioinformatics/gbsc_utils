###
#AUTHOR: Nathaniel Watson
###


import re
import json
import os
import datetime
from gbsc_utils import gbsc_utils
import glob

conf = os.path.join(os.path.dirname(__file__),"conf.json")
conf = json.load(open(conf,'r'))

runsInProgressDir = conf["runsInProgressDir"]
oldRunsArchive = conf["oldRunsArchive"]
newRunsArchive = conf["newRunsArchive"]
rawArchiveExtension = conf["rawArchiveExtension"]
analysisArchiveExtension = conf["analysisArchiveExtension"]
pubDir = conf["pubDir"]
oldPubDir = conf["oldPubDir"]
splitLaneReg = re.compile(r'_L\d_')
getLaneReg = re.compile(r'_(L\d)_')
copyCompleteSentinalFile = conf["copyCompleteSentinalFile"] #the name of the file that signals completetion of the copy of the run directory to SCG

modMinThreshold = 30 # modification minutes threshold

months = { 
  "01": "jan",
  "02": "feb",
  "03": "mar",
  "04": "apr",
  "05": "may",
  "06": "jun",
  "07": "jul",
  "08": "aug",
  "09": "sep",
  "10": "oct",
  "11": "nov",
  "12": "dec"
  }

ARCHIVE_STATE_NOT_STARTED = 0
ARCHIVE_STATE_IN_PROGRESS = 1
ARCHIVE_STATE_COMPLETE = 2

def parseLane(lane,stripLeadingL=False,stripLeadingZeros=True):
	"""
	Args    : lane - str. Lane number identifier in the form of an integer or with an "L" prefix followed by an integer. The integer may have 
                   preceeding zeros. i.e. the following are acceptable: L1, L001, 1, 001.
					  prefixWithL - bool. If True, checkes for the presence of a leading 'L' in lane. If no leading L found, one is added.
	          stripLeadingZeros - bool. If True, than any zeros found at the start of 'lane' (disregarding a potential leading 'L') and
	                 the first non-zero integer are removed.  
	Returns : str.
	"""
	lprefix = False
	if lane[0] == "L":
		lprefix = True
		lane = lane.lstrip("L")
	if stripLeadingZeros:
		lane = lane.lstrip("0")
	if stripLeadingL or not lprefix:
		return lane
	else:
		return "L" + lane
	

def getRunNameFlf(filename):
	"""
	Function : Given a file that has the lane information in it following the run name, parses out the lane number. Flf stands for "From Lane File".
	Args     : filename - str. A file name, i.e. 120124_ROCKFORD_00123_FC64DHK_L1_pf.bam.
	Returns  : str. The run name 
	Example  : call: getRunNameFlf"120124_ROCKFORD_00123_FC64DHK_L1_pf.bai")
						 return: "120124_ROCKFORD_00123_FC64DHK"
	"""
	runName = splitLaneReg.split(filename)[0]
	return runName
  

def getRunYearMonth(run):
	"""
	Function : Given a run name that begins with a date of the format YYMMDD, i.e. 120124_ROCKFORD_00123_FC64DHK,
						 parses out the year and and month.
	Args     : The run name
	Returns  : two-item tuple. The first item is the four-digit year. The second is the month as a lower-case three-letter string (abbreviation).
	"""
	digits = run.split("_")[0]
	year = "20" + digits[:2]
	month = months[digits[2:4]]
	return (year,month)

def getRunPath(run):
	"""
	Function : Returns the path of a run directory prefixed with the directory specifed by 'runsInProgressDir'.
	Args     : run - sequencing run name.
	Returns  : str.
	"""
	return os.path.join(runsInProgressDir,run)

def isCopyComplete(run):
	"""
	Funoction : Determines whether the copy of the sequencing run to SCG has completed. A copy is considered completed if the run directory path returned by getRunPath(run) or getPubDir(run) contains the copy complete sentinal file.
							getPubDir(run) is only tested if the former returns False.
							
	Args     : run - sequencing run name.
	Returns  : bool.
	"""
	rundir = ""
	try:
		rundir = getRunPath(run)
	except OSError:
		pass
	if os.path.exists(rundir):
		if os.path.exists(os.path.join(rundir,copyCompleteSentinalFile)):
			return True
	
	pubPath = ""
	try:
		pubPath = getPubPath(run)
	except OSError:
		pass
	if os.path.exists(pubPath):
		if os.path.exists(os.path.join(pubPath,copyCompleteSentinalFile)):
			return True
	return False

def getArchiveDir(run):
	"""
	Function : Calculates the archive directory path for a given run.
	Args     : run - Run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
	Returns  : str
	"""
	year,month = getRunYearMonth(run)
	archiveDir = os.path.join(newRunsArchive,year)
	if os.path.exists(archiveDir):
		return archiveDir
	else:
#		oldArchiveDir = os.path.join(oldRunsArchive,year,month,run)
#		if os.path.exists(oldArchiveDir):
#			return oldArchiveDir
		raise OSError("Expected archive path '{archiveDir}' for run {run} does not exist.".format(archiveDir=archiveDir,run=run))



def getPubPath(run,lane=None):
	"""
	Function : Calculates the absolute directory path to a run in the published results directory. If the lane argument is not None, then the returned directory 
						 path includes the lane directory.
	Args     : run - run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
						 lane - Lane number identifier in the form of an integer or with an "L" prefix followed by an integer. The integer may have
                    preceeding zeros. i.e. the following are acceptable: L1, L001, 1, 001.
	Returns  : str
	Raises   : OSError if run can't be located.
	"""
	year,month = getRunYearMonth(run)
	pubdir = os.path.join(pubDir,year,month,run)
	if lane:
		lane = parseLane(lane)
	rundir = pubdir
	if not os.path.exists(pubdir):
		oldpubdir = os.path.join(oldPubDir,year,month,run)	
		rundir = oldpubdir
		if not os.path.exists(oldpubdir):
			raise OSError("Published directory for run {run} does not exist. Checked old published path {oldpubdir} and new published path {pubdir}.".format(run=run,oldpubdir=oldpubdir,pubdir=pubdir))
	if lane:
		lanedir = os.path.join(rundir,lane)
		return lanedir
	return rundir

def getLaneStatsFile(run,lane):
	"""
	Function : Calculates the complete file path to a lane stats file.
	Args     : run - run name (i.e. 120124_ROCKFORD_00123_FC64DHK).
					 : lane - Lane number identifier in the form of an integer or with an "L" prefix followed by an integer. The integer may have 
                    preceeding zeros. i.e. the following are acceptable: L1, L001, 1, 001.
	Returns  : str.
	"""
	lane = parseLane(lane=lane,stripLeadingZeros=True)
	runPath = getPubPath(run)
	statsFile = os.path.join(runPath,run + "_" + lane + "_" + "stats.csv")
	return statsFile
	
	

def getBamFilePath(rundir,fileName):
	"""
	Function : Tries to find a BAM file in a given run directory in the given rundir. The main purpose of this function is to check for the BAM file in two places: first, immediately
					   within the run directory (where they used to be back in 2012), second, within a lane subdirectory. Checkes if they are gzip'd.
	Args     : rundir - path to the run directory (i.e. could be a published path or an archive path)
						 fileName - the name of the BAM file to look for (no directory path prefix) in the run directory specified by the rundir argument.
	"""
	runName = os.path.basename(rundir)	
	lane = getLaneReg.search(fileName).groups()[0] #i.e. L1
	path1 = os.path.join(rundir,fileName)
	if os.path.exists(path1):
		return path1
	elif os.path.exists(path1 + ".gz"):
		return path1 + ".gz"
	path2 = os.path.join(rundir,lane,fileName)
	if os.path.exists(path2):
		return path2
	elif os.path.exists(path2 + ".gz"):
		return path2 + ".gz"
	#for HiSeq 4000s that was run through the JsonWf pipeline at gbsc/gbsc_utils/bwa_pipeline/run.py 
	path3 = os.path.join(rundir,"bwa_mem",lane,fileName.split("_pf")[0] + ".coordSorted.clean.dedup.bam")
	print(path3)
	if os.path.exists(path3):
		return path3
	else:
		return None

def findAllBams(run,lane):
	"""
	Args : run  - str. run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
			   lane - Lane number identifier in the form of an integer or with an "L" prefix followed by an integer. The integer may have
      					preceeding zeros. i.e. the following are acceptable: L1, L001, 1, 001.
	"""
	
	lane = parseLane(lane=lane,stripLeadingZeros=True)
	runPath = getPubPath(run,lane=lane)
	globPat = os.path.join(runPath,"*_pf.bam*")
	bams =  glob.glob(globPat)
	return bams

def findAllFastqs(run,lane):	
	"""
	Args : run  - str. run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
			   lane - Lane number identifier in the form of an integer or with an "L" prefix followed by an integer. The integer may have
      					preceeding zeros. i.e. the following are acceptable: L1, L001, 1, 001.
	"""
	
	lane = parseLane(lane=lane,stripLeadingZeros=True)
	runPath = getPubPath(run,lane=lane)
	globPat = os.path.join(runPath,"*_pf.fastq*")
	fastqs =  glob.glob(globPat)
	return fastqs

#def rawArchiveDone(rundir):
#	"""
#	Function :
#	Args     : rundir - str. The run name (no directory path prefix).
#	Returns  : int. one of [ARCHIVE_STATE_NOT_STARTED, ARCHIVE_STATE_IN_PROGRESS, ARCHIVE_STATE_COMPLETE] 
#	"""
#	year,month = getRunYearMonth(rundir)	
#	archivePath = getArchiveDir(rundir)
#	rawArchive = os.path.join(archivePath,rundir + rawArchiveExtension)
#	if not os.path.exists(rawArchive):
#		return ARCHIVE_STATE_NOT_STARTED
#	else:
#		minutesSinceMod = gbsc_utils.getFileAgeMinutes(rawArchive)
#		if minutesSinceMod <= modMinThreshold: #consider in progress
#			return ARCHIVE_STATE_IN_PROGRESS
#		else:
#			return ARCHIVE_STATE_COMPLETE
	###NEW CODE: Check archiving_done flag on run object in UHTS. Check code in gbsc/gbsc_utils/uhts/uhts_utils.py

def analysisArchiveDone(rundir):
	"""
	Function :
	Args     : rundir -str. The run name (no directory path prefix).
	Returns  : int. One of [ARCHIVE_STATE_NOT_STARTED, ARCHIVE_STATE_IN_PROGRESS, ARCHIVE_STATE_COMPLETE]
	"""
	archivePath = getArchiveDir(rundir)
	analysisArchive = os.path.join(archivePath,rundir + analysisArchiveExtension)
	if not os.path.exists(analysisArchive):
		return ARCHIVE_STATE_NOT_STARTED
	else:
		minutesSinceMod = gbsc_utils.getFileAgeMinutes(analysisArchive)
		if minutesSinceMod <= 30: #consider in progress
			return ARCHIVE_STATE_IN_PROGRESS
		else:
			return ARCHIVE_STATE_COMPLETE
