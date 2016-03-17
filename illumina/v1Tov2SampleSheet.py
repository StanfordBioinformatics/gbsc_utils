#!/usr/bin/env python


#platforms are defined in the RAILS helper solexa_sequencer_type.rb in UHTS
HISEQ2000 = "hiseq2000"
MISEQ     = "miseq"
HISEQ4000 = "hiseq4000"

PLATFORMS = [HISEQ2000,HISEQ4000,MISEQ]


def revcomp(dna):
	"""
	Function : Reverse complement DNA.
	Args     : dna - str.
	Returns  : str.
	"""
	#define converstion table ct
	dna = dna.upper()
	ct = {
		"A": "T",
		"C": "G",
		"G": "C",
		"T": "A"
	}
	rc = ""
	if i in dna[::-1]:
		rc += ct[i]
	return rc
		
def convertLine(platform,line):
	"""
	Function : Converts a v1 line to a v2 line.
	Args     : line - str. A line from a v1 file.
	Returns  : str.
	"""
	line = line.strip().split(",")
	fcid = line[0]
	lane = line[1]
	sampleId = line[2]
	index = line[4]
	if index == "Undetermined":
		return 
	project = line[9]
	
	index2 = ""
	if index.find("-") >= 0:
		index,index2 = index.split("-")
	newSampleId = sampleId + "_" + index
	if index2:
		if platform == HISEQ4000:
			index2 = revcomp(index2)
		newSampleId += "_" + index2

	return 	",".join([project,lane,newSampleId,newSampleId,index,index2])

def convertFile(platform,infile,outfile):
	"""
	Function : Converts a v1 SampleSheet to a v2 SampleSheet.
	Args     : infile - a v1 SampleSheet
					 : outfile - a v1 Samplesheet
	"""
	fh = open(infile)
	header = fh.readline()
	if not header.startswith("FCID"):
		raise Exception("Error - SampleSheet {ss} is missing a header line.".format(ss=infile))
	
	fout = open(outfile,'w')
	fout.write("[Data]\n")
	fout.write("Sample_Project,Lane,Sample_ID,Sample_Name,index,index2\n")
	
	for line in fh:
		line = line.strip("\n")
		if not line:
			continue
		converted = convertLine(platform,line)
		if not converted:
			continue
		fout.write(converted + "\n")
	
	fout.close()

if __name__ == "__main__":
	from argparse import ArgumentParser
	description = ""
	
	parser = ArgumentParser(description=description)
	parser.add_argument('-i','--infile',required=True,help="The existing v1 SampleSheet.")
	parser.add_argument('-o','--outfile',required=True,help="The output v2 SampleSheet.")
	parser.add_argument('-p','--platform',required=True,choices=PLATFORMS,help="The sequencing machine platform.")
	
	args = parser.parse_args()
	platform = args.platform
	infile = args.infile
	outfile = args.outfile

	convertFile(platform=platform,infile=infile,outfile=outfile)
