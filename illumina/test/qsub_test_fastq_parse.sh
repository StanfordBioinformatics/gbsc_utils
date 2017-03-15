#!/bin/bash -eu

#$ -N test_fastq_parse
#$ -M nathankw@stanford.edu
#$ -m ae
#$ -l h_vmem=12G
#$ -l h_rt=2:00:00
#$ -l s_rt=2:00:00
#$ -R Y
#$ -cwd

module load gbsc/gbsc_utils python/2.7.9

mprof run test_fastq_parse.py
