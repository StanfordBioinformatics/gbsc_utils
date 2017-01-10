#!/bin/bash -eu

###
#Nathaniel Watson
#2016-01-09
#nathankw@stanford.edu
###

module load gbsc/gbsc_utils python/2.7.9

#reads1.fastq and reads2.fastq each contain 31,116 lines, which amounts to 7,779 FASTQ records. These files originally came from an Illumina HiSeq 4000 sequencing run, and are a portion of the unmatched reads. There was an actual barcode present in the unmatched reads, GATGAATC+AGATCTCG, that the library submitter missed. These test FASTQ files contain two records of that barcode. The goal here is to extract both in separate output FASTQ files, in the same order as the read ID (title line of a given FASTQ record).

python extract_barcodes.py --r1 reads1.fastq --r2=reads2.fastq -b GATGAATC+AGATCTCG --outfile-prefix=howdy --outdir=Extracted
