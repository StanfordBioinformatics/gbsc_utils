import os

from argparse import ArgumentParser

#modules to load: module load jsonwf/current
MAIL_TO = "nathankw@stanford.edu"

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-i',required=True,help="The tab-delimited input file specifying which paired-end FASTQ files to map. The columns are: 1) path to read1, 2) path to read2, 3) path to output directory.")

args = parser.parse_args()

infile = args.i
fh = open(infile)
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	read1,read2,outdir = line.split("\t")
	for i in read1,read2:
		if not os.path.exists(i):
			raise Exception("FASTQ file {i} does not exist!")
	barcode = read1.rsplit("_",3)[-3]
	sjmFile = os.path.join(outdir,"map_" + barcode + ".sjm")
	cmd = "jsonWorkflow.py -c " + os.getenv("JSONWF_INSTANCES") + "--run -s " + sjmFile + " --mail-to " + MAIL_TO
	cmd += " read1={read1} read2={read2}".format(read1=read1,read2=read2)
	subprocess.Popen(cmd,shell=True)
		
