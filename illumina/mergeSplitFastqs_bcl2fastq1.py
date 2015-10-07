import gzip
import os
from gbsc_utils.illumina import demultiplexing
from gbsc_utils.gbsc_utils import createSubprocess
from argparse import ArgumentParser



description = "Merges FASTQ files by sample that were created by bcl2fastq 1.8.4. Relies on the FASTQ file naming and directory structure endorsed by bcl2fsatq 1.8.4."
parser = ArgumentParser(description=description)
parser.add_argument('-s','--sample-sheet',required=True,help="The sample sheet that was used for the demultiplexing.")
parser.add_argument('-b','--bcl2fastq-output-dir',required=True,help="The output directory used during the demultiplexing.")
parser.add_argument('-o','--outdir',required=True,help="The output directory to contain the merged FASTQ files.")
parser.add_argument('-l','--lanes',type=int,nargs="+",help="The lane(s) whose FASTQs need merging. Enteral mutiple with a space in-between.")

args = parser.parse_args()
ss = args.sample_sheet
bcl2fastqOutputDir = args.bcl2fastq_output_dir
outdir = args.outdir
lanes = args.lanes

sffe = { #supported FASTQ File Extensions
		   "fq": ".fq",
		"fastq": ".fastq",
		   "gz": ".gz"
	}
d = demultiplexing.V1(bcl2fastqOutputDir=bcl2fastqOutputDir,sampleSheet=ss)
for i in d:
	if lanes:
		currentLane = i[d.LANE]
		if currentLane not in lanes:
			continue
	print("Processing sample {sample}".format(sample=i))
	fqs = d.getFastqFiles(i)
	read1Outfile = os.path.join(outdir,i[d.SAMPLE_ID] + "_" + i[d.INDEX] + "_L" + str(i[d.LANE]) + "_R1_combined.fastq")
	read2Outfile = os.path.join(outdir,i[d.SAMPLE_ID] + "_" + i[d.INDEX] + "_L" + str(i[d.LANE]) + "_R2_combined.fastq")
	if os.path.exists(read1Outfile):
		os.remove(read1Outfile)
	if os.path.exists(read2Outfile):
		os.remove(read2Outfile)

	for f in fqs:
		readNum = d.getFastqFileReadNumber(f)
		if readNum == 1:
			outfile = read1Outfile
		elif readNum == 2:
			outfile = read2Outfile
		else:
			raise Exception("Unknown read number for FASTQ file {fqfile}".format(fqfile=f))

		if f.endswith(sffe["gz"]):
			cmd = "zcat {f} >> {outfile}".format(f=f,outfile=outfile)
			print(cmd)
			createSubprocess(cmd=cmd,checkRetcode=True)
		elif f.endswith(sffe["fq"]) or f.endswith(sffe["fastq"]):
			cmd = "cat {f} >> {outfile}".format(f=f,outfile=outfile)
			print(cmd)
			createSubprocess(cmd=cmd,checkRetcode=True)
		else:
			raise Exception("Unsupported extension for FASTQ file {fqfile}; only the following extensions are supported: {supported}".format(fqfile=f,supported=sffe.values()))
