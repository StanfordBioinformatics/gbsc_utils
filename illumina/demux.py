import fnmatch
import os

def getFastqFilePaths(outdir):
	"""
	Function : Finds the paths to all FASTQ files output by bcl2fastq.
	Args     : outdir - The output directory specified by the --output-dir argument of bcl2fastq (or the older configureBclToFastq.pl)
	Returns  : list. Each eleming is a string containing the path to a FATQ file.
	"""
	res = []
	for root, dirnames, filenames in os.walk(outdir):
		for filename in fnmatch.filter(filenames, '*.fastq.gz'):
			res.append(os.path.join(root, filename))
	return res

	
def getBarcodeFromSampleNumber(sampleSheet,sampleNumber):
	"""
	Function : Given a sample sheet that is formatted for the v2 (bcl2fastq) demultiplexer, retrieves the barcode for a given sample number.$
	Args     : sampleSheet - path to the SampleSheet.
				     sampleNumber - str. The sample number in the FASTQ file output by bcl2fatq2. For exaple, S0 for undetermined reads, or S1, ...
	Returns : str.
	"""
	if sampleNumber == "S0":
		return "Undetermined"

	sampleNumber = int(sampleNumber.lstrip("S"))
	dico = {}
	fh = open(sampleSheet)
	parsedSampleNumber = 0
	for line in fh:
		line = line.strip("\n")
		if not line:
			continue
		if line.startswith("[Data]"):
			continue
		if line.startswith("Sample_Project"): #then header line
			continue
		parsedSampleNumber += 1
		line = line.split(",")
		index1 = line[4]
		index2 = line[5]
		barcode = index1
		if index2:
			barcode += "-" + index2
		lane = line[1]
		if lane not in dico:
			dico[lane] = {}
		sampleId = line[2]
		if sampleId not in dico[lane]:
			dico[lane][sampleId] = 1
		if sampleNumber == parsedSampleNumber:
			print(barcode)
			print(sampleId)
			return barcode


if __name__ == "__main__":
	import sys
	getBarcodeFromSampleNumber(sys.argv[1], sys.argv[2])
