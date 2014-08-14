###
#AUTHOR: Nathaniel Watson
###


import re
import os

oldRunsArchive = "/srv/gs1/projects/scg/Archive/IlluminaRuns/"
newRunsArchive = "/srv/gsfs0/projects/seq_center/Illumina/RawDataArchive"
splitLaneReg = re.compile(r'_L\d_')
getLaneReg = re.compile(r'_(L\d)_')

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
	Function : Given a run name that begins with a data of the format YYMMDD, i.e. 120124_ROCKFORD_00123_FC64DHK,
						 parses out the year and and month.
	Args     : The run name
	Returns  : two-item tuple. The first item is the four-ditig year. The second is the month as a lower-case three-letter string (abbreviation).
	"""
	digits = run.split("_")[0]
	year = "20" + digits[:2]
	month = months[digits[2:4]]
	return (year,month)

def getArchivePath(run):
	"""
	Function : Calculates the absolute directory path to a run. First checks oldRunsArchive, the newRunsArchive (constants).
	Args     : Run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
	Returns  : str, or the None object.
	"""
	year,month = getRunYearMonth(run)
	newArchiveDir = os.path.join(newRunsArchive,year,month,run)
	if os.path.exists(newArchiveDir):
		return newArchiveDir
	else:
		oldArchiveDir = os.path.join(oldRunsArchive,year,month,run)
		if os.path.exists(oldArchiveDir):
			return oldArchiveDir
		else:			
			raise OSError("Archive for run {run} does not exist. Checked old archive path {oldArchiveDir} and new archie path {newArchiveDir}.".format(run=run,oldArchiveDir=oldArchiveDir,newArchiveDir=newArchiveDir))

def getBamFile(runName,archive,fileName,log=None):
	lane = getLaneReg.search(fileName).groups()[0]
	path1 = os.path.join(os.path.join(archive,fileName))
	if os.path.exists(path1):
		return path1
	path2 = os.path.join(archive,lane,fileName)
	if os.path.exists(path2):
		return path2
	else:
		if log:
			log.write(runName + "\t" + archive + "\t" + lane + "\t" + fileName + "\n")
		return None
