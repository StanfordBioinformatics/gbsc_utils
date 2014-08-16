###
#AUTHOR: Nathaniel Watson
###

import argparse
import xml.etree.ElementTree as etree 
import operator
import glob
import os


class Field:
	def __init__(self,pos,value=False):
		self.pos = pos

dico = {
	"RunID": Field(pos=1),
	"ControlSoftware": Field(pos=2),
	"RTAVersion": Field(pos=3),
	"ClusterKit": Field(pos=4),
	"BarcodeKit": Field(pos=5),
	"SBSKit": Field(pos=6),
	"PairedEnd": Field(pos=7),
	"R1Cycles": Field(pos=8),
	"R2Cycles": Field(pos=9),
	"IR1Cycles": Field(pos=10),
	"IR2Cycles": Field(pos=11),
	"ReadsRaw": Field(pos=12),
	"ReadsPF": Field(pos=13),
	"ReadsPF%": Field(pos=14)
}

def rmSpaces(txt):
	txt = "_".join(txt.split())
	return txt

posAttGetter = operator.attrgetter('pos')
elementOneGetter  = operator.itemgetter(1)

def getItem(x):
	field = elementOneGetter(x)
	pos = posAttGetter(field)
	return pos

x = list(dico.items())[0]
header = [x[0] for x in sorted(list(dico.items()),key = getItem)]

def calcDemStats(demFile):
	tree = etree.parse(demFile)
	root = tree.getroot()
	chipResSum = root.find("ChipResultsSummary")
	childs =  chipResSum.getchildren()
	pf = float(chipResSum.find("clusterCountPF").text)
	raw = float(chipResSum.find("clusterCountRaw").text)
	pfPerc = str("{:.2f}".format(pf/raw * 100)) + "%"
		
	dico["ReadsRaw"].value = str(int(raw))
	dico["ReadsPF"].value = str(int(pf))
	dico["ReadsPF%"].value = str(pfPerc)

desc = "Outputs stats for an Illumina sequencing run. Stats come from specific tags in the XML files runParameters.xml (which is in top-level run directory) and DemultiplexedBustardSummary.xml (which is in each demultiplexed directory). If the stats file doesn't exist or exists with 0 size, then the header line is added. This allows for multiple runs of this program to output to the same stats file, w/o repeated header lines. Currently, only HiSeq runs are supported.  Support will be added for MiSeq runs. The stats that are output are listed below.\nOutput Stats:"
count = -1
for i in header:
	count += 1
	desc += "\t{count}) {i}\n".format(count=count,i=i)

parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-d',help="The DemultiplexedBustardSummary.xml file. Required when --run not specified.")
parser.add_argument("-r",help="The runParamaters.xml file. Required when --run not specified.")
parser.add_argument('-o','--outfile',required=True,help="Output file")
parser.add_argument('-a','--append-output',default="w",action="store_const",const="a",help="Don't overwrite --outfile if it exists already, rather, append to it.")
parser.add_argument('--run-name',help="Run Name. Output statistics for all demultiplexed directories in this specified run. Required when -d and -r not supplied.")
parser.add_argument("--runs-path",default="/srv/gsfs0/projects/seq_center/Illumina/RunsInProgress",help="The directory path the a run specified with --run (not including --run itself). Defaults to $(default)s")
parser.add_argument("--demultiplex-dir-prefix",default="Unaligned",help="Used only when --run-name specified. Demultiplexed directory prefix name. For each demultiplexed directory within the run directory that matches this prefix, statistics will be gathered for it. Default is $(default)s.")

args = parser.parse_args()
runName = args.run_name
runsPath = args.runs_path
demDirPrefix = args.demultiplex_dir_prefix
demFiles = args.d
if demFiles:
	demFiles = [demFiles]
else:
	demFiles = []
runFile = args.r
if (runName and demFiles) or (runName and runFile):
	parser.error("You must supply the --run argument or both -d and -r, not any other combination.")
if runFile and not demFiles:
	parser.error("You must supply the -d argument when -r is supplied.")
if demFiles and not runFile:
	parser.error("You must supply the -r argument when -d is supplied.")


if runName:
	runsPath = os.path.join(runsPath,runName)

outfile = args.outfile
mode = args.append_output

x = list(dico.items())[0]
header = [x[0] for x in sorted(list(dico.items()),key = getItem)]

outputHeader = False
if not os.path.exists(outfile) or not os.getsize(outfile):
	outputHeader = True
fout = open(outfile,mode)
if outputHeader:
	for i in header:
		fout.write(i + "\t")
	fout.write("\n")

if runName:
	runFile = os.path.join(runsPath,"runParameters.xml")

tree = etree.parse(runFile)
root = tree.getroot().find("Setup")

dico["RunID"].value = root.find("RunID").text
dico["PairedEnd"].value = root.find("PairEndFC").text
dico["R1Cycles"].value = root.find("Read1").text
dico["R2Cycles"].value = root.find("Read2").text
dico["IR1Cycles"].value = root.find("IndexRead1").text
dico["IR2Cycles"].value = root.find("IndexRead2").text
dico["BarcodeKit"].value = rmSpaces(root.find("Index").text)
try:
	dico["ClusterKit"].value = rmSpaces(root.find("Pe").text)
except AttributeError:
	dico["ClusterKit"].value = ""

dico["SBSKit"].value = rmSpaces(root.find("Sbs").text)
appName = rmSpaces(root.find("ApplicationName").text)
appVersion = root.find("ApplicationVersion").text
dico["ControlSoftware"].value = appName + ":" + appVersion
dico["RTAVersion"].value = root.find("RTAVersion").text

demDirs = glob.glob(os.path.join(runsPath,demDirPrefix) + "*")
for d in demDirs:
	demFile = os.path.join(d,"DemultiplexedBustardSummary.xml")
	demFiles.append(demFile)
for d in demFiles:
	calcDemStats(d)
	for i in header:
		fout.write(dico[i].value + "\t")
	fout.write("\n")
fout.close()
