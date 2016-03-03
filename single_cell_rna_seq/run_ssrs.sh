#!/bin/bash -eu

#$ -M nathankw@stanford.edu
#$ -m ae
#$ -R y

###
#Nathaniel Watson
#2016-02-02
###

module load jsonwf/current
module load gbsc/gbsc_utils #exports GBSC_UTILS env. var.

function help() {
	echo "Required Arguments:"
	echo "  -i"
	echo "	Input file indicating the datasets to run through the pipeline. Each row must contain"
	echo "	two whitespace delimited fields representing the read1 FASTQ file and the read2 FASTQ file, in that"
	echo "	order.  Each row represents a job and all jobs will be submitted to SGE to run in parallel. There"
	echo "	should not be any blank lines in the file."
	echo "  -m"
	echo "	Email address for SGE job status notifications."
	echo "  -o"
	echo "	output directory for all results".
}

inputFile=
mailTo=
outdir=
while getopts "hi:m:o:" opt
do
  case $opt in  
    h) help
			 exit 0
			;;
		i) inputFile=${OPTARG}
			;;
		m) mailTo=${OPTARG}
			;;
		o) outdir=${OPTARG}
			;;
  esac
done

if [[ -z ${inputFile} ]]
then
	echo "-i is required."
	help
	exit 1
fi

if [[ -z ${mailTo} ]]
then
	echo "-m is required."
	help
	exit 1
fi

if [[ -z ${outdir} ]]
then
	echo "-o is required."
	help
	exit 1
fi

#parse input file just to make sure it's conformable
count=0
while read read1 read2
do
	count=$(( $count + 1 ))
	if [[ -z $read1 || -z $read2 ]]
	then
		echo "Error on line ${count} in input file ${inputFile}: There should not be any blank lines, and all lines must have two whitespace delimited entries indicating the read1 FASTQ file and the read2 FASTQ file, respectively."
		exit 1
	fi
done < ${inputFile}

#Next, make sure the three SJM files that will be created don't exist already

load_genome_sjm=${outdir}/load_genome.sjm
if [[ -f ${load_genome_sjm} ]]
then
	echo "SJM file ${load_genome_sjm} already exists. Delete file and run the program again. Exiting."
	#by default, if the SJM file already exists, JsonWf will append to it.
	exit 1
fi

map_samples_sjm=${outdir}/map_samples.sjm
if [[ -f ${map_samples_sjm} ]]
then
	echo "SJM file ${map_samples_sjm} already exists. Delete file and run the program again. Exiting."
	#by default, if the SJM file already exists, JsonWf will append to it.
	exit 1
fi

unload_genome_sjm=${outdir}/unload_genome.sjm
if [[ -f ${unload_genome_sjm} ]]
then
	echo "SJM file ${unload_genome_sjm} already exists. Delete file and run the program again. Exiting."
	#by default, if the SJM file already exists, JsonWf will append to it.
	exit 1
fi

conf=${GBSC_UTILS}/single_cell_rna_seq/single_cell_rna_seq.json

#Load the genome
echo "Preparing to load the genome"
jsonWorkflow.py -c ${conf} --outdir=${outdir} --sjmfile=${load_genome_sjm} --disable-all-except star_load_genome --wait --run

#map samples
echo "Preparing to map the samples from the input file"
while read read1 read2
do
	jsonWorkflow.py -c ${conf} --outdir=${outdir} --jobNameMangling --sjmfile=${map_samples_sjm} --disable-all-except star_mapper read1=${read1} read2=${read2}
done < ${inputFile}

sjm -i --mail ${mailTo} ${map_samples_sjm}

#unload the genome
jsonWorkflow.py -c ${conf} --outdir=${outdir} --sjmfile=${unload_genome_sjm} --disable-all-except star_unload_genome --wait --run

