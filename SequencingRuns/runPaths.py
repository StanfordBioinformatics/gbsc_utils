###
#AUTHOR: Nathaniel Watson
###


import re
import os

oldRunsArchive = "/srv/gs1/projects/scg/Archive/IlluminaRuns/"
newRunsArchive = "/srv/gsfs0/projects/seq_center/Illumina/RawDataArchive"
pubDir = "/srv/gsfs0/projects/seq_center/Illumina/PublishedResults"
oldPubDir = "/srv/gs1/projects/scg/Archive/IlluminaRuns/" #"/srv/gs1/projects/scg/Archive/IlluminaRuns"
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
	Function : Calculates the absolute directory path to a run in the archive directory. First checks newRunsArchive, then oldRunsArchive (constants).
	Args     : run - Run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
	Returns  : str
	Raises   : OSError if run can't be located.
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
			raise OSError("Archive for run {run} does not exist. Checked old archive path {oldArchiveDir} and new archive path {newArchiveDir}.".format(run=run,oldArchiveDir=oldArchiveDir,newArchiveDir=newArchiveDir))



def getPubPath(run):
	"""
	Function : Calculates the absolute directory path to a run in the published results directory.
	Args     : run - run name (i.e. 120124_ROCKFORD_00123_FC64DHK)
	Returns  : str
	Raises   : OSError if run can't be located.
	"""
	year,month = getRunYearMonth(run)
	pubdir = os.path.join(pubDir,year,month,run)
	rundir = pubdir
	if not os.path.exists(pubdir):
		oldpubdir = os.path.join(oldPubDir,year,month,run)	
		rundir = oldpubdir
		if not os.path.exists(oldpubdir):
			raise OSError("Published directory for run {run} does not exist. Checked old published path {oldpubdir} and new published path {pubdir}.".format(run=run,oldpubdir=oldpubdir,pubdir=pubdir))
	return rundir

def getBamFile(rundir,fileName,log=None):
	"""
	Function : Tries to find a BAM file in a given run directory in the given rundir. The main purpose of this function is to check for the BAM file in two places: first, immediately
					   within the run directory (where they used to be back in 2012), second, within a lane subdirectory.
	Args     : rundir - path to the run directory (i.e. could be a published path or an archive path)
						 fileName - the name of the BAM file to look for (no directory path prefix)
						 log - a file handle open for writing. Used to track which BAMS are missing so that they can be later created if need-be.
	"""
	runName = os.path.basename(rundir)	
	lane = getLaneReg.search(fileName).groups()[0]
	path1 = os.path.join(rundir,fileName)
	if os.path.exists(path1):
		return path1
	path2 = os.path.join(rundir,lane,fileName)
	if os.path.exists(path2):
		return path2
	else:
		if log:
			log.write(runName + "\t" + rundir + "\t" + lane + "\t" + fileName + "\n")
		return None
