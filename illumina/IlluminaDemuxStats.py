###
#AUTHOR: Nathaniel Watson
###

import argparse
import xml.etree.ElementTree as etree 
import operator
import glob
import os


class Field:
	def __init__(self,pos,value=""):
		self.pos = pos
		self.value = value

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

desc = "Outputs stats for an Illumina sequencing run. Stats come from specific tags in the XML files runParameters.xml (which is in top-level run directory). The file DemultiplexedBustardSummary.xml (which is in the output directory of the v1 version of the demultiplexer) was originally also parsed for the additional stats fields of the number of raw reads, PF reads, and %PF reads, however, this is no longer the case. The reason is that the equivalent file ConversionStats.xml output in V2 of the demultiplexer doens't contain these overall summary stats, rather just the per-tile based stats, and in order for this script to support output from v1 and v2, it will only parse stats from the runParameters.xml file. If the output stats file doesn't exist or exists with 0 size, then the header line is added. This allows for multiple runs of this program to output to the same stats file, w/o repeated header lines. Currently, only HiSeq runs are supported.  Support will be added for MiSeq runs. The stats that are output are listed below.\nOutput Stats:"
count = -1
for i in header:
	count += 1
	desc += "\t{count}) {i}\n".format(count=count,i=i)

parser = argparse.ArgumentParser(description=desc,formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-r",help="The runParamaters.xml file. Required when --run not specified.")
parser.add_argument('-o','--outfile',required=True,help="Output file")
parser.add_argument('-a','--append-output',default="w",action="store_const",const="a",help="Don't overwrite --outfile if it exists already, rather, append to it.")
parser.add_argument('--run-name',help="Run Name. Output statistics for all demultiplexed directories in this specified run. Required when -c and -r not supplied.")
parser.add_argument("--runs-path",default="/srv/gsfs0/projects/seq_center/Illumina/RunsInProgress",help="The directory path the a run specified with --run (not including --run itself). Defaults to $(default)s")
#parser.add_argument("--demux-dir",help="Full path. Used only when --run-name specified. Essentially, this is the value of the --output-dir argument of the demultiplexer.")

args = parser.parse_args()
runName = args.run_name
runsPath = args.runs_path
#demuxDir = args.demux_dir
runParamsFile = args.r

if runName:
	runDir = os.path.join(runsPath,runName)
	runParamsFile = os.path.join(runDir,"runParameters.xml")

#calcDemStats(bustardSummaryFile)

outfile = args.outfile
mode = args.append_output

tree = etree.parse(runParamsFile)
root = tree.getroot().find("Setup")

dico["RunID"].value = root.find("RunID").text
dico["R1Cycles"].value = root.find("Read1").text
dico["R2Cycles"].value = root.find("Read2").text
dico["IR1Cycles"].value = root.find("IndexRead1").text
dico["IR2Cycles"].value = root.find("IndexRead2").text
pairedEnd = "No"
if int(dico["R2Cycles"].value) > 0:
	pairedEnd = "Yes"
dico["PairedEnd"].value = pairedEnd
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

header = [x[0] for x in sorted(list(dico.items()),key = getItem)]

outputHeader = False
if not os.path.exists(outfile) or not os.path.getsize(outfile):
	outputHeader = True

fout = open(outfile,mode)

if outputHeader:
	headerLine = ""
	for i in header:
		headerLine += i + "\t"
	headerLine.rstrip("\t")
	fout.write(headerLine + "\n")

for i in header:
	fout.write(dico[i].value + "\t")
fout.write("\n")
fout.close()
