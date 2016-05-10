import os
import sys
import logging
import pdb
import datetime

from argparse import ArgumentParser
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler(filename="error.txt",mode="w")
fh.setLevel(logging.ERROR)
logger.addHandler(ch)
logger.addHandler(fh)

#modules to load: module load jsonwf/current python/2.7.9

MAIL_TO = "nathankw@stanford.edu"
#JSONWF_INSTANCES env var defined in the jsonwf/current environment module
DEFAULT_CONF_FILE = os.path.join(os.getenv("JSONWF_INSTANCES"),"bwa-mem.json")

description = "Runs the bwa-mem JsonWf instance in batch. A tab-delimited file must be provided, where each line specifies a paired-end mapping rqeuest on a pair of FASTQ files."
parser = ArgumentParser(description=description)
parser.add_argument('-i','--infile',required=True,help="The tab-delimited input file specifying which paired-end FASTQ files to map. The columns are: 1) path to read1, 2) path to read2, 3) name of the output SAM file. Must have a .sam extension. The directory path to this output file will be used as the value of the --outdir argument to jsonWorkflow.py.")
parser.add_argument('-c','--conf-file',default=DEFAULT_CONF_FILE,help="The JsonWf conf file. Default is $(default)s. You can provide your own if you have customized the default.")

args = parser.parse_args()

infile = args.infile
confFile = args.conf_file
fh = open(infile)
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	read1,read2,sam = line.split("\t")
	modtime = datetime.datetime.fromtimestamp(os.path.getmtime(sam))
	#if os.path.exists(sam) and modtime.date() != datetime.datetime.now().date():
	if os.path.exists(sam):
		continue
	for i in read1,read2:
		if not os.path.exists(i):
			raise Exception("FASTQ file {i} does not exist!")
	barcode = read1.rsplit("_",3)[-3]
	sjmFile = sam.rstrip(".sam") + ".sjm"
	if os.path.exists(sjmFile):
		os.remove(sjmFile)
	outdir = os.path.dirname(sjmFile)
	cmd = "jsonWorkflow.py -c " + confFile  + " -s " + sjmFile + " --mail-to " + MAIL_TO + " --outdir " + outdir
	cmd += " --run"
	cmd += " read1={read1} read2={read2} samFile={sam}".format(read1=read1,read2=read2,sam=sam)
	logger.info("Running command {cmd}".format(cmd=cmd))
	popen = subprocess.Popen(cmd,shell=True)
	stdout,stderr = popen.communicate()
	retcode = popen.returncode
	if retcode:
		logger.error("JsonWf command {cmd} failed with retcode {retcode} stdout is {stdout}. stderr is {stderr}.".format(cmd=cmd,retcode=retcode,stdout=stdout,stderr=stderr))	
		
