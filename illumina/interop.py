###
#AUTHOR: Nathaniel Watson
###

import struct

class RawIntensities:
	"""
	Contains functionality to parse the binary interop files (currently only ExtractionMetricsOut.bin and CorrectedIntMetricsOut.bin).
	These files are used primarily for Illumina's Sequencing Analysis Viewer (SAV), which provides for real-time visualization of quality metrics that the 
  sequencing machine's real-time analysis software generates.
	"""
	EXTRACTION = "extraction"
	QUALITY = "quality"
	ERROR = "error" #ExtractionMetricsOut.bin
	TILE = "tile"
	CORRECTED = "corrected" #CorrectedIntMetricsOut.bin
	CONTROL = "control"
	IMAGE = "image"
	INDEX = "index"
	metricFiles = [EXTRACTION,QUALITY,ERROR,TILE,CORRECTED,CONTROL,IMAGE,INDEX]
	def __init__(self,metric,infile):
		"""
		Args: metric - case-insensitive str. The metric file. Must be one of the elements in self.metricFiles.
					infile - str. The Interop file that contains the raw intensities and FWHM scores. As of current (Jul, 2014), this is the ExtractionMetricsOut.bin file.
		"""
		self.fh = open(infile,'rb')
		self.metric = metric.lower()
		if self.metric not in self.metricFiles:
			raise TypeError("unknown metric file '{}'. Must be one of {}".format(self.metric,self.metricFiles))
		
		if self.metric == self.EXTRACTION:
			fmt = "=3H4f4HQ"
			byteCnt = 38
		elif self.metric == self.CORRECTED:
			fmt = "=12H6f"
			byteCnt = 48
		self.fmt = fmt
		self.byteCnt = byteCnt

	def fileVersion(self):
		self.fh.seek(0)
		byte = self.fh.read(1)
		return struct.unpack('=b',byte)[0]

	def recLength(self):
		self.fh.seek(1)
		byte = self.fh.read(1)
		return struct.unpack('=b',byte)[0]

	def writeRecs(self,outfile):
		fout = open(outfile,'w')
		for rec in self.records():
			rec = [str(x) for x in list(rec)]
			fout.write("\t".join(rec) + "\n")
		fout.close()

#	def records(self):
#			self.fh.seek(2)
#			while True:
#				bytes = self.fh.read(self.byteCnt)
#				if not bytes:
#					break
#				else:
#					yield struct.unpack(self.fmt,bytes)


	def records(self):
			bout = open("bytes.bin",'wb')
			self.fh.seek(2)
			while True:
				bytes = self.fh.read(self.byteCnt)
				if not bytes:
					break
				else:
					unpacked = struct.unpack(self.fmt,bytes)
					lane = int(unpacked[0])
					if lane == 0:
						bout.write(bytes)
						bout.write("\n")
					yield unpacked
			bout.close()
#example:
#from interop import *
#infile = "ExtractionMetricsOut.bin"
#raw = RawIntensities('extraction',infile)
#raw.writeRecs(outfile=infile.rstrip(".bin") + ".txt")
