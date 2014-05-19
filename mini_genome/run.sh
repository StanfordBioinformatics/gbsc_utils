#!/bin/bash

module load python/2.7
module load bwa
module load samtools

./make_genome.py --numchr 2 --chrlength 30 --numreads 5 --readlength 10
 