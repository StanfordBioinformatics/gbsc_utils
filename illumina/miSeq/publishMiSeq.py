#!/srv/gs1/software/python/3.2.3/bin/python3

###AUTHOR###
#Nathaniel Watson
###DATE####
#Feb. 11, 2014



import os
import sys
import subprocess
import argparse
import glob
import confparse

rsyncLogExt = "_rsyncLog.txt"
ssName = "SampleSheet.csv" #samplesheet name

def makeLogFileName(infile,extension=rsyncLogExt):
	log = os.path.join(dest,os.path.basename(infile) + extension)
	return log

parser = argparse.ArgumentParser(description="Publishes a MiSeq run and creates an index.html file for viewing and downloading links. In addition, an email template file is created in the published run directory.")
parser.add_argument('--run',required=True,help="Run name (i.e. 140121_SPENSER_0046_000000000-A74LR).")
parser.add_argument('--conf',default="/srv/gs1/software/gbsc/nathankw/conf/global.txt",help="Path to config file. Default is %(default)s.")
parser.add_argument('--no-email',action="store_true",help="Presence of this option indicates to not output an email template in the published directory for the run.")
parser.add_argument('--name',required=True,help="Name of the person you will send the results to.")
parser.add_argument('--no-copy',action="store_true",help="Presence of this option indicates that only the email template and HTML file with the links to the data are to be generated, and no copying of the fastq files from the rundir to the pubdir.")
args = parser.parse_args()

months = {}
months[1] = "jan"
months[2] = "feb"
months[3] = "mar"
months[4] = "apr"
months[5] = "may"
months[6] = "jun"
months[7] = "jul"
months[8] = "aug"
months[9] = "sep"
months[10] = "oct"
months[11] = "nov"
months[12] = "dec"

run = args.run
noemail = args.no_email
name = args.name
confFile = args.conf
nocopy = args.no_copy
ddate = run.split("_")[0]
yr = "20" + ddate[:2]
mo = int(ddate[2:4]) #this automatically strips a leading 0
moText = months[mo]


conf = confparse.Parse(confFile)
runDir = conf['illuminaRuns']
pubDir = conf['illuminaPublished']
nummelPub = conf['nummelPub'] #path to published directory as seen from nummel web server

src = os.path.join(runDir, run, 'Data', 'Intensities', 'BaseCalls')
dest = os.path.join(pubDir,yr,moText, run)
if not os.path.exists(dest):
	os.mkdir(dest,int("02775",8)) #python requires an int, so I convert from octal to int

cmd = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),"./publish_fastq.sh {dest}".format(dest=dest))
subprocess.check_call(cmd,shell=True)
fout = open(os.path.join(dest,"HTML_Complete.txt"),'w')
fout.close()

if not nocopy:
	sampleSheet = os.path.join(src,ssName)
	log=makeLogFileName(sampleSheet)
	subprocess.check_call("rsync -av {sampleSheet} {dest} &> {log}".format(sampleSheet=sampleSheet,dest=dest,log=log),shell=True)
	for fqFile in glob.glob(os.path.join(src,"*.fastq*")):
		log = makeLogFileName(fqFile)
		subprocess.check_call("rsync -av {fqFile} {dest} &> {log}".format(fqFile=fqFile,dest=dest,log=log),shell=True)
		##subprocess.check_call will raise CalledProcessError if exit code is non-zero. The CalledProcessError object will have the return code in the returncode attribute.
	
	fout = open(os.path.join(dest,"Rsync_Complete.txt"),'w')
	fout.close()
	for i in glob.glob(os.path.join(dest,"*" + rsyncLogExt)):
		os.remove(i)

if not noemail:
	fout = open(os.path.join(dest,"email.txt"),'w')
	nummelPath = os.path.join(nummelPub,yr,moText,run)
	fout.write("""
Sequencing results for MiSeq run {run}
Hi {name},

The results from your sequencing your run {run} can be found at the link below:

{nummelPath}/index.html

Please refer to the Sample Sheet available at the above link for help relating barcodes to sample names.

Let me know if you have any questions.

Regards,
Nathaniel
""".format(run=run,name=name,nummelPath=nummelPath))
