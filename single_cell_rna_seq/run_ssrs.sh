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

conf_default=${GBSC_UTILS}/single_cell_rna_seq/single_cell_rna_seq.json

function help() {
	echo "Required Arguments:"
	echo "  -i"
	echo "	Input file indicating the datasets to run through the pipeline. Each row must contain"
	echo "	three whitespace delimited fields representing:"
	echo "		1) One or more read1 FASTQ files delimited by a comma,"
	echo "		2) One ore more read2 FASTQ files delimited by a comma, and"
	echo "		3) The sample/job name. A directory will be created by this name within the folder path specified by the -o argument."
	echo "		   The pipeline results will be stored in this folder. Note that the order of the read1 files should match the order of the read2 files in order to pair them positionally."
	echo "	Each row represents a job and all jobs will be submitted to SGE to run in parallel. There should not be any blank lines in the file."
	echo "  -m"
	echo "	Email address for SGE job status notifications."
	echo "  -o"
	echo "	output directory for all results".
	echo	
	echo "Optional Arguments:"
	echo "  -c"
	echo "	The path to the JSON configuration/workflow file. Default is ${conf_default}."
}

inputFile=
mailTo=
outdir=
conf=
while getopts "hc:i:m:o:" opt
do
  case $opt in  
    h) help
			 exit 0
			;;
		c) conf=${OPTARG}
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

if ! [[ -f ${inputFile} ]]
then
	echo "Error: Input file ${inputFile} does not exist. Exiting"
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

if [[ -n ${conf} ]]
then
	conf=${conf}
else
	conf=${conf_default}
fi

#parse input file just to make sure it's conformable
declare -A samples
count=0
while read read1 read2 sampleName
do
	count=$(( $count + 1 ))
	if [[ -z $read1 || -z $read2 || -z $sampleName ]]
	then
		echo "Error on line ${count} in input file ${inputFile}: There should not be any blank lines, and all lines must have three whitespace delimited entries indicating the read1 FASTQ file(s) and the read2 FASTQ file(s) and the sampleName, respectively."
		exit 1
	fi

	#check if there are any duplicate sample names, since each sample will be mapped in a folder by the same name
	set +u 
	#needed b/c will get an error stating 'unbound variable' if sampleName doesn't yet exist in the array
	existingSample=${samples[${sampleName}]}
	if [[ -n $existingSample ]]
	then
		echo "Error - Sample name ${sampleName} already exists in ${inputFile}."
		exit 1
	fi
	set -u
	samples[${sampleName}]=${count}
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

#Load the genome
echo "Preparing to load the genome"
jsonWorkflow.py -c ${conf} --outdir=${outdir} --sjmfile=${load_genome_sjm} --disable-all-except star_load_genome
sjm -i --mail ${mailTo} ${load_genome_sjm} #call sjm explicitely rathe than add the --run --wait options to jsonWorkflow.py so that I can set the email notificaiton

#map samples
echo "Preparing to map the samples from the input file"
while read read1 read2 sampleName
do
	#jsonWorkflow.py -c ${conf} --outdir=${outdir}/${sampleName} --jobNameMangling --sjmfile=${map_samples_sjm} --disable-all-except star_mapper read1=${read1} read2=${read2}
	job_outdir=${outdir}/${sampleName}
	sjmfile=${job_outdir}/map.sjm
	jsonWorkflow.py --mail-to ${mailTo} -c ${conf} --outdir=${job_outdir} --sjmfile=${sjmfile} --disable-all-except star_mapper read1=${read1} read2=${read2} --run --wait
	sleep 2
done < ${inputFile}

#unload the genome
#Won't hurt to leave the genome loaded
#jsonWorkflow.py -c ${conf} --outdir=${outdir} --sjmfile=${unload_genome_sjm} --disable-all-except star_unload_genome --wait --run

