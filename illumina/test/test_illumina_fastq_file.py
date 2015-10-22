import unittest
from ddt import ddt, data, unpack
from gbsc_utils.illumina.illumina_fastq_file import FastqFile,UnknownReadNumberException

"""
Tests functions that parse fields out of Illumina's FASTQ files as output by the bcl2fastq program. 

The FASTQ file naming format for bcl2fastq v1.8.4 is <sample name>_<barcode sequence>_L<lane>_R<read number>_<set
      number>.fastq.gz
See the bcl2fastq user guide for the meanings on the different fields.

The FASTQ file naming format for bcl2fastq v2.17 is, for example:  <SampleName>_S1_L001_R1_001.fastq.gz.	
See the bcl2fastq user guide for the meanings on the different fields.

The main differences b/w 1.8.4 and 2.17 is that in the latter, the set_number is always 0001, and instead of 
including the barcode sequence, it uses the sample number (see UG for details). Since the differences won't affect 
the illumina_fastq_file.FastqFile class, a test on a file output from either demultiplexer will produce the same result.
"""

@ddt
class TestFastqFile_isForwardReadFile(unittest.TestCase):

	def test_true(self):
		n = FastqFile("S60_CAGATC_L001_R1_003.fastq.gz")
		self.assertTrue(n.isForwardReadFile())


	def test_false(self):
		n = FastqFile("S60_CAGATC_L001_R2_003.fastq.gz")
		self.assertFalse(n.isForwardReadFile())

	def test_raises_UnknownReadNumberException(self):
		name = "S60_CAGATC_L001_R3_003.fastq.gz"
		self.assertRaises(UnknownReadNumberException,FastqFile,name)

class TestFastqFile_isReverseReadFile(unittest.TestCase):

	def test_true(self):
		n = FastqFile("S60_CAGATC_L001_R2_003.fastq.gz")
		self.assertTrue(n.isReverseReadFile())


	def test_false(self):
		n = FastqFile("S60_CAGATC_L001_R1_003.fastq.gz")
		self.assertFalse(n.isReverseReadFile())

	def test_raises_UnknownReadNumberException(self):
		name = "S60_CAGATC_L001_R3_003.fastq.gz"
		self.assertRaises(UnknownReadNumberException,FastqFile,name)

if __name__ == "__main__":
	unittest.main(verbosity=2)

